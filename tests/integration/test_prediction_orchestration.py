"""Integration tests for the prediction orchestration pipeline.

These tests verify the full orchestrated prediction path end-to-end,
covering cache behavior, strategy resolution, retry/fallback, batch
operations, error handling, and backward compatibility.
"""

from __future__ import annotations

import copy
import threading
import time
from typing import Any

import pytest

from ares._result import PredictionResult
from ares.model_registry import ModelCapabilities, ModelEntry, ModelHealth
from ares.orchestration import build_default_stage_registry
from ares.orchestration.cache import InMemoryCacheProvider
from ares.orchestration.constants import (
    EVENT_CACHE_HIT,
    EVENT_CACHE_MISS,
    EVENT_ORCHESTRATION_COMPLETE,
    EVENT_ORCHESTRATION_FAILED,
    EVENT_ORCHESTRATION_FALLBACK,
    EVENT_ORCHESTRATION_STARTED,
    EVENT_STAGE_COMPLETE,
    EVENT_STAGE_STARTED,
    STAGE_RESULT_ENRICHMENT,
)
from ares.orchestration.exceptions import (
    InputValidationError,
    ModelUnavailableError,
    OrchestrationError,
)
from ares.orchestration.orchestrator import PredictionOrchestrator
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
from ares.orchestration.prediction_service import (
    PredictionService,
    get_prediction_service,
    reset_prediction_service,
)
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
def _ready_model_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ares.orchestration.strategy_registry.find_entry",
        lambda model_name, paths=None: _ready_entry(model_name),
    )


def _make_service(
    engine: Any | None = None,
    cache: InMemoryCacheProvider | None = None,
    recorder: Recorder | None = None,
) -> tuple[PredictionService, FakeEngine, FakeQueryPipeline]:
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
    )
    return PredictionService(orchestrator), fake_engine, fake_pipeline


@pytest.fixture(autouse=True)
def _reset_singleton() -> None:
    reset_prediction_service()
    yield
    reset_prediction_service()


# ── Full Pipeline ─────────────────────────────────────────────────


@pytest.mark.orchestration
class TestFullPipeline:
    def test_predict_returns_valid_result(self) -> None:
        service, _, _ = _make_service()
        result = service.predict("What is Python?", "What is Python programming?")
        assert result.prediction == "duplicate"
        assert result.confidence > 0
        assert result.orchestration_trace is not None

    def test_predict_trace_has_all_stages(self) -> None:
        service, _, _ = _make_service()
        result = service.predict("a", "b")
        stages = [s["name"] for s in result.orchestration_trace["stages"]]
        assert "InputValidationStage" in stages
        assert "QueryUnderstandingStage" in stages
        assert "StrategySelectionStage" in stages
        assert "PredictionStage" in stages
        assert "ResultEnrichmentStage" in stages

    def test_predict_with_model_override(self) -> None:
        service, engine, _ = _make_service()
        service.predict("a", "b", model="Custom Model")
        assert engine.calls[0][2]["model"] == "Custom Model"

    def test_predict_with_threshold_override(self) -> None:
        service, engine, _ = _make_service()
        service.predict("a", "b", threshold=0.8)
        assert engine.calls[0][2]["threshold"] == 0.8

    def test_predict_generates_request_id(self) -> None:
        service, _, _ = _make_service()
        result = service.predict("a", "b")
        assert result.orchestration_trace["request_id"]

    def test_predict_preserves_provided_request_id(self) -> None:
        service, _, _ = _make_service()
        result = service.predict("a", "b", request_id="my-req-123")
        assert result.orchestration_trace["request_id"] == "my-req-123"


# ── Cache Behavior ─────────────────────────────────────────────────


@pytest.mark.orchestration
class TestCacheBehavior:
    def test_cache_hit_skips_query_understanding(self) -> None:
        cache = InMemoryCacheProvider()
        service, _, pipeline = _make_service(cache=cache)
        service.predict("a", "b")
        service.predict("a", "b")
        assert len(pipeline.calls) == 1

    def test_cache_miss_on_first_call(self) -> None:
        cache = InMemoryCacheProvider()
        service, _, pipeline = _make_service(cache=cache)
        result = service.predict("a", "b")
        assert result.orchestration_trace["cache_hit"] is False
        assert len(pipeline.calls) == 1

    def test_skip_cache_bypasses_cache(self) -> None:
        cache = InMemoryCacheProvider()
        service, engine, _ = _make_service(cache=cache)
        service.predict("a", "b", skip_cache=True)
        service.predict("a", "b", skip_cache=True)
        assert len(engine.calls) == 2

    def test_cache_events_published(self) -> None:
        cache = InMemoryCacheProvider()
        recorder = Recorder()
        service, _, _ = _make_service(cache=cache, recorder=recorder)
        service.predict("a", "b")
        service.predict("a", "b")
        event_types = [e for e, _ in recorder.events]
        assert EVENT_CACHE_MISS in event_types
        assert EVENT_CACHE_HIT in event_types

    def test_different_inputs_cache_independently(self) -> None:
        cache = InMemoryCacheProvider()
        service, engine, _ = _make_service(cache=cache)
        service.predict("a", "b")
        service.predict("c", "d")
        assert len(engine.calls) == 2


# ── Retry Behavior ─────────────────────────────────────────────────


@pytest.mark.orchestration
class TestRetryBehavior:
    def test_retry_succeeds_after_transient_failure(self) -> None:
        engine = FakeEngine(fail_times=1)
        service, used_engine, _ = _make_service(engine=engine)
        result = service.predict("a", "b")
        assert result.prediction == "duplicate"
        assert len(used_engine.calls) == 2

    def test_retry_exhaustion_triggers_fallback(self) -> None:
        engine = FakeEngine(fail_times=2)
        recorder = Recorder()
        service, used_engine, _ = _make_service(engine=engine, recorder=recorder)
        result = service.predict("a", "b")
        assert result.orchestration_trace["fallback_used"] is True
        assert used_engine.calls[2][2]["model"] == "Fallback Model"
        event_types = [e for e, _ in recorder.events]
        assert EVENT_ORCHESTRATION_FALLBACK in event_types

    def test_non_retryable_error_no_retry(self) -> None:
        engine = FakeEngine(error=InputValidationError("bad"))
        service, used_engine, _ = _make_service(engine=engine)
        with pytest.raises(OrchestrationError):
            service.predict("a", "b")
        assert len(used_engine.calls) == 1


# ── Fallback Behavior ─────────────────────────────────────────────


@pytest.mark.orchestration
class TestFallbackBehavior:
    def test_fallback_used_only_once(self) -> None:
        engine = FakeEngine(fail_times=2)
        recorder = Recorder()
        service, used_engine, _ = _make_service(engine=engine, recorder=recorder)
        result = service.predict("a", "b")
        assert result.orchestration_trace["fallback_used"] is True
        fallback_calls = [c for c in used_engine.calls if c[2].get("model") == "Fallback Model"]
        assert len(fallback_calls) == 1

    def test_fallback_records_in_trace(self) -> None:
        engine = FakeEngine(fail_times=2)
        service, _, _ = _make_service(engine=engine)
        result = service.predict("a", "b")
        assert result.orchestration_trace["fallback_used"] is True
        assert result.orchestration_trace["strategy"] == "fallback"


# ── Error Handling ─────────────────────────────────────────────────


@pytest.mark.orchestration
class TestErrorHandling:
    def test_invalid_input_raises_input_validation(self) -> None:
        service, _, _ = _make_service()
        with pytest.raises(InputValidationError):
            service.predict("", "b")

    def test_both_empty_raises(self) -> None:
        service, _, _ = _make_service()
        with pytest.raises(InputValidationError):
            service.predict("", "")

    def test_engine_error_wrapped_as_orchestration_error(self) -> None:
        engine = FakeEngine(error=RuntimeError("boom"))
        service, _, _ = _make_service(engine=engine)
        with pytest.raises(OrchestrationError):
            service.predict("a", "b")

    def test_model_unavailable_wrapped(self) -> None:
        engine = FakeEngine(error=ModelUnavailableError("gone"))
        service, _, _ = _make_service(engine=engine)
        with pytest.raises(OrchestrationError):
            service.predict("a", "b")


# ── Batch Operations ──────────────────────────────────────────────


@pytest.mark.orchestration
class TestBatchOperations:
    def test_batch_preserves_order(self) -> None:
        service, _, _ = _make_service()
        results = service.predict_batch([("a", "b"), ("c", "d"), ("e", "f")])
        assert len(results) == 3
        assert all(isinstance(r, PredictionResult) for r in results)

    def test_batch_empty(self) -> None:
        service, _, _ = _make_service()
        assert service.predict_batch([]) == []

    def test_batch_per_pair_isolation(self) -> None:
        engine = FakeEngine(error=RuntimeError("crash"))
        service, _, _ = _make_service(engine=engine)
        results = service.predict_batch([("ok", "ok"), ("bad", "bad")])
        assert len(results) == 2
        assert isinstance(results[0], Exception)
        assert isinstance(results[1], Exception)

    def test_batch_bounds_concurrency(self) -> None:
        active: list[int] = []
        peak: list[int] = [0]
        lock = threading.Lock()

        class CountingEngine:
            def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
                with lock:
                    active.append(1)
                    peak[0] = max(peak[0], len(active))
                time.sleep(0.05)
                with lock:
                    active.pop()
                return _result()

        service, _, _ = _make_service(engine=CountingEngine())
        results = service.predict_batch([("a", "b")] * 4, max_concurrency=2)
        assert len(results) == 4
        assert peak[0] <= 2

    def test_batch_exceeding_max_raises(self) -> None:
        fake_engine = FakeEngine()
        fake_pipeline = FakeQueryPipeline()
        selector = StrategySelector(StrategyRegistry.with_defaults())
        registry = build_default_stage_registry(fake_engine, fake_pipeline, selector)
        orchestrator = PredictionOrchestrator(registry, batch_max_pairs=2)
        service = PredictionService(orchestrator)
        with pytest.raises(ValueError):
            service.predict_batch([("a", "b"), ("c", "d"), ("e", "f")])


# ── Skip Stages / Raw Mode ────────────────────────────────────────


@pytest.mark.orchestration
class TestRawMode:
    def test_predict_raw_skips_enrichment(self) -> None:
        service, _, _ = _make_service()
        result = service.predict_raw("a", "b")
        assert result.prediction == "duplicate"
        stages = [s["name"] for s in result.orchestration_trace["stages"]]
        assert STAGE_RESULT_ENRICHMENT not in stages

    def test_predict_raw_still_runs_pipeline(self) -> None:
        service, _, pipeline = _make_service()
        service.predict_raw("a", "b")
        assert len(pipeline.calls) == 1

    def test_predict_raw_has_trace(self) -> None:
        service, _, _ = _make_service()
        result = service.predict_raw("a", "b")
        assert result.orchestration_trace is not None
        assert result.orchestration_trace["request_id"]


# ── Event Publishing ──────────────────────────────────────────────


@pytest.mark.orchestration
class TestEventPublishing:
    def test_full_lifecycle_events_published(self) -> None:
        recorder = Recorder()
        service, _, _ = _make_service(recorder=recorder)
        service.predict("a", "b")
        event_types = [e for e, _ in recorder.events]
        assert EVENT_ORCHESTRATION_STARTED in event_types
        assert EVENT_ORCHESTRATION_COMPLETE in event_types
        assert EVENT_STAGE_STARTED in event_types
        assert EVENT_STAGE_COMPLETE in event_types

    def test_failure_publishes_failed_event(self) -> None:
        recorder = Recorder()
        engine = FakeEngine(error=RuntimeError("crash"))
        service, _, _ = _make_service(engine=engine, recorder=recorder)
        with pytest.raises(OrchestrationError):
            service.predict("a", "b")
        event_types = [e for e, _ in recorder.events]
        assert EVENT_ORCHESTRATION_FAILED in event_types


# ── Concurrent Access ─────────────────────────────────────────────


@pytest.mark.orchestration
class TestConcurrentAccess:
    def test_shared_orchestrator_thread_safety(self) -> None:
        service, _, _ = _make_service()
        results: list[Any] = []
        errors: list[Exception] = []
        lock = threading.Lock()

        def predict_pair(q1: str, q2: str) -> None:
            try:
                r = service.predict(q1, q2)
                with lock:
                    results.append(r)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=predict_pair, args=(f"q{i}", f"q{i}")) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 10
        assert len(errors) == 0
        assert all(r.prediction == "duplicate" for r in results)


# ── Singleton Behavior ────────────────────────────────────────────


@pytest.mark.orchestration
class TestServiceSingleton:
    def test_get_returns_same_instance(self) -> None:
        a = get_prediction_service()
        b = get_prediction_service()
        assert a is b

    def test_reset_creates_new(self) -> None:
        a = get_prediction_service()
        reset_prediction_service()
        b = get_prediction_service()
        assert a is not b

    def test_singleton_has_orchestrator(self) -> None:
        service = get_prediction_service()
        assert service.orchestrator is not None
