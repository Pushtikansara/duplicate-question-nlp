from __future__ import annotations

from typing import Any

from ares.agents.base import Agent
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentOutput


class TestAgent:
    def test_metadata_is_required(self, concrete_agent: Agent) -> None:
        assert concrete_agent.metadata.agent_id == "test_agent"
        assert concrete_agent.metadata.name == "Test Agent"

    def test_get_capabilities(self, concrete_agent: Agent) -> None:
        caps = concrete_agent.get_capabilities()
        assert AgentCapability.PREDICTION in caps

    def test_execute_returns_output(self, concrete_agent: Agent) -> None:
        import asyncio

        output = asyncio.run(concrete_agent.execute({"input": "test"}))
        assert isinstance(output, AgentOutput)
        assert output.status == AgentExecutionStatus.SUCCESS
        assert output.result["prediction"] == "test"
        assert output.confidence == 0.95

    def test_set_context(self, concrete_agent: Agent, agent_context: Any) -> None:
        concrete_agent.set_context(agent_context)
        assert concrete_agent.context is agent_context

    def test_create_output(self, concrete_agent: Agent, agent_context: Any) -> None:
        concrete_agent.set_context(agent_context)
        output = concrete_agent.create_output(
            status=AgentExecutionStatus.SUCCESS,
            result={"key": "val"},
            confidence=0.8,
            evidence=[{"id": "e1"}],
            warnings=["warn"],
            processing_time_ms=5.0,
        )
        assert output.agent_id == "test_agent"
        assert output.status == AgentExecutionStatus.SUCCESS
        assert output.result["key"] == "val"
        assert output.confidence == 0.8
        assert len(output.evidence) == 1
        assert len(output.warnings) == 1
        assert output.processing_time_ms == 5.0

    def test_set_context_updates_logger(self, concrete_agent: Agent, agent_context: Any) -> None:
        concrete_agent.set_context(agent_context)
        assert concrete_agent._logger.name == "test"

    def test_lifecycle_hooks_are_noop_by_default(self, concrete_agent: Agent) -> None:
        import asyncio

        assert asyncio.run(concrete_agent.on_register()) is None
        assert asyncio.run(concrete_agent.on_load()) is None
        assert asyncio.run(concrete_agent.on_activate()) is None
        assert asyncio.run(concrete_agent.on_pause()) is None
        assert asyncio.run(concrete_agent.on_resume()) is None
        assert asyncio.run(concrete_agent.on_disable()) is None
