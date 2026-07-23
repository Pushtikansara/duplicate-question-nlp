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


class DebateStrategy(OrchestrationStrategy):
    @property
    def strategy_type(self) -> OrchestrationStrategyType:
        return OrchestrationStrategyType.DEBATE

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

        async def run_debater(agent: Agent) -> TaskNode:
            agent_id = agent.metadata.agent_id
            node = TaskNode(id=agent_id, agent_id=agent_id, input=input)

            debate_input = {
                **input,
                "debate_type": "analysis",
                "agent_name": agent.metadata.name,
            }

            try:
                node.status = TaskStatus.RUNNING
                agent_output = await agent.execute(debate_input)
                elapsed = (time.time() - start) * 1000
                node.processing_time_ms = elapsed
                if agent_output.status == AgentExecutionStatus.SUCCESS:
                    node.status = TaskStatus.COMPLETED
                else:
                    node.status = TaskStatus.FAILED
                    node.error = agent_output.error
                node.output = agent_output

                for other_agent in agents:
                    if other_agent.metadata.agent_id != agent_id:
                        self.send_message(
                            sender_id=agent_id,
                            recipient_id=other_agent.metadata.agent_id,
                            content=agent_output.result,
                            shared_context=shared_context,
                            message_type="debate_position",
                        )
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                node.processing_time_ms = elapsed
                node.status = TaskStatus.FAILED
                node.error = str(e)
            return node

        semaphore = asyncio.Semaphore(p.max_concurrency)

        async def run_with_semaphore(agent: Agent) -> TaskNode:
            async with semaphore:
                return await run_debater(agent)

        tasks = [run_with_semaphore(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, TaskNode):
                task_nodes[result.id] = result
            elif isinstance(result, Exception):
                logger = __import__("logging").getLogger(__name__)
                logger.error("Debate execution error: %s", result)

        all_outputs = [
            n.output for n in task_nodes.values() if n.output is not None and n.status == TaskStatus.COMPLETED
        ]

        if all_outputs and len(all_outputs) == len(agents):
            consensus = self._build_consensus(all_outputs)
            shared_context.set("consensus", consensus)

        total_time = (time.time() - start) * 1000
        return aggregator.collect_results(
            task_nodes=task_nodes,
            shared_context=shared_context,
            workflow_id=shared_context.workflow_id,
            trace_id=shared_context.trace_id,
            processing_time_ms=total_time,
            strategy=self.strategy_type,
        )

    def _build_consensus(
        self,
        outputs: list[Any],
    ) -> dict[str, Any]:
        if not outputs:
            return {"consensus": False, "agreement": 0.0}

        confidences = [o.confidence for o in outputs if hasattr(o, "confidence")]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        decisions = [o.result.get("decision", o.result.get("result", {})) for o in outputs if hasattr(o, "result")]

        return {
            "consensus": avg_confidence >= 0.5,
            "agreement": avg_confidence,
            "num_positions": len(outputs),
            "decisions": decisions,
        }
