from __future__ import annotations

import statistics
import time
from typing import Any

import pytest

from ares.orchestration.cache import InMemoryCacheProvider
from ares.orchestration.context import PipelineState, PredictionInput, RequestParams
from ares.orchestration.interfaces import PipelineStage
from ares.orchestration.metadata import OrchestrationMetadata
from ares.orchestration.orchestrator import PredictionOrchestrator
from ares.orchestration.pipeline import Pipeline
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
from ares.orchestration.stage_registry import StageRegistry
from ares.orchestration.stages import (
    InputValidationStage,
    PredictionStage,
    QueryUnderstandingStage,
    ResultEnrichmentStage,
    StrategySelectionStage,
)
from ares.orchestration.strategy_registry import StrategyRegistry, StrategySelector
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.router_models import RoutingDecision

# Generous upper bounds so the measurements are stable on slow CI runners.
MINIMAL_PIPELINE_P95_BUDGET_MS = 2.0
CACHE_HIT_P95_BUDGET_MS = 2.0
STRATEGY_RESOLUTION_P95_BUDGET_MS = 2.0
FULL_ORCHESTRATION_P95_BUDGET_MS = 20.0


def _percentiles(samples: list[float]) -> tuple[float, float]:
    return statistics.median(samples), statistics.quantiles(samples, n=20)[18]


def _measure(fn: Any, iterations: int) -> list[float]:
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - started) * 1000.0)
    return samples


def _input() -> PredictionInput:
    return PredictionInput(question1="What is the capital of France?", question2="Capital of France?")


def _state() -> PipelineState:
    return PipelineState()


def _metadata() -> OrchestrationMetadata:
    return OrchestrationMetadata()


class _NoopStage(PipelineStage):
    name = "NoopStage"

    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None:
        return None


class _InstantPipeline:
    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )


class _InstantEngine:
    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
        from ares._result import PredictionResult

        return PredictionResult(
            predicted_label=1,
            prediction="duplicate",
            confidence=0.9,
            prob_duplicate=0.9,
            prob_non_duplicate=0.1,
            model_name=kwargs.get("model", ""),
            latency_ms=1.0,
        )


@pytest.fixture(autouse=True)
def ready_model_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    from ares.model_registry import ModelCapabilities, ModelEntry, ModelHealth

    def _entry(display_name: str) -> ModelEntry:
        return ModelEntry(
            display_name=display_name,
            internal_id=display_name.lower().replace(" ", "_"),
            status=ModelHealth.READY,
            capabilities=ModelCapabilities(supports_batch=True, supports_cross_encoding=True),
        )

    monkeypatch.setattr(
        "ares.orchestration.strategy_registry.find_entry",
        lambda model_name, paths=None: _entry(model_name),
    )


class TestPipelineOverhead:
    def test_minimal_pipeline_overhead(self) -> None:
        registry = StageRegistry()
        registry.register(_NoopStage())  # type: ignore[arg-type]
        pipeline = Pipeline(registry)
        samples = _measure(lambda: pipeline.execute(_input(), _state(), _metadata()), 200)
        _, p95 = _percentiles(samples)
        assert p95 < MINIMAL_PIPELINE_P95_BUDGET_MS

    def test_full_stage_pipeline_overhead(self) -> None:
        engine = _InstantEngine()
        registry = build_registry(engine, cache=None)
        pipeline = Pipeline(registry)
        samples = _measure(lambda: pipeline.execute(_input(), _state(), _metadata()), 200)
        _, p95 = _percentiles(samples)
        assert p95 < FULL_ORCHESTRATION_P95_BUDGET_MS


class TestCachePerformance:
    def test_cache_hit_under_budget(self) -> None:
        engine = _InstantEngine()
        cache = InMemoryCacheProvider(max_size=1000)
        registry = build_registry(engine, cache)
        pipeline = Pipeline(registry)

        input_ = _input()
        pipeline.execute(input_, _state(), _metadata())

        hits = _measure(lambda: pipeline.execute(input_, _state(), _metadata()), 200)
        _, hit_p95 = _percentiles(hits)
        assert hit_p95 < CACHE_HIT_P95_BUDGET_MS


class TestStrategyResolution:
    def test_strategy_resolution_overhead(self) -> None:
        selector = StrategySelector(StrategyRegistry.with_defaults())
        analysis = QueryAnalysis(
            original_question_1="a",
            original_question_2="b",
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )
        request_params = RequestParams()
        samples = _measure(lambda: selector.resolve(analysis.routing_decision, request_params), 200)
        _, p95 = _percentiles(samples)
        assert p95 < STRATEGY_RESOLUTION_P95_BUDGET_MS


class TestOrchestratorPerformance:
    def test_full_orchestration_through_orchestrator(self) -> None:
        engine = _InstantEngine()
        registry = build_registry(engine, cache=InMemoryCacheProvider())
        orchestrator = PredictionOrchestrator(
            registry,
            retry_policy=DefaultRetryPolicy(max_attempts=2, backoff_ms=0),
            fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback Model"),
        )
        samples = _measure(lambda: orchestrator.run("What is the capital of France?", "Capital of France?"), 50)
        _, p95 = _percentiles(samples)
        assert p95 < FULL_ORCHESTRATION_P95_BUDGET_MS

    def test_batch_concurrency_scales_throughput(self) -> None:
        import time as _time

        class _SlowEngine:
            def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
                _time.sleep(0.02)
                return _InstantEngine().predict(question1, question2, **kwargs)

        registry = build_registry(_SlowEngine(), cache=InMemoryCacheProvider())
        orchestrator = PredictionOrchestrator(registry, max_concurrency=4)
        pairs = [("q", "p")] * 8
        started = _time.perf_counter()
        orchestrator.run_batch(pairs, max_concurrency=4)
        parallel_duration = _time.perf_counter() - started
        started = _time.perf_counter()
        orchestrator.run_batch(pairs, max_concurrency=1)
        serial_duration = _time.perf_counter() - started
        assert parallel_duration < serial_duration


def build_registry(engine: Any, cache: InMemoryCacheProvider | None) -> StageRegistry:
    registry = StageRegistry()
    registry.register(InputValidationStage(), order=1)
    registry.register(
        QueryUnderstandingStage(_InstantPipeline(), cache_provider=cache),
        order=2,
    )
    registry.register(
        StrategySelectionStage(StrategySelector(StrategyRegistry.with_defaults())),
        order=3,
    )
    registry.register(PredictionStage(engine), order=4)  # type: ignore[arg-type]
    registry.register(ResultEnrichmentStage(), order=5)
    return registry
