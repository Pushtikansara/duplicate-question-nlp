from __future__ import annotations

import asyncio
import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import AgentExecutionStatus
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


class ParallelStrategy(OrchestrationStrategy):
    @property
    def strategy_type(self) -> OrchestrationStrategyType:
        return OrchestrationStrategyType.PARALLEL

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

        async def run_agent(agent: Agent) -> TaskNode:
            agent_id = agent.metadata.agent_id
            node = TaskNode(id=agent_id, agent_id=agent_id, input=input)
            try:
                node.status = TaskStatus.RUNNING
                agent_output = await agent.execute(input)
                elapsed = (time.time() - start) * 1000
                node.processing_time_ms = elapsed
                if agent_output.status == AgentExecutionStatus.SUCCESS:
                    node.status = TaskStatus.COMPLETED
                elif agent_output.status == AgentExecutionStatus.TIMEOUT:
                    node.status = TaskStatus.TIMEOUT
                else:
                    node.status = TaskStatus.FAILED
                    node.error = agent_output.error
                node.output = agent_output
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                node.processing_time_ms = elapsed
                node.status = TaskStatus.FAILED
                node.error = str(e)
            return node

        semaphore = asyncio.Semaphore(p.max_concurrency)

        async def run_agent_with_semaphore(agent: Agent) -> TaskNode:
            async with semaphore:
                return await run_agent(agent)

        tasks = [run_agent_with_semaphore(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, TaskNode):
                task_nodes[result.id] = result
            elif isinstance(result, Exception):
                logger = __import__("logging").getLogger(__name__)
                logger.error("Parallel agent execution error: %s", result)

        total_time = (time.time() - start) * 1000
        return aggregator.collect_results(
            task_nodes=task_nodes,
            shared_context=shared_context,
            workflow_id=shared_context.workflow_id,
            trace_id=shared_context.trace_id,
            processing_time_ms=total_time,
            strategy=self.strategy_type,
        )
