from __future__ import annotations

from typing import Any

import pytest

from ares._result import PredictionResult
from ares.model_registry import ModelCapabilities, ModelEntry, ModelHealth
from ares.orchestration import (
    build_default_stage_registry,
)
from ares.orchestration.cache import InMemoryCacheProvider
from ares.orchestration.constants import (
    EVENT_CACHE_HIT,
    EVENT_CACHE_MISS,
    EVENT_ORCHESTRATION_COMPLETE,
    EVENT_ORCHESTRATION_FAILED,
    EVENT_ORCHESTRATION_STARTED,
    EVENT_STRATEGY_SELECTED,
)
from ares.orchestration.exceptions import InputValidationError, ModelUnavailableError, OrchestrationError
from ares.orchestration.orchestrator import PredictionOrchestrator
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
from ares.orchestration.strategy_registry import StrategyRegistry, StrategySelector
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.router_models import RoutingDecision


def _result(model_name: str = "Test Model") -> PredictionResult:
    return PredictionResult(
        predicted_label=1,
        prediction="duplicate",
        confidence=0.9,
        prob_duplicate=0.9,
        prob_non_duplicate=0.1,
        model_name=model_name,
        latency_ms=1.0,
    )


class FakeQueryPipeline:
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
    def __init__(self, result: Any | None = None, error: Exception | None = None, fail_times: int = 0) -> None:
        self.result = result if result is not None else _result()
        self.error = error
        self.fail_times = fail_times
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
        self.calls.append((question1, question2, kwargs))
        if self.error is not None:
            raise self.error
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ModelUnavailableError("model unavailable")
        import copy

        return copy.copy(self.result)


class Recorder:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any] | None]] = []

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append((event_type, payload))


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
def ready_model_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ares.orchestration.strategy_registry.find_entry",
        lambda model_name, paths=None: _ready_entry(model_name),
    )


def _make_orchestrator(
    *,
    engine: Any | None = None,
    cache: InMemoryCacheProvider | None = None,
    recorder: Recorder | None = None,
    max_concurrency: int = 4,
    batch_max_pairs: int = 1000,
    ready_registry: bool = True,
) -> tuple[PredictionOrchestrator, FakeEngine, FakeQueryPipeline]:
    fake_engine = engine if engine is not None else FakeEngine()
    fake_pipeline = FakeQueryPipeline()
    selector = StrategySelector(StrategyRegistry.with_defaults())
    registry = build_default_stage_registry(
        fake_engine,
        fake_pipeline,
        selector,
        cache_provider=cache,
        event_publisher=recorder,
    )
    orchestrator = PredictionOrchestrator(
        registry,
        retry_policy=DefaultRetryPolicy(max_attempts=2, backoff_ms=0),
        fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback Model"),
        event_publisher=recorder,
        max_concurrency=max_concurrency,
        batch_max_pairs=batch_max_pairs,
    )
    return orchestrator, fake_engine, fake_pipeline


class TestRun:
    def test_run_returns_result_with_trace(self) -> None:
        orchestrator, engine, _ = _make_orchestrator()
        result = orchestrator.run("What is the capital of France?", "Capital of France?")
        assert result.prediction == "duplicate"
        assert len(engine.calls) == 1
        trace = result.orchestration_trace
        assert trace is not None
        assert "cache_hit" in trace
        assert len(trace["stages"]) == 5

    def test_run_stages_in_documented_order(self) -> None:
        orchestrator, _, _ = _make_orchestrator()
        result = orchestrator.run("a", "b")
        names = [s["name"] for s in result.orchestration_trace["stages"]]
        assert names == [
            "InputValidationStage",
            "QueryUnderstandingStage",
            "StrategySelectionStage",
            "PredictionStage",
            "ResultEnrichmentStage",
        ]

    def test_run_publishes_lifecycle_events(self) -> None:
        recorder = Recorder()
        orchestrator, _, _ = _make_orchestrator(recorder=recorder)
        orchestrator.run("a", "b")
        types = [event for event, _ in recorder.events]
        assert EVENT_ORCHESTRATION_STARTED in types
        assert EVENT_ORCHESTRATION_COMPLETE in types
        assert EVENT_STRATEGY_SELECTED in types

    def test_run_cache_hit_on_second_call(self) -> None:
        recorder = Recorder()
        cache = InMemoryCacheProvider()
        orchestrator, engine, query_pipeline = _make_orchestrator(cache=cache, recorder=recorder)
        first = orchestrator.run("a", "b")
        second = orchestrator.run("a", "b")
        assert first.orchestration_trace["cache_hit"] is False
        assert second.orchestration_trace["cache_hit"] is True
        assert len(query_pipeline.calls) == 1
        types = [event for event, _ in recorder.events]
        assert EVENT_CACHE_MISS in types
        assert EVENT_CACHE_HIT in types

    def test_run_skip_cache(self) -> None:
        cache = InMemoryCacheProvider()
        orchestrator, engine, _ = _make_orchestrator(cache=cache)
        orchestrator.run("a", "b", skip_cache=True)
        orchestrator.run("a", "b", skip_cache=True)
        assert len(engine.calls) == 2

    def test_run_invalid_input_raises(self) -> None:
        orchestrator, _, _ = _make_orchestrator()
        with pytest.raises(InputValidationError):
            orchestrator.run("", "b")

    def test_run_model_override_reaches_engine(self) -> None:
        orchestrator, engine, _ = _make_orchestrator()
        orchestrator.run("a", "b", model="Custom Model")
        assert engine.calls[0][2]["model"] == "Custom Model"

    def test_run_threshold_override_reaches_engine(self) -> None:
        orchestrator, engine, _ = _make_orchestrator()
        orchestrator.run("a", "b", threshold=0.8)
        assert engine.calls[0][2]["threshold"] == 0.8

    def test_run_strategy_uses_routing_decision(self) -> None:
        orchestrator, engine, _ = _make_orchestrator()
        orchestrator.run("a", "b")
        model = engine.calls[0][2]["model"]
        assert model == "TF-IDF + Logistic Regression (Week 2)"

    def test_run_fallback_on_model_unavailable(self) -> None:
        cache = InMemoryCacheProvider()
        engine = FakeEngine(fail_times=2)
        recorder = Recorder()
        orchestrator, used_engine, _ = _make_orchestrator(engine=engine, cache=cache, recorder=recorder)
        result = orchestrator.run("a", "b")
        assert used_engine.calls[0][2]["model"] == "TF-IDF + Logistic Regression (Week 2)"
        assert used_engine.calls[1][2]["model"] == "TF-IDF + Logistic Regression (Week 2)"
        assert used_engine.calls[2][2]["model"] == "Fallback Model"
        assert result.orchestration_trace["fallback_used"] is True
        assert result.orchestration_trace["strategy"] == "fallback"

    def test_run_failure_publishes_failed_event(self) -> None:
        recorder = Recorder()
        engine = FakeEngine(error=RuntimeError("crash"))
        orchestrator, _, _ = _make_orchestrator(engine=engine, recorder=recorder)
        with pytest.raises(OrchestrationError):
            orchestrator.run("a", "b")
        types = [event for event, _ in recorder.events]
        assert EVENT_ORCHESTRATION_FAILED in types


class TestRunBatch:
    def test_batch_returns_results_in_input_order(self) -> None:
        orchestrator, _, _ = _make_orchestrator()
        pairs = [("q1a", "q1b"), ("q2a", "q2b"), ("q3a", "q3b")]
        results = orchestrator.run_batch(pairs)
        assert len(results) == 3
        assert all(isinstance(r, PredictionResult) for r in results)

    def test_batch_empty(self) -> None:
        orchestrator, _, _ = _make_orchestrator()
        assert orchestrator.run_batch([]) == []

    def test_batch_exceeding_max_pairs_raises(self) -> None:
        orchestrator, _, _ = _make_orchestrator(batch_max_pairs=2)
        with pytest.raises(ValueError):
            orchestrator.run_batch([("a", "b"), ("c", "d"), ("e", "f")])

    def test_batch_isolates_per_pair_failures(self) -> None:
        cache = InMemoryCacheProvider()
        engine = FakeEngine(error=RuntimeError("crash"))
        orchestrator, _, _ = _make_orchestrator(engine=engine, cache=cache)
        results = orchestrator.run_batch([("ok1", "ok2"), ("bad1", "bad2")])
        assert len(results) == 2
        assert isinstance(results[0], Exception)
        assert isinstance(results[1], Exception)

    def test_batch_bounds_concurrency(self) -> None:
        import threading

        active: list[int] = []
        peak: list[int] = [0]
        lock = threading.Lock()

        class CountingEngine:
            def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
                with lock:
                    active.append(1)
                    peak[0] = max(peak[0], len(active))
                import time

                time.sleep(0.05)
                with lock:
                    active.pop()
                return _result()

        orchestrator, _, _ = _make_orchestrator(engine=CountingEngine(), max_concurrency=2)
        results = orchestrator.run_batch([("a", "b")] * 4, max_concurrency=2)
        assert len(results) == 4
        assert peak[0] <= 2

    def test_batch_skip_cache(self) -> None:
        cache = InMemoryCacheProvider()
        orchestrator, engine, _ = _make_orchestrator(cache=cache)
        pairs = [("a", "b"), ("a", "b")]
        orchestrator.run_batch(pairs, skip_cache=True)
        assert len(engine.calls) == 2

    def test_batch_defaults_to_configured_concurrency(self) -> None:
        orchestrator, _, _ = _make_orchestrator(max_concurrency=3)
        results = orchestrator.run_batch([("a", "b"), ("c", "d"), ("e", "f")])
        assert len(results) == 3
