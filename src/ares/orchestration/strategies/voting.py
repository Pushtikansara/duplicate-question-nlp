from __future__ import annotations

import asyncio
import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import AgentExecutionStatus, AgentOutput
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


class VotingStrategy(OrchestrationStrategy):
    def __init__(
        self,
        min_votes: int = 1,
        require_majority: bool = False,
    ) -> None:
        self._min_votes = min_votes
        self._require_majority = require_majority

    @property
    def strategy_type(self) -> OrchestrationStrategyType:
        return OrchestrationStrategyType.VOTING

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

        async def run_voter(agent: Agent) -> TaskNode:
            agent_id = agent.metadata.agent_id
            node = TaskNode(id=agent_id, agent_id=agent_id, input=input)

            vote_input = {
                **input,
                "vote_type": "analysis",
                "agent_name": agent.metadata.name,
            }

            try:
                node.status = TaskStatus.RUNNING
                agent_output = await agent.execute(vote_input)
                elapsed = (time.time() - start) * 1000
                node.processing_time_ms = elapsed
                if agent_output.status == AgentExecutionStatus.SUCCESS:
                    node.status = TaskStatus.COMPLETED
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

        async def run_with_semaphore(agent: Agent) -> TaskNode:
            async with semaphore:
                return await run_voter(agent)

        tasks = [run_with_semaphore(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, TaskNode):
                task_nodes[result.id] = result
            elif isinstance(result, Exception):
                logger = __import__("logging").getLogger(__name__)
                logger.error("Voting execution error: %s", result)

        all_outputs = [n.output for n in task_nodes.values() if n.output is not None]

        vote_result = self._tally_votes(all_outputs)
        shared_context.set("vote_result", vote_result)

        total_time = (time.time() - start) * 1000
        return aggregator.collect_results(
            task_nodes=task_nodes,
            shared_context=shared_context,
            workflow_id=shared_context.workflow_id,
            trace_id=shared_context.trace_id,
            processing_time_ms=total_time,
            strategy=self.strategy_type,
        )

    def _tally_votes(
        self,
        outputs: list[AgentOutput],
    ) -> dict[str, Any]:
        if not outputs:
            return {
                "winner": None,
                "total_votes": 0,
                "vote_counts": {},
                "confidence": 0.0,
                "majority_reached": False,
            }

        if len(outputs) < self._min_votes:
            return {
                "winner": None,
                "total_votes": len(outputs),
                "vote_counts": {},
                "confidence": 0.0,
                "majority_reached": False,
            }

        decisions: dict[str, list[float]] = {}
        for output in outputs:
            decision = str(output.result.get("decision", output.result.get("vote", "abstain")))
            if decision not in decisions:
                decisions[decision] = []
            decisions[decision].append(output.confidence)

        total_confidence = sum(sum(confs) for confs in decisions.values()) or 1.0

        vote_counts = {decision: len(confs) for decision, confs in decisions.items()}
        weighted_scores = {decision: sum(confs) / total_confidence for decision, confs in decisions.items()}

        winner = max(weighted_scores, key=lambda k: weighted_scores.get(k, 0.0))
        winner_confidence = weighted_scores[winner]
        total_votes = len(outputs)
        majority_needed = total_votes // 2 + 1 if self._require_majority else 1
        majority_reached = vote_counts.get(winner, 0) >= majority_needed

        return {
            "winner": winner,
            "total_votes": total_votes,
            "vote_counts": vote_counts,
            "weighted_scores": weighted_scores,
            "confidence": winner_confidence,
            "majority_reached": majority_reached,
        }
