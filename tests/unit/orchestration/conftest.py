from __future__ import annotations

from typing import Any

import pytest

from ares.agents.base import Agent
from ares.agents.types import (
    AgentCapability,
    AgentExecutionStatus,
    AgentMetadata,
    AgentOutput,
)


class SuccessAgent(Agent):
    def __init__(self, agent_id: str = "success_agent") -> None:
        super().__init__()
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"Success Agent {agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"decision": "approved", **input},
            confidence=0.95,
        )


class FailingAgent(Agent):
    def __init__(self, agent_id: str = "failing_agent") -> None:
        super().__init__()
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"Failing Agent {agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        raise ValueError("Agent execution failed")


class SlowAgent(Agent):
    def __init__(self, agent_id: str = "slow_agent") -> None:
        super().__init__()
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"Slow Agent {agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
                timeout_seconds=0.1,
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        import asyncio

        await asyncio.sleep(10)
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"result": "too late"},
        )


class VoteAgent(Agent):
    def __init__(self, decision: str = "yes", confidence: float = 0.8, agent_id: str = "vote_agent") -> None:
        super().__init__()
        self._decision = decision
        self._confidence = confidence
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"Vote Agent {agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.CONSENSUS_BUILDING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"vote": self._decision, "decision": self._decision},
            confidence=self._confidence,
        )


class SupervisorAgent(Agent):
    metadata = AgentMetadata(
        agent_id="supervisor_agent",
        name="Supervisor Agent",
        version="1.0",
        capabilities=frozenset({AgentCapability.PLANNING}),
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={
                "delegated_tasks": {
                    "worker_a": {"task": "analyze"},
                    "worker_b": {"task": "validate"},
                },
            },
            confidence=0.9,
        )


class WorkerAgent(Agent):
    def __init__(self, agent_id: str = "worker_a") -> None:
        super().__init__()
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"Worker {agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"completed": True, **input},
            confidence=0.85,
        )


@pytest.fixture
def success_agent() -> SuccessAgent:
    return SuccessAgent()


@pytest.fixture
def success_agent_a() -> SuccessAgent:
    return SuccessAgent(agent_id="success_agent_a")


@pytest.fixture
def success_agent_b() -> SuccessAgent:
    return SuccessAgent(agent_id="success_agent_b")


@pytest.fixture
def success_agent_c() -> SuccessAgent:
    return SuccessAgent(agent_id="success_agent_c")


@pytest.fixture
def failing_agent() -> FailingAgent:
    return FailingAgent()


@pytest.fixture
def failing_agent_a() -> FailingAgent:
    return FailingAgent(agent_id="failing_agent_a")


@pytest.fixture
def failing_agent_b() -> FailingAgent:
    return FailingAgent(agent_id="failing_agent_b")


@pytest.fixture
def slow_agent() -> SlowAgent:
    return SlowAgent()


@pytest.fixture
def vote_agent_yes() -> VoteAgent:
    return VoteAgent(decision="yes", confidence=0.9, agent_id="vote_yes")


@pytest.fixture
def vote_agent_no() -> VoteAgent:
    return VoteAgent(decision="no", confidence=0.7, agent_id="vote_no")


@pytest.fixture
def supervisor_agent() -> SupervisorAgent:
    return SupervisorAgent()


@pytest.fixture
def worker_a() -> WorkerAgent:
    return WorkerAgent(agent_id="worker_a")


@pytest.fixture
def worker_b() -> WorkerAgent:
    return WorkerAgent(agent_id="worker_b")
