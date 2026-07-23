from __future__ import annotations

from typing import Any

import pytest

from ares.agents.base import Agent
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput
from ares.orchestration.engine import OrchestrationEngine
from ares.orchestration.types import OrchestrationStatus, OrchestrationStrategyType


class EchoAgent(Agent):
    def __init__(self, agent_id: str = "echo") -> None:
        super().__init__()
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"Echo {agent_id}",
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
def engine() -> OrchestrationEngine:
    eng = OrchestrationEngine()
    eng.coordinator.agent_manager.register_agent(
        EchoAgent,
        AgentMetadata(
            agent_id="echo",
            name="Echo",
            version="1.0",
            capabilities=frozenset({AgentCapability.REASONING}),
        ),
    )
    eng.coordinator.agent_manager.register_agent(
        EchoAgent,
        AgentMetadata(
            agent_id="echo2",
            name="Echo2",
            version="1.0",
            capabilities=frozenset({AgentCapability.REASONING}),
        ),
    )
    eng.coordinator.agent_manager.register_agent(
        EchoAgent,
        AgentMetadata(
            agent_id="echo3",
            name="Echo3",
            version="1.0",
            capabilities=frozenset({AgentCapability.REASONING}),
        ),
    )
    return eng


class TestOrchestrationEngine:
    async def test_run_single(self, engine: OrchestrationEngine):
        result = await engine.run_single("echo", {"query": "hello"})
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_run_agents(self, engine: OrchestrationEngine):
        result = await engine.run_agents(
            agent_ids=["echo", "echo2"],
            input={"query": "hello"},
            strategy=OrchestrationStrategyType.PARALLEL,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 2

    async def test_run_parallel(self, engine: OrchestrationEngine):
        result = await engine.run_parallel(
            agent_ids=["echo", "echo2", "echo3"],
            input={"query": "parallel"},
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 3

    async def test_run_debate(self, engine: OrchestrationEngine):
        result = await engine.run_debate(
            agent_ids=["echo", "echo2"],
            input={"topic": "debate"},
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 2

    async def test_run_voting(self, engine: OrchestrationEngine):
        result = await engine.run_voting(
            agent_ids=["echo", "echo2"],
            input={"question": "vote"},
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_run_pipeline(self, engine: OrchestrationEngine):
        result = await engine.run_pipeline(
            agent_ids=["echo", "echo2"],
            input={"data": "pipeline"},
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_get_metrics_summary(self, engine: OrchestrationEngine):
        summary = engine.get_metrics_summary()
        assert summary["total_runs"] == 0
        assert summary["success_rate"] == 1.0

        await engine.run_single("echo", {})
        summary = engine.get_metrics_summary()
        assert summary["total_runs"] == 1
        assert summary["completed_runs"] == 1

    async def test_coordinator_property(self, engine: OrchestrationEngine):
        assert engine.coordinator is not None
        assert engine.metrics is engine.coordinator.metrics
