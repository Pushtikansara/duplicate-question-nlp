from __future__ import annotations

from typing import Any

from ares.orchestration.constants import (
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_MAX_QUESTION_LENGTH,
    DEFAULT_STAGE_ORDER,
)
from ares.orchestration.interfaces import CacheProvider, EventPublisher, PredictionEngine
from ares.orchestration.stage_registry import StageRegistry
from ares.orchestration.stages import (
    InputValidationStage,
    PredictionStage,
    QueryUnderstandingStage,
    ResultEnrichmentStage,
    StrategySelectionStage,
)
from ares.orchestration.strategy_registry import StrategySelector
from ares.query_understanding.query_pipeline import QueryPipeline


def build_default_stage_registry(
    engine: PredictionEngine,
    query_pipeline: QueryPipeline,
    strategy_selector: StrategySelector,
    *,
    cache_provider: CacheProvider | None = None,
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    cache_fail_closed: bool = False,
    event_publisher: EventPublisher | None = None,
    max_question_length: int = DEFAULT_MAX_QUESTION_LENGTH,
    stage_config: dict[str, Any] | None = None,
    adaptive_auto_route: bool = False,
) -> StageRegistry:
    """Build the default five-stage registry.

    Stage ordering and enablement are driven by ``stage_config`` when
    provided (the ``pipeline.stages`` section of
    ``configs/orchestration.yaml``); otherwise every stage is enabled with
    the documented execution order. Stages are resolved by their
    ``STAGE_*`` constant names.

    ``adaptive_auto_route`` (Phase 14) lets the strategy-selection stage drop
    the resolved model when no caller override exists, leaving routing to the
    adaptive prediction engine.
    """
    stage_config = stage_config or {}
    registry = StageRegistry()
    candidates = {
        DEFAULT_STAGE_ORDER[0]: InputValidationStage(max_question_length=max_question_length),
        DEFAULT_STAGE_ORDER[1]: QueryUnderstandingStage(
            query_pipeline,
            cache_provider,
            cache_ttl_seconds=cache_ttl_seconds,
            event_publisher=event_publisher,
            fail_closed=cache_fail_closed,
        ),
        DEFAULT_STAGE_ORDER[2]: StrategySelectionStage(
            strategy_selector,
            event_publisher=event_publisher,
            adaptive_auto_route=adaptive_auto_route,
        ),
        DEFAULT_STAGE_ORDER[3]: PredictionStage(engine, event_publisher=event_publisher),
        DEFAULT_STAGE_ORDER[4]: ResultEnrichmentStage(),
    }
    for order, name in enumerate(DEFAULT_STAGE_ORDER, start=1):
        entry = stage_config.get(name, {})
        if isinstance(entry, dict) and entry.get("enabled") is False:
            continue
        registry.register(
            candidates[name],
            enabled=entry.get("enabled", True) if isinstance(entry, dict) else True,
            order=entry.get("order", order) if isinstance(entry, dict) else order,
            depends_on=entry.get("depends_on", []) if isinstance(entry, dict) else [],
        )
    return registry
