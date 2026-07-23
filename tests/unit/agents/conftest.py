from __future__ import annotations

from typing import Any

import pytest

from ares.agents.base import Agent
from ares.agents.context import AgentContext
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput


class ConcreteAgent(Agent):
    metadata = AgentMetadata(
        agent_id="test_agent",
        name="Test Agent",
        version="1.0.0",
        description="A test agent",
        capabilities=frozenset({AgentCapability.PREDICTION}),
        tools_required=("predict",),
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        return self.create_output(
            status=AgentExecutionStatus.SUCCESS,
            result={"prediction": "test"},
            confidence=0.95,
            processing_time_ms=10.0,
        )


class FailingAgent(Agent):
    metadata = AgentMetadata(
        agent_id="failing_agent",
        name="Failing Agent",
        version="1.0.0",
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        msg = "Intentional failure"
        raise ValueError(msg)


class SlowAgent(Agent):
    metadata = AgentMetadata(
        agent_id="slow_agent",
        name="Slow Agent",
        version="1.0.0",
        timeout_seconds=0.05,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        import asyncio

        await asyncio.sleep(10)
        return self.create_output(status=AgentExecutionStatus.SUCCESS)


@pytest.fixture
def concrete_agent_class() -> type[Agent]:
    return ConcreteAgent


@pytest.fixture
def concrete_agent() -> Agent:
    return ConcreteAgent()


@pytest.fixture
def failing_agent() -> Agent:
    return FailingAgent()


@pytest.fixture
def slow_agent() -> Agent:
    return SlowAgent()


@pytest.fixture
def agent_context() -> AgentContext:
    import logging

    return AgentContext(
        agent_id="test_agent",
        logger=logging.getLogger("test"),
    )
