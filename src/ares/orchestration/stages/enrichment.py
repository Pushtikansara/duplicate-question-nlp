from __future__ import annotations

from typing import Any

from ares.orchestration.constants import STAGE_RESULT_ENRICHMENT
from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.exceptions import TaskExecutionError
from ares.orchestration.interfaces import PipelineStage
from ares.orchestration.metadata import ExecutionMetadata, OrchestrationMetadata


class ResultEnrichmentStage(PipelineStage):
    """Attaches the orchestration trace to the prediction result.

    The trace combines the orchestration metadata (per-stage statuses and
    timings) with the execution metadata (retry count, fallback usage,
    strategy and model name). The trace is stored on
    ``PredictionResult.orchestration_trace``.
    """

    name = STAGE_RESULT_ENRICHMENT

    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None:
        result = state.prediction_result
        if result is None:
            raise TaskExecutionError("No prediction result to enrich")

        trace: dict[str, Any] = metadata.to_trace_dict()
        execution_metadata = state.execution_metadata
        if isinstance(execution_metadata, ExecutionMetadata):
            trace["request_id"] = execution_metadata.request_id
            trace["fallback_used"] = execution_metadata.fallback_used
            trace["retry_count"] = execution_metadata.retry_count
            trace["strategy"] = execution_metadata.strategy
            trace["model_name"] = execution_metadata.model_name
        else:
            trace["fallback_used"] = state.fallback_used
        result.orchestration_trace = trace
