from __future__ import annotations

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


class SequentialStrategy(OrchestrationStrategy):
    @property
    def strategy_type(self) -> OrchestrationStrategyType:
        return OrchestrationStrategyType.SEQUENTIAL

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

        previous_output: dict[str, Any] = input

        for i, agent in enumerate(agents):
            agent_id = agent.metadata.agent_id
            node = TaskNode(
                id=agent_id,
                agent_id=agent_id,
                depends_on=[agents[i - 1].metadata.agent_id] if i > 0 else [],
                input=previous_output,
            )
            task_nodes[agent_id] = node

            try:
                node.status = TaskStatus.RUNNING
                agent_output = await agent.execute(previous_output)
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
                previous_output = {**input, **agent_output.result}
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                node.processing_time_ms = elapsed
                node.status = TaskStatus.FAILED
                node.error = str(e)
                if p.stop_on_first_error:
                    break

        total_time = (time.time() - start) * 1000
        return aggregator.collect_results(
            task_nodes=task_nodes,
            shared_context=shared_context,
            workflow_id=shared_context.workflow_id,
            trace_id=shared_context.trace_id,
            processing_time_ms=total_time,
            strategy=self.strategy_type,
        )
