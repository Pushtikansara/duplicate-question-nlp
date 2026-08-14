from __future__ import annotations

from ares.orchestration.config import EngineConfiguration
from ares.orchestration.constants import (
    EVENT_STRATEGY_SELECTED,
    STAGE_STRATEGY_SELECTION,
)
from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.exceptions import StrategyResolutionError
from ares.orchestration.interfaces import EventPublisher, PipelineStage
from ares.orchestration.metadata import OrchestrationMetadata
from ares.orchestration.strategy_registry import StrategySelector


class StrategySelectionStage(PipelineStage):
    """Translates the routing decision into an executable engine configuration.

    Delegates to the Phase 13.2 ``StrategySelector`` which resolves the
    strategy → model mapping against the registered strategy definitions,
    honours per-request model/threshold/reflect overrides and validates the
    target model against the model registry.

    When ``adaptive_auto_route`` is enabled (Phase 14) the resolved model is
    dropped unless the caller explicitly requested one, so the adaptive
    prediction engine can make its own routing decision.
    """

    name = STAGE_STRATEGY_SELECTION

    def __init__(
        self,
        strategy_selector: StrategySelector,
        event_publisher: EventPublisher | None = None,
        *,
        adaptive_auto_route: bool = False,
    ) -> None:
        self._selector = strategy_selector
        self._event_publisher = event_publisher
        self._adaptive_auto_route = adaptive_auto_route

    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None:
        analysis = state.query_analysis
        if analysis is None:
            raise StrategyResolutionError("Query analysis is missing before strategy selection")
        routing_decision = getattr(analysis, "routing_decision", None)
        if routing_decision is None:
            raise StrategyResolutionError("Query analysis carries no routing decision")

        try:
            engine_config = self._selector.resolve(
                routing_decision,
                input.request_params,
            )
        except StrategyResolutionError:
            raise
        except Exception as exc:
            raise StrategyResolutionError(f"Strategy resolution failed: {exc}") from exc

        if self._adaptive_auto_route and not (input.request_params.model or "").strip():
            engine_config = EngineConfiguration(
                model_name="",
                threshold=engine_config.threshold,
                use_reflection=False,
                use_semantic_validation=False,
            )

        state.engine_config = engine_config
        if self._event_publisher is not None:
            self._event_publisher.publish(
                EVENT_STRATEGY_SELECTED,
                {
                    "strategy": getattr(routing_decision, "selected_strategy", None),
                    "model_name": engine_config.model_name,
                    "threshold": engine_config.threshold,
                    "use_reflection": engine_config.use_reflection,
                },
            )
