from __future__ import annotations

import time
from typing import Any

from ares.orchestration.cancellation import CancellationToken
from ares.orchestration.config import EngineConfiguration
from ares.orchestration.constants import (
    EVENT_ORCHESTRATION_FALLBACK,
    EVENT_STAGE_ABORTED,
    EVENT_STAGE_COMPLETE,
    EVENT_STAGE_STARTED,
    STAGE_PREDICTION,
    STAGE_STRATEGY_SELECTION,
)
from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.exceptions import (
    InvalidStageConfigurationError,
    MaxRetriesExceededError,
    ModelTimeoutError,
    ModelUnavailableError,
    PipelineAbortedError,
    RunCancelledError,
    StrategyResolutionError,
    TaskExecutionError,
)
from ares.orchestration.interfaces import (
    EventPublisher,
    FallbackPolicy,
    MetricsCollector,
    PipelineStage,
    RetryPolicy,
)
from ares.orchestration.metadata import ExecutionMetadata, OrchestrationMetadata
from ares.orchestration.stage_registry import StageRegistry
from ares.orchestration.types import StageStatus

_FALLBACKABLE_ERRORS: tuple[type[Exception], ...] = (
    TaskExecutionError,
    StrategyResolutionError,
    ModelUnavailableError,
    ModelTimeoutError,
    MaxRetriesExceededError,
)


class Pipeline:
    """Executes registered stages against a stage registry.

    For every stage the pipeline publishes lifecycle events, times the
    execution and records a ``StageResult``. Failures are evaluated against
    the injected retry policy; when the retry budget is exhausted and the
    failing stage consumes the engine configuration, the fallback policy
    provides an alternative configuration and the stage is re-executed once.
    Cancellation tokens abort execution with ``RunCancelledError``.
    """

    def __init__(
        self,
        registry: StageRegistry,
        *,
        retry_policy: RetryPolicy | None = None,
        fallback_policy: FallbackPolicy | None = None,
        event_publisher: EventPublisher | None = None,
        metrics: MetricsCollector | None = None,
    ) -> None:
        self._registry = registry
        self._retry_policy = retry_policy
        self._fallback_policy = fallback_policy
        self._event_publisher = event_publisher
        self._metrics = metrics
        self._current_stage = ""

    @property
    def registry(self) -> StageRegistry:
        return self._registry

    def execute(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
        cancellation_token: CancellationToken | None = None,
    ) -> PipelineState:
        stages = self._registry.ordered_stages()
        if not stages:
            raise InvalidStageConfigurationError("No pipeline stages are registered or enabled")

        try:
            self._execute_stages(stages, input, state, metadata, cancellation_token)
        except Exception as exc:
            state.error = str(exc)
            if self._metrics is not None:
                self._metrics.increment("orchestration.pipeline.failed", {"stage": self._current_stage})
            raise
        finally:
            self._finalize_execution_metadata(state, metadata)
        return state

    def _execute_stages(
        self,
        stages: list[PipelineStage],
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
        cancellation_token: CancellationToken | None,
    ) -> None:
        index = 0
        while index < len(stages):
            stage = stages[index]
            self._current_stage = stage.name
            self._check_cancelled(cancellation_token)
            self._publish(EVENT_STAGE_STARTED, {"stage": stage.name})

            started = time.time()
            try:
                self._run_with_retries(stage, input, state, metadata, cancellation_token)
            except Exception as exc:
                duration_ms = (time.time() - started) * 1000.0
                metadata.add_stage(
                    stage.name,
                    duration_ms,
                    StageStatus.FAILED,
                    detail={"error": str(exc)},
                )
                self._publish(EVENT_STAGE_ABORTED, {"stage": stage.name, "error": str(exc)})
                if self._metrics is not None:
                    self._metrics.increment("orchestration.stage.failed", {"stage": stage.name})
                if self._should_fallback(stage, exc, state):
                    fallback_policy = self._fallback_policy
                    if fallback_policy is None:
                        raise
                    fallback_config = fallback_policy.get_fallback_config()
                    state.engine_config = fallback_config
                    state.fallback_used = True
                    self._mark_fallback_in_execution_metadata(state)
                    self._publish(
                        EVENT_ORCHESTRATION_FALLBACK,
                        {
                            "stage": stage.name,
                            "fallback_model": fallback_config.model_name,
                            "error": str(exc),
                        },
                    )
                    continue
                raise
            else:
                duration_ms = (time.time() - started) * 1000.0
                metadata.add_stage(stage.name, duration_ms, StageStatus.SUCCESS)
                self._publish(EVENT_STAGE_COMPLETE, {"stage": stage.name, "duration_ms": duration_ms})
                if self._metrics is not None:
                    self._metrics.timing("orchestration.stage.duration_ms", duration_ms, {"stage": stage.name})
                index += 1

    def _run_with_retries(
        self,
        stage: PipelineStage,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
        cancellation_token: CancellationToken | None,
    ) -> None:
        attempt = 0
        while True:
            attempt += 1
            self._check_cancelled(cancellation_token)
            try:
                stage.run(input, state, metadata)
                return
            except Exception as exc:
                if isinstance(exc, PipelineAbortedError):
                    raise
                if self._retry_policy is None or not self._retry_policy.should_retry(attempt, exc):
                    raise
                self._mark_retry_in_execution_metadata(state)
                backoff = self._retry_policy.get_backoff(attempt)
                if backoff > 0:
                    time.sleep(backoff)

    def _should_fallback(self, stage: PipelineStage, error: Exception, state: PipelineState) -> bool:
        if state.fallback_used:
            return False
        if self._fallback_policy is None:
            return False
        if stage.name not in (STAGE_STRATEGY_SELECTION, STAGE_PREDICTION):
            return False
        return isinstance(error, _FALLBACKABLE_ERRORS)

    def _check_cancelled(self, cancellation_token: CancellationToken | None) -> None:
        if cancellation_token is not None and cancellation_token.is_cancelled:
            raise RunCancelledError("Pipeline execution was cancelled")

    def _publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        if self._event_publisher is not None:
            self._event_publisher.publish(event_type, payload)

    @staticmethod
    def _mark_retry_in_execution_metadata(state: PipelineState) -> None:
        execution_metadata = state.execution_metadata
        if isinstance(execution_metadata, ExecutionMetadata):
            execution_metadata.retry_count += 1

    @staticmethod
    def _mark_fallback_in_execution_metadata(state: PipelineState) -> None:
        execution_metadata = state.execution_metadata
        if isinstance(execution_metadata, ExecutionMetadata):
            execution_metadata.fallback_used = True
            execution_metadata.strategy = "fallback"

    @staticmethod
    def _finalize_execution_metadata(state: PipelineState, metadata: OrchestrationMetadata) -> None:
        execution_metadata = state.execution_metadata
        if not isinstance(execution_metadata, ExecutionMetadata):
            return
        execution_metadata.stages = list(metadata.stages)
        execution_metadata.total_duration_ms = metadata.elapsed_ms()
        execution_metadata.stage_timings = {s.name: s.duration_ms for s in metadata.stages}
        if state.error is not None:
            execution_metadata.error = state.error
        engine_config = state.engine_config
        if isinstance(engine_config, EngineConfiguration):
            execution_metadata.model_name = engine_config.model_name
        Pipeline._refresh_result_trace(state, metadata)

    @staticmethod
    def _refresh_result_trace(state: PipelineState, metadata: OrchestrationMetadata) -> None:
        """Attach the complete trace (including the final stage) to the result.

        The result enrichment stage attaches the trace from within the stage
        execution, so its own entry is not yet recorded at that point. This
        final refresh supersedes it with the complete stage list.
        """
        result = state.prediction_result
        if result is None or not hasattr(result, "orchestration_trace"):
            return
        trace: dict[str, Any] = metadata.to_trace_dict()
        execution_metadata = state.execution_metadata
        if isinstance(execution_metadata, ExecutionMetadata):
            trace["request_id"] = execution_metadata.request_id
            trace["fallback_used"] = execution_metadata.fallback_used
            trace["retry_count"] = execution_metadata.retry_count
            trace["strategy"] = execution_metadata.strategy
            trace["model_name"] = execution_metadata.model_name
        result.orchestration_trace = trace
