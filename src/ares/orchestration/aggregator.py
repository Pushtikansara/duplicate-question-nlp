from __future__ import annotations

import logging
from typing import Any

from ares.agents.types import AgentOutput
from ares.orchestration.types import OrchestrationResult, OrchestrationStatus, SharedAgentContext, TaskNode, TaskStatus

logger = logging.getLogger(__name__)


class ResultAggregator:
    def collect_results(
        self,
        task_nodes: dict[str, TaskNode],
        shared_context: SharedAgentContext,
        workflow_id: str = "",
        trace_id: str = "",
        processing_time_ms: float = 0.0,
        strategy: Any = None,
    ) -> OrchestrationResult:
        agent_outputs: list[AgentOutput] = []
        for node in task_nodes.values():
            if node.output is not None:
                agent_outputs.append(node.output)

        if not task_nodes:
            return OrchestrationResult(
                workflow_id=workflow_id,
                status=OrchestrationStatus.COMPLETED,
                agent_results=[],
                task_nodes={},
                shared_context=shared_context,
                processing_time_ms=processing_time_ms,
                trace_id=trace_id,
                strategy=strategy,
            )

        all_failed = all(n.status == TaskStatus.FAILED for n in task_nodes.values())
        any_failed = any(n.status == TaskStatus.FAILED for n in task_nodes.values())
        any_cancelled = any(n.status == TaskStatus.CANCELLED for n in task_nodes.values())
        any_timeout = any(n.status == TaskStatus.TIMEOUT for n in task_nodes.values())

        if all_failed:
            status = OrchestrationStatus.FAILED
        elif any_cancelled:
            status = OrchestrationStatus.CANCELLED
        elif any_timeout or any_failed:
            status = OrchestrationStatus.PARTIAL
        else:
            status = OrchestrationStatus.COMPLETED

        error = self._build_error_summary(task_nodes)

        return OrchestrationResult(
            workflow_id=workflow_id,
            status=status,
            agent_results=agent_outputs,
            task_nodes=task_nodes,
            shared_context=shared_context,
            processing_time_ms=processing_time_ms,
            error=error,
            trace_id=trace_id,
            stage_timings=self._compute_stage_timings(task_nodes),
            strategy=strategy,
        )

    def merge_outputs(
        self,
        outputs: list[AgentOutput],
        merge_strategy: str = "concat",
    ) -> dict[str, Any]:
        if not outputs:
            return {}

        if merge_strategy == "concat":
            merged: dict[str, Any] = {}
            for output in outputs:
                for key, value in output.result.items():
                    if key in merged:
                        if isinstance(merged[key], list) and isinstance(value, list):
                            merged[key] = merged[key] + value
                        elif isinstance(merged[key], dict) and isinstance(value, dict):
                            merged[key] = {**merged[key], **value}
                        else:
                            merged[key] = value
                    else:
                        merged[key] = value
            return merged

        if merge_strategy == "first":
            return outputs[0].result if outputs else {}

        if merge_strategy == "last":
            return outputs[-1].result if outputs else {}

        if merge_strategy == "weighted":
            return self._weighted_merge(outputs)

        return {}

    def select_best_output(
        self,
        outputs: list[AgentOutput],
        by: str = "confidence",
    ) -> AgentOutput | None:
        if not outputs:
            return None

        if by == "confidence":
            return max(outputs, key=lambda o: o.confidence)

        if by == "first":
            return outputs[0]

        return None

    def _weighted_merge(self, outputs: list[AgentOutput]) -> dict[str, Any]:
        merged: dict[str, list[Any]] = {}
        total_confidence = sum(o.confidence for o in outputs) or 1.0

        for output in outputs:
            weight = output.confidence / total_confidence
            for key, value in output.result.items():
                if key not in merged:
                    merged[key] = []
                merged[key].append((value, weight))

        result: dict[str, Any] = {}
        for key, values in merged.items():
            if all(isinstance(v, (int, float)) for v, _ in values):
                result[key] = sum(v * w for v, w in values)
            elif all(isinstance(v, str) for v, _ in values):
                result[key] = max(values, key=lambda x: x[1])[0]
            else:
                result[key] = [v for v, _ in values]
        return result

    def _build_error_summary(
        self,
        task_nodes: dict[str, TaskNode],
    ) -> str | None:
        errors = [f"'{nid}': {n.error}" for nid, n in task_nodes.items() if n.error]
        return "; ".join(errors) if errors else None

    def _compute_stage_timings(
        self,
        task_nodes: dict[str, TaskNode],
    ) -> dict[str, float]:
        return {nid: node.processing_time_ms for nid, node in task_nodes.items() if node.processing_time_ms > 0}
