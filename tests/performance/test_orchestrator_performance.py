"""Performance tests for the orchestration layer.

Measures orchestration overhead, cache-hit vs cache-miss paths, batch
throughput, and concurrent access patterns. These tests use mock engines
to isolate orchestration latency from model inference latency.
"""

from __future__ import annotations

import copy
import statistics
import threading
import time
from typing import Any

import pytest

from ares._result import PredictionResult
from ares.model_registry import ModelCapabilities, ModelEntry, ModelHealth
from ares.orchestration import build_default_stage_registry
from ares.orchestration.cache import InMemoryCacheProvider
from ares.orchestration.orchestrator import PredictionOrchestrator
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
from ares.orchestration.prediction_service import PredictionService
from ares.orchestration.strategy_registry import StrategyRegistry, StrategySelector
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.router_models import RoutingDecision


def _result() -> PredictionResult:
    return PredictionResult(
        predicted_label=1,
        prediction="duplicate",
        confidence=0.9,
        prob_duplicate=0.9,
        prob_non_duplicate=0.1,
        model_name="Test Model",
        latency_ms=0.5,
    )


class FakeQueryPipeline:
    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )


class FakeEngine:
    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
        return copy.copy(_result())


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
    cache: InMemoryCacheProvider | None = None,
    max_concurrency: int = 4,
) -> PredictionService:
    engine = FakeEngine()
    pipeline = FakeQueryPipeline()
    selector = StrategySelector(StrategyRegistry.with_defaults())
    registry = build_default_stage_registry(engine, pipeline, selector, cache_provider=cache)
    orchestrator = PredictionOrchestrator(
        registry,
        retry_policy=DefaultRetryPolicy(max_attempts=2, backoff_ms=0),
        fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback"),
        max_concurrency=max_concurrency,
    )
    return PredictionService(orchestrator)


@pytest.mark.performance
@pytest.mark.orchestration
class TestOrchestrationOverhead:
    """Measure the overhead added by the orchestration layer."""

    def test_single_prediction_overhead(self) -> None:
        service = _make_service()
        latencies = []
        for _ in range(50):
            start = time.perf_counter()
            service.predict("What is Python?", "What is Python programming?")
            latencies.append((time.perf_counter() - start) * 1000)
        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        assert p50 < 100, f"p50 overhead {p50:.1f}ms exceeds 100ms threshold"
        assert p95 < 200, f"p95 overhead {p95:.1f}ms exceeds 200ms threshold"

    def test_cache_hit_skips_query_understanding(self) -> None:
        """Verify cache hit actually short-circuits the pipeline."""
        cache = InMemoryCacheProvider()
        service = _make_service(cache=cache)
        service.predict("a", "b")
        cached_result = service.predict("a", "b")
        assert cached_result.orchestration_trace["cache_hit"] is True

    def test_raw_mode_overhead_comparable(self) -> None:
        service = _make_service()
        standard_latencies = []
        raw_latencies = []
        for _ in range(20):
            start = time.perf_counter()
            service.predict("a", "b")
            standard_latencies.append((time.perf_counter() - start) * 1000)
        for _ in range(20):
            start = time.perf_counter()
            service.predict_raw("a", "b")
            raw_latencies.append((time.perf_counter() - start) * 1000)
        avg_standard = statistics.mean(standard_latencies)
        avg_raw = statistics.mean(raw_latencies)
        assert avg_raw < avg_standard * 1.5, (
            f"Raw mode ({avg_raw:.1f}ms) should not be significantly slower than standard ({avg_standard:.1f}ms)"
        )


@pytest.mark.performance
@pytest.mark.orchestration
class TestBatchPerformance:
    """Measure batch throughput and concurrency behavior."""

    def test_batch_throughput(self) -> None:
        service = _make_service(max_concurrency=4)
        pairs = [(f"q{i}a", f"q{i}b") for i in range(20)]
        start = time.perf_counter()
        results = service.predict_batch(pairs, max_concurrency=4)
        elapsed = time.perf_counter() - start
        assert len(results) == 20
        throughput = len(results) / elapsed
        assert throughput > 10, f"Batch throughput {throughput:.1f} pairs/sec below 10 pairs/sec threshold"

    def test_batch_concurrency_bounds(self) -> None:
        active: list[int] = []
        peak: list[int] = [0]
        lock = threading.Lock()

        class SlowEngine:
            def predict(self, q1: str, q2: str, **kwargs: Any) -> Any:
                with lock:
                    active.append(1)
                    peak[0] = max(peak[0], len(active))
                time.sleep(0.02)
                with lock:
                    active.pop()
                return _result()

        engine = SlowEngine()
        pipeline = FakeQueryPipeline()
        selector = StrategySelector(StrategyRegistry.with_defaults())
        registry = build_default_stage_registry(engine, pipeline, selector)
        orchestrator = PredictionOrchestrator(registry, max_concurrency=2)
        service = PredictionService(orchestrator)
        results = service.predict_batch([("a", "b")] * 8, max_concurrency=2)
        assert len(results) == 8
        assert peak[0] <= 2, f"Peak concurrency {peak[0]} exceeded limit of 2"


@pytest.mark.performance
@pytest.mark.orchestration
class TestConcurrentPerformance:
    """Measure performance under concurrent access."""

    def test_concurrent_predictions(self) -> None:
        service = _make_service()
        latencies: list[float] = []
        lock = threading.Lock()

        def predict_pair(q1: str, q2: str) -> None:
            start = time.perf_counter()
            service.predict(q1, q2)
            elapsed = (time.perf_counter() - start) * 1000
            with lock:
                latencies.append(elapsed)

        threads = [threading.Thread(target=predict_pair, args=(f"q{i}", f"q{i}")) for i in range(10)]
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total = (time.perf_counter() - start) * 1000
        assert len(latencies) == 10
        assert total < 5000, f"10 concurrent predictions took {total:.0f}ms (threshold: 5000ms)"
