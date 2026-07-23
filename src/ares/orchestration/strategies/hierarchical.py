from __future__ import annotations

import asyncio
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


class HierarchicalStrategy(OrchestrationStrategy):
    @property
    def strategy_type(self) -> OrchestrationStrategyType:
        return OrchestrationStrategyType.HIERARCHICAL

    async def execute(
        self,
        agents: list[Agent],
        input: dict[str, Any],
        shared_context: SharedAgentContext,
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult:
        p = policies or RunPolicies()
        task_nodes: dict[str, TaskNode] = {}
        aggregator = ResultAggregator()
        start = time.time()

        if not agents:
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
            input=input,
        )
        task_nodes[supervisor_node.id] = supervisor_node

        try:
            supervisor_node.status = TaskStatus.RUNNING
            supervisor_output = await supervisor.execute(input)
            supervisor_elapsed = (time.time() - start) * 1000
            supervisor_node.processing_time_ms = supervisor_elapsed
            supervisor_node.output = supervisor_output

            if supervisor_output.status.name == "SUCCESS" or supervisor_output.status.name == "SUCCESS":
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

            sub_tasks = supervisor_output.result.get("sub_tasks", {})
            if isinstance(sub_tasks, dict):
                worker_inputs = sub_tasks
            elif isinstance(sub_tasks, list):
                worker_inputs = {
                    w.metadata.agent_id: {"task": sub_tasks[i] if i < len(sub_tasks) else {}}
                    for i, w in enumerate(workers)
                }
            else:
                worker_inputs = {w.metadata.agent_id: {} for w in workers}
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

        async def run_worker(worker: Agent, worker_input: dict[str, Any]) -> TaskNode:
            worker_id = worker.metadata.agent_id
            node = TaskNode(
                id=worker_id,
                agent_id=worker_id,
                depends_on=[supervisor_node.id],
                input=worker_input,
            )
            try:
                node.status = TaskStatus.RUNNING
                worker_output = await worker.execute(worker_input)
                elapsed = (time.time() - start) * 1000
                node.processing_time_ms = elapsed
                node.output = worker_output
                if worker_output.status.name in ("SUCCESS",):
                    node.status = TaskStatus.COMPLETED
                else:
                    node.status = TaskStatus.FAILED
                    node.error = worker_output.error
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                node.processing_time_ms = elapsed
                node.status = TaskStatus.FAILED
                node.error = str(e)
            return node

        semaphore = asyncio.Semaphore(p.max_concurrency)

        async def run_with_semaphore(worker: Agent, inp: dict[str, Any]) -> TaskNode:
            async with semaphore:
                return await run_worker(worker, inp)

        worker_tasks = [
            run_with_semaphore(
                w,
                worker_inputs.get(w.metadata.agent_id, {}),
            )
            for w in workers
        ]
        worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)

        for result in worker_results:
            if isinstance(result, TaskNode):
                task_nodes[result.id] = result
            elif isinstance(result, Exception):
                logger = __import__("logging").getLogger(__name__)
                logger.error("Worker execution error: %s", result)

        total_time = (time.time() - start) * 1000
        return aggregator.collect_results(
            task_nodes=task_nodes,
            shared_context=shared_context,
            workflow_id=shared_context.workflow_id,
            trace_id=shared_context.trace_id,
            processing_time_ms=total_time,
            strategy=self.strategy_type,
        )
