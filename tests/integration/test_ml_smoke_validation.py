"""ML smoke validation for the orchestrated prediction path.

Verifies that the orchestration layer does not corrupt inputs, that
normalization is consistent, that selected model/strategy is correct,
and that scores/thresholds are propagated correctly.

All tests use mock engines — no real model inference is performed.
The purpose is to validate orchestration correctness, not ML accuracy.
"""

from __future__ import annotations

from typing import Any

import pytest

from ares._result import PredictionResult
from ares.model_registry import ModelCapabilities, ModelEntry, ModelHealth
from ares.orchestration import build_default_stage_registry
from ares.orchestration.orchestrator import PredictionOrchestrator
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
from ares.orchestration.prediction_service import PredictionService
from ares.orchestration.strategy_registry import StrategyRegistry, StrategySelector
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.router_models import RoutingDecision

TEST_CASES = [
    {
        "name": "identical_short",
        "q1": "hi",
        "q2": "hi",
        "expected_label": 1,
    },
    {
        "name": "identical_case_insensitive",
        "q1": "Hello",
        "q2": "hello",
        "expected_label": 1,
    },
    {
        "name": "substring_match",
        "q1": "Python",
        "q2": "Python programming language",
        "expected_label": 1,
    },
    {
        "name": "punctuation_difference",
        "q1": "hello",
        "q2": "hello!",
        "expected_label": 1,
    },
    {
        "name": "obvious_non_duplicate",
        "q1": "What is Python?",
        "q2": "What is the capital of France?",
        "expected_label": 0,
    },
    {
        "name": "longer_non_duplicate",
        "q1": "What are the best restaurants in Paris?",
        "q2": "How does quantum entanglement work in physics?",
        "expected_label": 0,
    },
    {
        "name": "clearly_unrelated",
        "q1": "What is the meaning of life?",
        "q2": "How do I fix a flat tire?",
        "expected_label": 0,
    },
]


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
    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )


class SmokeEngine:
    """Deterministic engine that returns predictions based on input similarity."""

    def predict(self, question1: str, question2: str, **kwargs: Any) -> PredictionResult:
        q1 = question1.strip().lower()
        q2 = question2.strip().lower()
        if q1 == q2:
            label, prob_dup = 1, 0.95
        elif q1 in q2 or q2 in q1:
            label, prob_dup = 1, 0.85
        else:
            label, prob_dup = 0, 0.25
        prob_non = 1.0 - prob_dup
        model = kwargs.get("model", "SmokeEngine")
        threshold = kwargs.get("threshold", 0.5)
        prediction = "duplicate" if label == 1 else "non-duplicate"
        return PredictionResult(
            predicted_label=label,
            prediction=prediction,
            confidence=prob_dup if label == 1 else prob_non,
            prob_duplicate=prob_dup,
            prob_non_duplicate=prob_non,
            model_name=model,
            latency_ms=0.1,
            threshold=threshold,
        )


@pytest.fixture(autouse=True)
def _mock_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ares.orchestration.strategy_registry.find_entry",
        lambda model_name, paths=None: _ready_entry(model_name),
    )


def _make_service() -> PredictionService:
    engine = SmokeEngine()
    pipeline = FakeQueryPipeline()
    selector = StrategySelector(StrategyRegistry.with_defaults())
    registry = build_default_stage_registry(engine, pipeline, selector)
    orchestrator = PredictionOrchestrator(
        registry,
        retry_policy=DefaultRetryPolicy(max_attempts=2, backoff_ms=0),
        fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback"),
    )
    return PredictionService(orchestrator)


@pytest.mark.orchestration
@pytest.mark.smoke
class TestMLSmokeValidation:
    """Verify orchestration correctness across diverse input patterns."""

    @pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["name"])
    def test_prediction_through_orchestrator(self, case: dict) -> None:
        service = _make_service()
        result = service.predict(case["q1"], case["q2"])
        assert result.predicted_label == case["expected_label"], (
            f"[{case['name']}] Expected label {case['expected_label']}, got {result.predicted_label}"
        )

    @pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["name"])
    def test_orchestration_trace_present(self, case: dict) -> None:
        service = _make_service()
        result = service.predict(case["q1"], case["q2"])
        trace = result.orchestration_trace
        assert trace is not None
        assert "stages" in trace
        assert "request_id" in trace
        assert "strategy" in trace
        assert "model_name" in trace

    @pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["name"])
    def test_scores_are_valid(self, case: dict) -> None:
        service = _make_service()
        result = service.predict(case["q1"], case["q2"])
        assert 0.0 <= result.prob_duplicate <= 1.0
        assert 0.0 <= result.prob_non_duplicate <= 1.0
        assert 0.0 <= result.confidence <= 1.0
        assert abs(result.prob_duplicate + result.prob_non_duplicate - 1.0) < 1e-6

    @pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["name"])
    def test_threshold_applied(self, case: dict) -> None:
        service = _make_service()
        result = service.predict(case["q1"], case["q2"], threshold=0.7)
        assert result.threshold == 0.7

    @pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["name"])
    def test_model_propagated(self, case: dict) -> None:
        service = _make_service()
        result = service.predict(case["q1"], case["q2"], model="TestModel")
        assert result.model_name == "TestModel"

    def test_batch_preserves_order(self) -> None:
        service = _make_service()
        pairs = [(c["q1"], c["q2"]) for c in TEST_CASES]
        results = service.predict_batch(pairs)
        assert len(results) == len(TEST_CASES)
        for result, case in zip(results, TEST_CASES, strict=True):
            assert result.predicted_label == case["expected_label"]

    def test_raw_mode_preserves_predictions(self) -> None:
        service = _make_service()
        for case in TEST_CASES:
            result = service.predict_raw(case["q1"], case["q2"])
            assert result.predicted_label == case["expected_label"]

    def test_deterministic_results(self) -> None:
        service = _make_service()
        r1 = service.predict("What is Python?", "What is Python programming?")
        r2 = service.predict("What is Python?", "What is Python programming?")
        assert r1.prediction == r2.prediction
        assert r1.confidence == r2.confidence
        assert r1.prob_duplicate == r2.prob_duplicate
