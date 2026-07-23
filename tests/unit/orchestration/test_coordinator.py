from __future__ import annotations

from typing import Any

import pytest

from ares.agents.base import Agent
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput
from ares.orchestration.coordinator import AgentCoordinator
from ares.orchestration.exceptions import StrategyNotFoundError
from ares.orchestration.strategies.sequential import SequentialStrategy
from ares.orchestration.types import (
    OrchestrationStatus,
    OrchestrationStrategyType,
    RunPolicies,
    SharedAgentContext,
)


class SimpleAgent(Agent):
    def __init__(self, agent_id: str = "simple") -> None:
        super().__init__()
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"Agent {agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"echo": input},
            confidence=1.0,
        )


@pytest.fixture
def coordinator() -> AgentCoordinator:
    c = AgentCoordinator()
    c.agent_manager.register_agent(
        SimpleAgent,
        AgentMetadata(
            agent_id="simple",
            name="Simple",
            version="1.0",
            capabilities=frozenset({AgentCapability.REASONING}),
        ),
    )
    c.agent_manager.register_agent(
        SimpleAgent,
        AgentMetadata(
            agent_id="simple2",
            name="Simple2",
            version="1.0",
            capabilities=frozenset({AgentCapability.REASONING}),
        ),
    )
    return c


class TestAgentCoordinator:
    async def test_run_agents_sequential(self, coordinator: AgentCoordinator):
        result = await coordinator.run_agents(
            agent_ids=["simple"],
            input={"query": "hello"},
            strategy_type=OrchestrationStrategyType.SEQUENTIAL,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 1

    async def test_run_agents_parallel(self, coordinator: AgentCoordinator):
        result = await coordinator.run_agents(
            agent_ids=["simple", "simple2"],
            input={"query": "hello"},
            strategy_type=OrchestrationStrategyType.PARALLEL,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 2

    async def test_run_agents_debate(self, coordinator: AgentCoordinator):
        result = await coordinator.run_agents(
            agent_ids=["simple", "simple2"],
            input={"topic": "test"},
            strategy_type=OrchestrationStrategyType.DEBATE,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 2

    async def test_run_agents_voting(self, coordinator: AgentCoordinator):
        result = await coordinator.run_agents(
            agent_ids=["simple", "simple2"],
            input={"question": "test"},
            strategy_type=OrchestrationStrategyType.VOTING,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_run_agents_pipeline(self, coordinator: AgentCoordinator):
        result = await coordinator.run_agents(
            agent_ids=["simple", "simple2"],
            input={"query": "test"},
            strategy_type=OrchestrationStrategyType.PIPELINE,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_run_agents_hierarchical(self, coordinator: AgentCoordinator):
        result = await coordinator.run_agents(
            agent_ids=["simple", "simple2"],
            input={"task": "analyze"},
            strategy_type=OrchestrationStrategyType.HIERARCHICAL,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_run_agents_supervisor(self, coordinator: AgentCoordinator):
        result = await coordinator.run_agents(
            agent_ids=["simple", "simple2"],
            input={"task": "analyze"},
            strategy_type=OrchestrationStrategyType.SUPERVISOR,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_cancellation(self, coordinator: AgentCoordinator):
        run_id = "test_cancel"
        token = coordinator.cancellation_manager.create_token(run_id)
        token.cancel("Cancelled")

        async def should_cancel():
            return await coordinator.run_agents(
                agent_ids=["simple"],
                input={},
                strategy_type=OrchestrationStrategyType.SEQUENTIAL,
                shared_context=SharedAgentContext(workflow_id=run_id, trace_id=run_id),
            )

        result = await should_cancel()
        assert result.status == OrchestrationStatus.CANCELLED

    async def test_register_custom_strategy(self, coordinator: AgentCoordinator):
        strategy = SequentialStrategy()
        coordinator.register_strategy(OrchestrationStrategyType.SEQUENTIAL, strategy)
        assert coordinator.get_strategy(OrchestrationStrategyType.SEQUENTIAL) is strategy

    async def test_get_nonexistent_strategy(self, coordinator: AgentCoordinator):
        coordinator._strategies.clear()
        with pytest.raises(StrategyNotFoundError):
            coordinator.get_strategy(OrchestrationStrategyType.SEQUENTIAL)

    async def test_get_all_registered_strategies(self, coordinator: AgentCoordinator):
        for strategy_type in OrchestrationStrategyType:
            strategy = coordinator.get_strategy(strategy_type)
            assert strategy is not None
            assert strategy.strategy_type == strategy_type

    async def test_metrics_after_run(self, coordinator: AgentCoordinator):
        await coordinator.run_agents(
            agent_ids=["simple"],
            input={},
        )
        assert coordinator.metrics.total_runs == 1
        assert coordinator.metrics.completed_runs == 1

    async def test_run_with_policies(self, coordinator: AgentCoordinator):
        policies = RunPolicies(timeout_seconds=30.0, max_concurrency=5)
        result = await coordinator.run_agents(
            agent_ids=["simple"],
            input={},
            strategy_type=OrchestrationStrategyType.SEQUENTIAL,
            policies=policies,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_run_with_shared_context(self, coordinator: AgentCoordinator):
        ctx = SharedAgentContext(workflow_id="custom_wf", trace_id="custom_trace")
        result = await coordinator.run_agents(
            agent_ids=["simple"],
            input={},
            shared_context=ctx,
        )
        assert result.shared_context.workflow_id == "custom_wf"
        assert result.trace_id == "custom_trace"

    async def test_send_message(self, coordinator: AgentCoordinator):
        ctx = SharedAgentContext()
        coordinator.send_message("a", "b", {"key": "val"}, ctx)
        assert len(ctx.messages) == 1
        assert ctx.messages[0].sender_id == "a"
        assert ctx.messages[0].recipient_id == "b"
