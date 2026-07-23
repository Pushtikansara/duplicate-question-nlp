from __future__ import annotations

import time
from typing import Any

from ares.agents.base import Agent
from ares.orchestration.aggregator import ResultAggregator
from ares.orchestration.strategies.base import OrchestrationStrategy
from ares.orchestration.types import (
    OrchestrationResult,
    OrchestrationStrategyType,
    RunPolicies,
    SharedAgentContext,
    TaskNode,
    TaskStatus,
)


class SupervisorStrategy(OrchestrationStrategy):
    @property
    def strategy_type(self) -> OrchestrationStrategyType:
        return OrchestrationStrategyType.SUPERVISOR

    async def execute(
        self,
        agents: list[Agent],
        input: dict[str, Any],
        shared_context: SharedAgentContext,
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult:
        task_nodes: dict[str, TaskNode] = {}
        aggregator = ResultAggregator()
        start = time.time()

        if len(agents) < 2:
            total_time = (time.time() - start) * 1000
            return aggregator.collect_results(
                task_nodes=task_nodes,
                shared_context=shared_context,
                workflow_id=shared_context.workflow_id,
                trace_id=shared_context.trace_id,
                processing_time_ms=total_time,
                strategy=self.strategy_type,
            )

        supervisor = agents[0]
        workers = agents[1:]

        supervisor_node = TaskNode(
            id=supervisor.metadata.agent_id,
            agent_id=supervisor.metadata.agent_id,
            input={"task": "supervise", **input},
        )
        task_nodes[supervisor_node.id] = supervisor_node

        try:
            supervisor_node.status = TaskStatus.RUNNING
            supervisor_input = {
                "task": "delegate",
                "workers": [w.metadata.agent_id for w in workers],
                **input,
            }
            supervisor_output = await supervisor.execute(supervisor_input)
            elapsed = (time.time() - start) * 1000
            supervisor_node.processing_time_ms = elapsed
            supervisor_node.output = supervisor_output

            if supervisor_output.status.name == "SUCCESS":
                supervisor_node.status = TaskStatus.COMPLETED
            else:
                supervisor_node.status = TaskStatus.FAILED
                supervisor_node.error = supervisor_output.error
                total_time = (time.time() - start) * 1000
                return aggregator.collect_results(
                    task_nodes=task_nodes,
                    shared_context=shared_context,
                    workflow_id=shared_context.workflow_id,
                    trace_id=shared_context.trace_id,
                    processing_time_ms=total_time,
                    strategy=self.strategy_type,
                )

            delegated_tasks = supervisor_output.result.get("delegated_tasks", {})
            if not delegated_tasks:
                delegated_tasks = {w.metadata.agent_id: input for w in workers}
        except Exception as e:
            supervisor_node.status = TaskStatus.FAILED
            supervisor_node.error = str(e)
            total_time = (time.time() - start) * 1000
            return aggregator.collect_results(
                task_nodes=task_nodes,
                shared_context=shared_context,
                workflow_id=shared_context.workflow_id,
                trace_id=shared_context.trace_id,
                processing_time_ms=total_time,
                strategy=self.strategy_type,
            )

        for worker in workers:
            worker_id = worker.metadata.agent_id
            worker_input = delegated_tasks.get(worker_id, input)
            worker_node = TaskNode(
                id=worker_id,
                agent_id=worker_id,
                depends_on=[supervisor_node.id],
                input=worker_input,
            )
            task_nodes[worker_id] = worker_node

            try:
                worker_node.status = TaskStatus.RUNNING
                worker_output = await worker.execute(worker_input)
                elapsed = (time.time() - start) * 1000
                worker_node.processing_time_ms = elapsed
                worker_node.output = worker_output
                if worker_output.status.name == "SUCCESS":
                    worker_node.status = TaskStatus.COMPLETED
                else:
                    worker_node.status = TaskStatus.FAILED
                    worker_node.error = worker_output.error

                self.send_message(
                    sender_id=worker_id,
                    recipient_id=supervisor.metadata.agent_id,
                    content=worker_output.result,
                    shared_context=shared_context,
                    message_type="worker_result",
                )
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                worker_node.processing_time_ms = elapsed
                worker_node.status = TaskStatus.FAILED
                worker_node.error = str(e)

                self.send_message(
                    sender_id=worker_id,
                    recipient_id=supervisor.metadata.agent_id,
                    content={"error": str(e)},
                    shared_context=shared_context,
                    message_type="worker_error",
                )

        total_time = (time.time() - start) * 1000
        return aggregator.collect_results(
            task_nodes=task_nodes,
            shared_context=shared_context,
            workflow_id=shared_context.workflow_id,
            trace_id=shared_context.trace_id,
            processing_time_ms=total_time,
            strategy=self.strategy_type,
        )
