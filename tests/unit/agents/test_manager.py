from __future__ import annotations

from typing import Any

import pytest

import ares.agents.exceptions as aex
from ares.agents.context import AgentContext
from ares.agents.manager import AgentManager
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentPermissions, AgentStatus


class TestAgentManager:
    @pytest.mark.asyncio
    async def test_register_agent(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(
            agent_id="test_agent",
            name="Test Agent",
            version="1.0.0",
            capabilities=frozenset({AgentCapability.PREDICTION}),
        )
        perms = AgentPermissions(agent_id="test_agent", allowed_tools=("predict",))
        agent_id = manager.register_agent(concrete_agent_class, metadata, perms)
        assert agent_id == "test_agent"
        assert manager.has_agent("test_agent")

    @pytest.mark.asyncio
    async def test_register_existing_agent(self, concrete_agent: Any) -> None:
        manager = AgentManager()
        agent_id = manager.register_existing_agent(concrete_agent)
        assert agent_id == "test_agent"

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        await manager.load_agent("test_agent")
        assert manager.get_agent_info("test_agent").status == AgentStatus.LOADED
        await manager.activate_agent("test_agent")
        assert manager.get_agent_info("test_agent").status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_invoke_agent_success(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        await manager.load_agent("test_agent")
        await manager.activate_agent("test_agent")
        output = await manager.invoke_agent("test_agent", {"input": "test"})
        assert output.status == AgentExecutionStatus.SUCCESS
        assert output.confidence == 0.95
        assert output.result["prediction"] == "test"

    @pytest.mark.asyncio
    async def test_invoke_not_active_raises(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        with pytest.raises(aex.AgentExecutionError):
            await manager.invoke_agent("test_agent", {})

    @pytest.mark.asyncio
    async def test_invoke_failing_agent(self, failing_agent: Any) -> None:
        manager = AgentManager()
        manager.register_existing_agent(failing_agent)
        await manager.load_agent("failing_agent")
        await manager.activate_agent("failing_agent")
        output = await manager.invoke_agent("failing_agent", {})
        assert output.status == AgentExecutionStatus.FAILURE
        assert output.error is not None

    @pytest.mark.asyncio
    async def test_invoke_slow_agent_times_out(self, slow_agent: Any) -> None:
        manager = AgentManager()
        manager.register_existing_agent(slow_agent)
        await manager.load_agent("slow_agent")
        await manager.activate_agent("slow_agent")
        output = await manager.invoke_agent("slow_agent", {})
        assert output.status == AgentExecutionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_pause_and_resume(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        await manager.load_agent("test_agent")
        await manager.activate_agent("test_agent")
        await manager.pause_agent("test_agent")
        assert manager.get_agent_info("test_agent").status == AgentStatus.PAUSED
        await manager.resume_agent("test_agent")
        assert manager.get_agent_info("test_agent").status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_disable_and_enable(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        await manager.load_agent("test_agent")
        await manager.activate_agent("test_agent")
        await manager.disable_agent("test_agent")
        assert manager.get_agent_info("test_agent").status == AgentStatus.DISABLED
        await manager.enable_agent("test_agent")
        assert manager.get_agent_info("test_agent").status == AgentStatus.REGISTERED

    @pytest.mark.asyncio
    async def test_list_agents(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        for i in range(3):
            metadata = AgentMetadata(agent_id=f"agent_{i}", name=f"Agent {i}", version="1.0")
            manager.register_agent(concrete_agent_class, metadata)
        assert len(manager.list_agents()) == 3

    @pytest.mark.asyncio
    async def test_get_agent_info(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        info = manager.get_agent_info("test_agent")
        assert info.metadata.name == "Test"

    @pytest.mark.asyncio
    async def test_invoke_with_custom_context(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        await manager.load_agent("test_agent")
        await manager.activate_agent("test_agent")
        import logging

        ctx = AgentContext(
            agent_id="test_agent",
            logger=logging.getLogger("test"),
            workflow_id="wf-1",
            trace_id="trace-1",
        )
        output = await manager.invoke_agent("test_agent", {"input": "test"}, context=ctx)
        assert output.status == AgentExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_unregister_agent(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        manager.unregister_agent("test_agent")
        assert not manager.has_agent("test_agent")

    @pytest.mark.asyncio
    async def test_set_event_bus(self, concrete_agent_class: Any) -> None:
        manager = AgentManager()
        events: list[Any] = []

        class FakeBus:
            def emit(self, channel: str, event: Any) -> None:
                events.append(event)

        manager.set_event_bus(FakeBus())
        metadata = AgentMetadata(agent_id="test_agent", name="Test", version="1.0")
        manager.register_agent(concrete_agent_class, metadata)
        assert len(events) > 0
