from __future__ import annotations

import logging
from typing import Any

from ares.agents.manager import AgentManager
from ares.agents.registry import AgentRegistry
from ares.orchestration.coordinator import AgentCoordinator
from ares.orchestration.metrics import OrchestrationMetrics
from ares.orchestration.types import (
    OrchestrationResult,
    OrchestrationStrategyType,
    RunPolicies,
    SharedAgentContext,
)

logger = logging.getLogger(__name__)


class OrchestrationEngine:
    def __init__(
        self,
        coordinator: AgentCoordinator | None = None,
        agent_manager: AgentManager | None = None,
        registry: AgentRegistry | None = None,
        event_bus: Any = None,
    ) -> None:
        self._coordinator = coordinator or AgentCoordinator(
            agent_manager=agent_manager,
            registry=registry,
            event_bus=event_bus,
        )

    @property
    def coordinator(self) -> AgentCoordinator:
        return self._coordinator

    @property
    def metrics(self) -> OrchestrationMetrics:
        return self._coordinator.metrics

    async def run_agents(
        self,
        agent_ids: list[str],
        input: dict[str, Any],
        strategy: OrchestrationStrategyType = OrchestrationStrategyType.SEQUENTIAL,
        policies: RunPolicies | None = None,
        shared_context: SharedAgentContext | None = None,
    ) -> OrchestrationResult:
        return await self._coordinator.run_agents(
            agent_ids=agent_ids,
            input=input,
            strategy_type=strategy,
            policies=policies,
            shared_context=shared_context,
        )

    async def run_single(
        self,
        agent_id: str,
        input: dict[str, Any],
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult:
        return await self.run_agents(
            agent_ids=[agent_id],
            input=input,
            strategy=OrchestrationStrategyType.SEQUENTIAL,
            policies=policies,
        )

    async def run_parallel(
        self,
        agent_ids: list[str],
        input: dict[str, Any],
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult:
        return await self.run_agents(
            agent_ids=agent_ids,
            input=input,
            strategy=OrchestrationStrategyType.PARALLEL,
            policies=policies,
        )

    async def run_debate(
        self,
        agent_ids: list[str],
        input: dict[str, Any],
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult:
        return await self.run_agents(
            agent_ids=agent_ids,
            input=input,
            strategy=OrchestrationStrategyType.DEBATE,
            policies=policies,
        )

    async def run_voting(
        self,
        agent_ids: list[str],
        input: dict[str, Any],
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult:
        return await self.run_agents(
            agent_ids=agent_ids,
            input=input,
            strategy=OrchestrationStrategyType.VOTING,
            policies=policies,
        )

    async def run_pipeline(
        self,
        agent_ids: list[str],
        input: dict[str, Any],
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult:
        return await self.run_agents(
            agent_ids=agent_ids,
            input=input,
            strategy=OrchestrationStrategyType.PIPELINE,
            policies=policies,
        )

    def get_metrics_summary(self) -> dict[str, Any]:
        m = self.metrics
        return {
            "total_runs": m.total_runs,
            "completed_runs": m.completed_runs,
            "failed_runs": m.failed_runs,
            "cancelled_runs": m.cancelled_runs,
            "timed_out_runs": m.timed_out_runs,
            "total_tasks": m.total_tasks,
            "completed_tasks": m.completed_tasks,
            "failed_tasks": m.failed_tasks,
            "retried_tasks": m.retried_tasks,
            "avg_processing_time_ms": m.average_processing_time_ms(),
            "success_rate": m.success_rate(),
            "strategy_counts": dict(m.strategy_counts),
        }
