from __future__ import annotations

from pathlib import Path
from typing import Any

from ares.orchestration.cache import InMemoryCacheProvider
from ares.orchestration.config_loader import (
    build_pipeline_stage_config,
    build_strategy_registry,
    load_orchestration_yaml,
)
from ares.orchestration.constants import (
    DEFAULT_BATCH_MAX_PAIRS,
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_MAX_CONCURRENCY,
    STAGE_RESULT_ENRICHMENT,
)
from ares.orchestration.engine_adapter import ARESPredictionEngine
from ares.orchestration.factory import build_default_stage_registry
from ares.orchestration.interfaces import (
    CacheProvider,
    EventPublisher,
    FallbackPolicy,
    PredictionEngine,
    RetryPolicy,
)
from ares.orchestration.orchestrator import PredictionOrchestrator
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
from ares.orchestration.strategy_registry import StrategySelector
from ares.query_understanding.query_pipeline import QueryPipeline


class PredictionService:
    """Canonical application-level prediction entry point.

    Every production prediction interface (REST, gRPC, CLI, tools, agents)
    funnels through this service, which delegates to the single
    ``PredictionOrchestrator`` instance built from ``configs/orchestration.yaml``.

    The service keeps the orchestration layer behind one stable function
    signature (question pair + optional model/threshold/reflect/timeout) so
    callers never construct an ARES engine themselves and never observe
    pipeline internals.
    """

    def __init__(self, orchestrator: PredictionOrchestrator) -> None:
        self._orchestrator = orchestrator

    @property
    def orchestrator(self) -> PredictionOrchestrator:
        return self._orchestrator

    def predict(
        self,
        question1: str,
        question2: str,
        *,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
        skip_cache: bool = False,
        timeout_ms: float | None = None,
        request_id: str | None = None,
    ) -> Any:
        """Run one question pair through the orchestrated prediction pipeline."""
        return self._orchestrator.run(
            question1,
            question2,
            model=model,
            threshold=threshold,
            reflect=reflect,
            skip_cache=skip_cache,
            timeout_ms=timeout_ms,
            request_id=request_id,
        )

    def predict_batch(
        self,
        pairs: list[tuple[str, str]],
        *,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
        skip_cache: bool = False,
        timeout_ms: float | None = None,
        max_concurrency: int | None = None,
        request_id: str | None = None,
    ) -> list[Any]:
        """Run pairs with bounded concurrency; per-pair failures are returned
        as exceptions at the pair's index (input order is preserved)."""
        return self._orchestrator.run_batch(
            pairs,
            model=model,
            threshold=threshold,
            reflect=reflect,
            skip_cache=skip_cache,
            timeout_ms=timeout_ms,
            max_concurrency=max_concurrency,
            request_id=request_id,
        )

    def predict_raw(
        self,
        question1: str,
        question2: str,
        *,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
        skip_cache: bool = False,
        timeout_ms: float | None = None,
        request_id: str | None = None,
    ) -> Any:
        """Run prediction through the orchestration pipeline but skip
        result enrichment.  Returns the raw ``PredictionResult`` with an
        orchestration trace that excludes the enrichment stage.

        Intended for diagnostic endpoints and multi-agent consumers that
        need raw engine output without the enrichment layer.
        """
        return self._orchestrator.run(
            question1,
            question2,
            model=model,
            threshold=threshold,
            reflect=reflect,
            skip_cache=skip_cache,
            timeout_ms=timeout_ms,
            request_id=request_id,
            skip_stages=(STAGE_RESULT_ENRICHMENT,),
        )


def load_adaptive_routing_config(config_dir: Path | None = None) -> dict[str, Any]:
    """Load the Phase 14 ``configs/adaptive_routing.yaml`` payload ({} if absent)."""
    from ares.adaptive.config_loader import load_adaptive_config

    return load_adaptive_config(config_dir=config_dir)


def build_default_prediction_service(
    config_dir: Path | None = None,
    *,
    engine: PredictionEngine | None = None,
    query_pipeline: QueryPipeline | None = None,
    strategy_selector: StrategySelector | None = None,
    cache_provider: CacheProvider | None = None,
    retry_policy: RetryPolicy | None = None,
    fallback_policy: FallbackPolicy | None = None,
    event_publisher: EventPublisher | None = None,
    max_concurrency: int | None = None,
    batch_max_pairs: int | None = None,
) -> PredictionService:
    """Assemble the default orchestrated prediction path from configuration.

    Reads ``configs/orchestration.yaml`` (falling back to built-in defaults
    when absent) and wires: the ARES engine adapter (canonical engine),
    the query understanding pipeline, the strategy registry/selector, the
    in-memory cache and the retry/fallback policies behind one
    ``PredictionOrchestrator`` with the default five-stage registry.

    Every injectable component is optional, which keeps unit tests able to
    substitute fakes without touching configuration or singletons.
    """
    config = load_orchestration_yaml(config_dir) or {}

    cache_config = config.get("cache") or {}
    cache_enabled = bool(cache_config.get("enabled", True))
    if cache_provider is None and cache_enabled:
        cache_provider = InMemoryCacheProvider(
            int(cache_config.get("max_entries", DEFAULT_CACHE_MAX_ENTRIES)),
            default_ttl=int(cache_config.get("ttl_seconds", DEFAULT_CACHE_TTL_SECONDS)),
        )

    retry_config = config.get("retry") or {}
    if retry_policy is None:
        retry_policy = DefaultRetryPolicy(
            enabled=bool(retry_config.get("enabled", True)),
            max_attempts=int(retry_config.get("max_attempts", 2)),
            backoff_ms=int(retry_config.get("backoff_ms", 100)),
        )

    fallback_config = config.get("fallback") or {}
    if fallback_policy is None:
        fallback_policy = DefaultFallbackPolicy(
            enabled=bool(fallback_config.get("enabled", True)),
            fallback_model=str(fallback_config.get("model", DEFAULT_FALLBACK_MODEL)),
        )

    pipeline_config = config.get("pipeline") or {}
    stage_config = build_pipeline_stage_config(config_dir) or None

    if engine is None:
        engine = ARESPredictionEngine()

    adaptive_config = load_adaptive_routing_config(config_dir) or {}
    adaptive_enabled = bool(adaptive_config.get("enabled", False))
    if adaptive_enabled:
        from ares.adaptive.executor import AdaptivePredictionEngine

        engine = AdaptivePredictionEngine(engine, config=adaptive_config)

    if query_pipeline is None:
        query_pipeline = QueryPipeline()
    if strategy_selector is None:
        strategy_selector = StrategySelector(build_strategy_registry(config_dir))

    registry = build_default_stage_registry(
        engine,
        query_pipeline,
        strategy_selector,
        cache_provider=cache_provider,
        cache_ttl_seconds=int(cache_config.get("ttl_seconds", DEFAULT_CACHE_TTL_SECONDS)),
        cache_fail_closed=bool(cache_config.get("fail_closed", False)),
        event_publisher=event_publisher,
        stage_config=stage_config,
        adaptive_auto_route=adaptive_enabled,
    )

    orchestrator = PredictionOrchestrator(
        registry,
        retry_policy=retry_policy,
        fallback_policy=fallback_policy,
        event_publisher=event_publisher,
        max_concurrency=max_concurrency or int(pipeline_config.get("max_concurrency", DEFAULT_MAX_CONCURRENCY)),
        batch_max_pairs=batch_max_pairs or int(pipeline_config.get("batch_max_pairs", DEFAULT_BATCH_MAX_PAIRS)),
    )
    return PredictionService(orchestrator)


_service: PredictionService | None = None


def get_prediction_service() -> PredictionService:
    """Return the process-wide canonical prediction service (lazily built).

    The singleton guarantees REST, gRPC, CLI, tools and agents share one
    orchestrator, one pipeline, one cache and one set of policies, which is
    the Phase 13.4 goal of a single canonical prediction path.
    """
    global _service
    if _service is None:
        _service = build_default_prediction_service()
    return _service


def reset_prediction_service() -> None:
    """Drop the process-wide singleton (used by tests to rebuild/replace it)."""
    global _service
    _service = None
