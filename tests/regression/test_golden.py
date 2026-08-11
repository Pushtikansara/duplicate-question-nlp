from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from ares._result import PredictionResult
from ares.model_registry import ModelCapabilities, ModelEntry, ModelHealth
from duplicate_question_app._models.embeddings import _get_sigmoid_params, _get_threshold, _result_dict

GOLDEN_FILE = Path(__file__).parent / "golden_outputs.json"


@pytest.fixture(scope="session")
def golden_outputs():
    """Load golden (frozen) expected outputs. Creates the file if it doesn't exist."""
    if not GOLDEN_FILE.exists():
        _generate_golden_outputs()
    with open(GOLDEN_FILE) as f:
        return json.load(f)


def _generate_golden_outputs():
    """Generate frozen golden outputs for regression testing."""
    from ares._config import get_config

    inf_cfg = get_config("inference") or {}
    thresholds = inf_cfg.get("per_model_thresholds", {})
    sigmoid_params = inf_cfg.get("sigmoid_params", {})

    data = {
        "sigmoid_params": {
            "e5-base-v2": {
                "steepness": sigmoid_params.get("E5-base-v2", [8.0, 0.82])[0],
                "midpoint": sigmoid_params.get("E5-base-v2", [8.0, 0.82])[1],
            },
            "bge-base-en-v1.5": {
                "steepness": sigmoid_params.get("BGE-base-en-v1.5", [15.6755, 0.8591])[0],
                "midpoint": sigmoid_params.get("BGE-base-en-v1.5", [15.6755, 0.8591])[1],
            },
            "mpnet-base-v2": {
                "steepness": sigmoid_params.get("MPNet-base-v2", [11.5976, 0.8133])[0],
                "midpoint": sigmoid_params.get("MPNet-base-v2", [11.5976, 0.8133])[1],
            },
        },
        "thresholds": {
            "e5-base-v2": thresholds.get("E5-base-v2", 0.35),
            "bge-base-en-v1.5": thresholds.get("BGE-base-en-v1.5", 0.3),
            "mpnet-base-v2": thresholds.get("MPNet-base-v2", 0.36),
        },
        "result_dict": {
            "prediction_duplicate": {
                "predicted_label": 1,
                "prediction": "Duplicate",
                "prob_duplicate": 0.85,
                "prob_non_duplicate": 0.15,
                "confidence": 0.85,
            },
            "prediction_non_duplicate": {
                "predicted_label": 0,
                "prediction": "Non-Duplicate",
                "prob_duplicate": 0.3,
                "prob_non_duplicate": 0.7,
                "confidence": 0.7,
            },
        },
    }
    GOLDEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOLDEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


class TestGoldenRegression:
    @pytest.mark.regression
    def test_sigmoid_params_frozen(self, golden_outputs):
        for model_name, expected in golden_outputs["sigmoid_params"].items():
            steepness, midpoint = _get_sigmoid_params(model_name)
            assert steepness == pytest.approx(expected["steepness"], rel=1e-4)
            assert midpoint == pytest.approx(expected["midpoint"], rel=1e-4)

    @pytest.mark.regression
    def test_thresholds_frozen(self, golden_outputs):
        for model_name, expected in golden_outputs["thresholds"].items():
            threshold = _get_threshold(model_name)
            assert threshold == pytest.approx(expected, rel=1e-3)

    @pytest.mark.regression
    def test_result_dict_duplicate_frozen(self, golden_outputs):
        expected = golden_outputs["result_dict"]["prediction_duplicate"]
        result = _result_dict(
            q1="test a",
            q2="test b",
            pred_label=1,
            prob_dup=0.85,
            prob_non=0.15,
            threshold=0.5,
            model_name="E5",
            device="cpu",
            latency_ms=10,
        )
        assert result["predicted_label"] == expected["predicted_label"]
        assert result["prediction"] == expected["prediction"]
        assert result["prob_duplicate"] == pytest.approx(expected["prob_duplicate"])
        assert result["confidence"] == pytest.approx(expected["confidence"])

    @pytest.mark.regression
    def test_result_dict_non_duplicate_frozen(self, golden_outputs):
        expected = golden_outputs["result_dict"]["prediction_non_duplicate"]
        result = _result_dict(
            q1="test a",
            q2="test b",
            pred_label=0,
            prob_dup=0.3,
            prob_non=0.7,
            threshold=0.5,
            model_name="BGE",
            device="cpu",
            latency_ms=5,
        )
        assert result["predicted_label"] == expected["predicted_label"]
        assert result["prediction"] == expected["prediction"]
        assert result["confidence"] == pytest.approx(expected["confidence"])


# ── Orchestrator vs Direct ARES Comparison ─────────────────────────


def _ready_entry(display_name: str) -> ModelEntry:
    return ModelEntry(
        display_name=display_name,
        internal_id=display_name.lower().replace(" ", "_"),
        status=ModelHealth.READY,
        capabilities=ModelCapabilities(
            supports_batch=True,
            supports_cross_encoding="Cross-Encoder" in display_name,
            supports_explainability=True,
        ),
    )


class FakeQueryPipeline:
    def run(self, question_1: str, question_2: str) -> Any:
        from ares.query_understanding.query_models import QueryAnalysis
        from ares.query_understanding.router_models import RoutingDecision

        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )


class FakeEngine:
    def __init__(self, result: Any | None = None) -> None:
        self.result = result or PredictionResult(
            predicted_label=1,
            prediction="duplicate",
            confidence=0.9,
            prob_duplicate=0.9,
            prob_non_duplicate=0.1,
            model_name="Test Model",
            latency_ms=1.0,
        )
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
        self.calls.append((question1, question2, kwargs))
        return copy.copy(self.result)


@pytest.mark.orchestration
class TestOrchestratorVsAresComparison:
    """Verify that the orchestrator produces equivalent results to direct
    engine access for the same inputs. This ensures the orchestration
    layer does not corrupt predictions."""

    @pytest.fixture(autouse=True)
    def _mock_registry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "ares.orchestration.strategy_registry.find_entry",
            lambda model_name, paths=None: _ready_entry(model_name),
        )

    def _make_orchestrator(self, engine: Any | None = None):
        from ares.orchestration import build_default_stage_registry
        from ares.orchestration.orchestrator import PredictionOrchestrator
        from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
        from ares.orchestration.strategy_registry import StrategyRegistry, StrategySelector

        fake_engine = engine or FakeEngine()
        pipeline = FakeQueryPipeline()
        selector = StrategySelector(StrategyRegistry.with_defaults())
        registry = build_default_stage_registry(fake_engine, pipeline, selector)
        return PredictionOrchestrator(
            registry,
            retry_policy=DefaultRetryPolicy(max_attempts=2, backoff_ms=0),
            fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback"),
        ), fake_engine

    @pytest.mark.regression
    def test_prediction_label_preserved(self) -> None:
        orchestrator, _ = self._make_orchestrator()
        result = orchestrator.run("What is Python?", "What is Python programming?")
        assert result.prediction == "duplicate"
        assert result.predicted_label == 1

    @pytest.mark.regression
    def test_confidence_preserved(self) -> None:
        orchestrator, _ = self._make_orchestrator()
        result = orchestrator.run("a", "b")
        assert result.confidence == pytest.approx(0.9, abs=1e-6)

    @pytest.mark.regression
    def test_probabilities_preserved(self) -> None:
        orchestrator, _ = self._make_orchestrator()
        result = orchestrator.run("a", "b")
        assert result.prob_duplicate == pytest.approx(0.9, abs=1e-6)
        assert result.prob_non_duplicate == pytest.approx(0.1, abs=1e-6)

    @pytest.mark.regression
    def test_model_name_preserved(self) -> None:
        orchestrator, _ = self._make_orchestrator()
        result = orchestrator.run("a", "b")
        assert result.model_name == "Test Model"

    @pytest.mark.regression
    def test_threshold_applied_correctly(self) -> None:
        orchestrator, engine = self._make_orchestrator()
        orchestrator.run("a", "b", threshold=0.8)
        assert engine.calls[0][2]["threshold"] == 0.8

    @pytest.mark.regression
    def test_trace_matches_execution(self) -> None:
        orchestrator, _ = self._make_orchestrator()
        result = orchestrator.run("a", "b")
        trace = result.orchestration_trace
        assert trace is not None
        stage_names = [s["name"] for s in trace["stages"]]
        assert stage_names == [
            "InputValidationStage",
            "QueryUnderstandingStage",
            "StrategySelectionStage",
            "PredictionStage",
            "ResultEnrichmentStage",
        ]

    @pytest.mark.regression
    def test_batch_results_match_single(self) -> None:
        orchestrator, _ = self._make_orchestrator()
        single = orchestrator.run("a", "b")
        batch = orchestrator.run_batch([("a", "b")])
        assert len(batch) == 1
        assert batch[0].prediction == single.prediction
        assert batch[0].confidence == single.confidence
