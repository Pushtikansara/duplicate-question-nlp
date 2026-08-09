from __future__ import annotations

from ares.orchestration.constants import (
    EVENT_PREDICTION_COMPLETE,
    EVENT_PREDICTION_STARTED,
    STAGE_PREDICTION,
)
from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.exceptions import OrchestrationError, TaskExecutionError
from ares.orchestration.interfaces import EventPublisher, PipelineStage, PredictionEngine
from ares.orchestration.metadata import OrchestrationMetadata


class PredictionStage(PipelineStage):
    """Runs the prediction engine with the selected engine configuration.

    The engine is invoked through the ``PredictionEngine`` protocol. Failures
    raised by the engine implementation are re-raised as-is when they already
    are orchestration errors (e.g. ``ModelUnavailableError`` from the engine
    adapter), otherwise they are wrapped in ``TaskExecutionError``.
    """

    name = STAGE_PREDICTION

    def __init__(
        self,
        engine: PredictionEngine,
        event_publisher: EventPublisher | None = None,
    ) -> None:
        self._engine = engine
        self._event_publisher = event_publisher

    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None:
        engine_config = state.engine_config
        if engine_config is None:
            raise TaskExecutionError("No engine configuration selected before prediction")

        self._publish(EVENT_PREDICTION_STARTED)
        try:
            result = self._engine.predict(
                input.question1,
                input.question2,
                model=engine_config.model_name,
                threshold=engine_config.threshold,
                reflect=engine_config.use_reflection,
                timeout_ms=input.request_params.timeout_ms,
            )
        except OrchestrationError:
            raise
        except Exception as exc:
            raise TaskExecutionError(f"Prediction failed: {exc}") from exc

        state.prediction_result = result
        self._publish(EVENT_PREDICTION_COMPLETE)

    def _publish(self, event_type: str) -> None:
        if self._event_publisher is not None:
            self._event_publisher.publish(event_type)
