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


class PipelineStrategy(OrchestrationStrategy):
    def __init__(
        self,
        stage_map: dict[str, list[str]] | None = None,
    ) -> None:
        self._stage_map = stage_map or {}

    @property
    def strategy_type(self) -> OrchestrationStrategyType:
        return OrchestrationStrategyType.PIPELINE

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

        stages = self._build_stages(agents)
        pipeline_input = input
        all_failed = False

        for _stage_idx, stage in enumerate(stages):
            if all_failed:
                for agent in stage:
                    agent_id = agent.metadata.agent_id
                    node = TaskNode(
                        id=agent_id,
                        agent_id=agent_id,
                        status=TaskStatus.SKIPPED,
                        input=pipeline_input,
                    )
                    task_nodes[agent_id] = node
                continue

            stage_outputs: dict[str, Any] = {}
            stage_failed = False

            for agent in stage:
                agent_id = agent.metadata.agent_id
                node = TaskNode(
                    id=agent_id,
                    agent_id=agent_id,
                    input=pipeline_input,
                    depends_on=[a.metadata.agent_id for a in stage[: stage.index(agent)]]
                    if stage.index(agent) > 0
                    else [],
                )
                task_nodes[agent_id] = node

                try:
                    node.status = TaskStatus.RUNNING
                    agent_output = await agent.execute(pipeline_input)
                    elapsed = (time.time() - start) * 1000
                    node.processing_time_ms = elapsed
                    if agent_output.status == AgentExecutionStatus.SUCCESS:
                        node.status = TaskStatus.COMPLETED
                    else:
                        node.status = TaskStatus.FAILED
                        node.error = agent_output.error
                        stage_failed = True
                    node.output = agent_output
                    stage_outputs[agent_id] = agent_output.result
                except Exception as e:
                    elapsed = (time.time() - start) * 1000
                    node.processing_time_ms = elapsed
                    node.status = TaskStatus.FAILED
                    node.error = str(e)
                    stage_failed = True

            pipeline_input = stage_outputs
            all_failed = stage_failed and p.stop_on_first_error

        total_time = (time.time() - start) * 1000
        return aggregator.collect_results(
            task_nodes=task_nodes,
            shared_context=shared_context,
            workflow_id=shared_context.workflow_id,
            trace_id=shared_context.trace_id,
            processing_time_ms=total_time,
            strategy=self.strategy_type,
        )

    def _build_stages(self, agents: list[Agent]) -> list[list[Agent]]:
        if self._stage_map:
            agent_map = {a.metadata.agent_id: a for a in agents}
            stages: list[list[Agent]] = []
            for stage_ids in self._stage_map.values():
                stage = []
                for sid in stage_ids:
                    if sid in agent_map:
                        stage.append(agent_map[sid])
                if stage:
                    stages.append(stage)
            return stages

        return [[agent] for agent in agents]
