from __future__ import annotations

from typing import Any

import pytest

from ares._result import PredictionResult
from ares.model_registry import ModelCapabilities, ModelEntry, ModelHealth
from ares.orchestration.exceptions import ModelUnavailableError, OrchestrationError
from ares.orchestration.prediction_service import (
    PredictionService,
    build_default_prediction_service,
    get_prediction_service,
    reset_prediction_service,
)
from ares.orchestration.strategy_registry import StrategyRegistry, StrategySelector
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.query_pipeline import QueryPipeline
from ares.query_understanding.router_models import RoutingDecision


def _result() -> PredictionResult:
    return PredictionResult(
        predicted_label=1,
        prediction="duplicate",
        confidence=0.9,
        prob_duplicate=0.9,
        prob_non_duplicate=0.1,
        model_name="Test Model",
        latency_ms=1.0,
    )


class FakeQueryPipeline(QueryPipeline):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        self.calls.append((question_1, question_2))
        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )


class FakeEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.error: Exception | None = None

    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
        self.calls.append((question1, question2, kwargs))
        if self.error is not None:
            raise self.error
        return _result()


@pytest.fixture(autouse=True)
def _reset_service() -> None:
    reset_prediction_service()
    yield
    reset_prediction_service()


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


@pytest.fixture(autouse=True)
def _mock_model_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ares.orchestration.strategy_registry.find_entry",
        lambda model_name, paths=None: _ready_entry(model_name),
    )


def _service() -> tuple[PredictionService, FakeEngine, FakeQueryPipeline]:
    engine = FakeEngine()
    pipeline = FakeQueryPipeline()
    selector = StrategySelector(StrategyRegistry.with_defaults())
    service = build_default_prediction_service(
        engine=engine,
        query_pipeline=pipeline,
        strategy_selector=selector,
        cache_provider=None,
        retry_policy=None,
        fallback_policy=None,
    )
    return service, engine, pipeline


class TestPredictionService:
    def test_predict_delegates_to_orchestrator(self) -> None:
        service, engine, pipeline = _service()
        result = service.predict("q1", "q2")
        assert result.prediction == "duplicate"
        assert engine.calls == [
            (
                "q1",
                "q2",
                {
                    "model": "TF-IDF + Logistic Regression (Week 2)",
                    "threshold": 0.5,
                    "reflect": False,
                    "timeout_ms": None,
                },
            )
        ]
        assert pipeline.calls == [("q1", "q2")]

    def test_predict_forwards_request_overrides(self) -> None:
        service, engine, _ = _service()
        service.predict("q1", "q2", model="Cross-Encoder-Quora (Trained)", threshold=0.7, reflect=True, timeout_ms=500)
        assert engine.calls[0][2] == {
            "model": "Cross-Encoder-Quora (Trained)",
            "threshold": 0.7,
            "reflect": True,
            "timeout_ms": 500,
        }

    def test_predict_forwards_request_id(self) -> None:
        service, _, _ = _service()
        result = service.predict("q1", "q2", request_id="req-123")
        assert result.orchestration_trace is not None
        assert result.orchestration_trace["request_id"] == "req-123"

    def test_predict_generates_request_id_when_absent(self) -> None:
        service, _, _ = _service()
        result = service.predict("q1", "q2")
        assert result.orchestration_trace is not None
        assert result.orchestration_trace["request_id"]

    def test_predict_attaches_strategy_and_model_to_trace(self) -> None:
        service, _, _ = _service()
        result = service.predict("q1", "q2", model="Cross-Encoder-Quora (Trained)", reflect=True)
        trace = result.orchestration_trace or {}
        assert trace["model_name"] == "Cross-Encoder-Quora (Trained)"
        assert trace["strategy"] == "fast_lexical"

    def test_predict_batch_preserves_order_and_isolates_failures(self) -> None:
        service, engine, _ = _service()
        engine.error = ModelUnavailableError("down")
        outcomes = service.predict_batch([("a", "b"), ("c", "d")], max_concurrency=2)
        assert isinstance(outcomes[0], ModelUnavailableError)
        assert isinstance(outcomes[1], ModelUnavailableError)
        engine.error = None
        outcomes = service.predict_batch([("a", "b"), ("c", "d")])
        assert [o.prediction for o in outcomes] == ["duplicate", "duplicate"]

    def test_predict_batch_returns_empty_for_no_pairs(self) -> None:
        service, _, _ = _service()
        assert service.predict_batch([]) == []

    def test_predict_propagates_orchestration_errors(self) -> None:
        service, engine, _ = _service()
        engine.error = ModelUnavailableError("model gone")
        with pytest.raises(OrchestrationError) as exc_info:
            service.predict("q1", "q2")
        assert isinstance(exc_info.value, ModelUnavailableError)


class TestPredictionServiceRaw:
    def test_predict_raw_skips_enrichment_stage(self) -> None:
        service, engine, pipeline = _service()
        result = service.predict_raw("q1", "q2")
        assert result.prediction == "duplicate"
        assert result.orchestration_trace is not None
        stages_run = result.orchestration_trace.get("stages_run", [])
        assert "result_enrichment" not in stages_run
        assert engine.calls == [
            (
                "q1",
                "q2",
                {
                    "model": "TF-IDF + Logistic Regression (Week 2)",
                    "threshold": 0.5,
                    "reflect": False,
                    "timeout_ms": None,
                },
            )
        ]

    def test_predict_raw_forwards_overrides(self) -> None:
        service, engine, _ = _service()
        service.predict_raw("q1", "q2", model="Cross-Encoder-Quora (Trained)", threshold=0.7, reflect=True)
        assert engine.calls[0][2] == {
            "model": "Cross-Encoder-Quora (Trained)",
            "threshold": 0.7,
            "reflect": True,
            "timeout_ms": None,
        }

    def test_predict_raw_still_runs_pipeline(self) -> None:
        service, engine, pipeline = _service()
        service.predict_raw("q1", "q2")
        assert pipeline.calls == [("q1", "q2")]

    def test_predict_raw_has_orchestration_trace(self) -> None:
        service, _, _ = _service()
        result = service.predict_raw("q1", "q2")
        assert result.orchestration_trace is not None
        assert result.orchestration_trace["request_id"]


class TestPredictionServiceSingleton:
    def test_get_prediction_service_returns_shared_instance(self) -> None:
        first = get_prediction_service()
        second = get_prediction_service()
        assert first is second
        assert isinstance(first.orchestrator, object)

    def test_reset_prediction_service_rebuilds(self) -> None:
        first = get_prediction_service()
        reset_prediction_service()
        second = get_prediction_service()
        assert first is not second

    def test_singleton_is_orchestrated(self) -> None:
        service = get_prediction_service()
        from ares.orchestration.orchestrator import PredictionOrchestrator

        assert isinstance(service.orchestrator, PredictionOrchestrator)
