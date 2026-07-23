from __future__ import annotations

from typing import Any

import pytest

from ares.agents.exceptions import AgentStateError
from ares.agents.lifecycle import AgentLifecycleManager
from ares.agents.registry import AgentRegistry
from ares.agents.types import AgentStatus


class TestAgentLifecycleManager:
    @pytest.fixture
    def manager(self, concrete_agent: Any) -> AgentLifecycleManager:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        return AgentLifecycleManager(registry)

    @pytest.mark.asyncio
    async def test_load_transition(self, manager: AgentLifecycleManager) -> None:
        await manager.load("test_agent")
        info = manager._registry.get_info("test_agent")
        assert info.status == AgentStatus.LOADED

    @pytest.mark.asyncio
    async def test_activate_transition(self, manager: AgentLifecycleManager) -> None:
        await manager.load("test_agent")
        await manager.activate("test_agent")
        info = manager._registry.get_info("test_agent")
        assert info.status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_pause_resume_cycle(self, manager: AgentLifecycleManager) -> None:
        await manager.load("test_agent")
        await manager.activate("test_agent")
        await manager.pause("test_agent")
        info = manager._registry.get_info("test_agent")
        assert info.status == AgentStatus.PAUSED
        await manager.resume("test_agent")
        info = manager._registry.get_info("test_agent")
        assert info.status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_disable_from_active(self, manager: AgentLifecycleManager) -> None:
        await manager.load("test_agent")
        await manager.activate("test_agent")
        await manager.disable("test_agent")
        info = manager._registry.get_info("test_agent")
        assert info.status == AgentStatus.DISABLED

    @pytest.mark.asyncio
    async def test_enable_from_disabled(self, manager: AgentLifecycleManager) -> None:
        await manager.load("test_agent")
        await manager.activate("test_agent")
        await manager.disable("test_agent")
        await manager.enable("test_agent")
        info = manager._registry.get_info("test_agent")
        assert info.status == AgentStatus.REGISTERED

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self, manager: AgentLifecycleManager) -> None:
        info = manager._registry.get_info("test_agent")
        assert info.status == AgentStatus.REGISTERED
        with pytest.raises(AgentStateError):
            await manager.pause("test_agent")

    @pytest.mark.asyncio
    async def test_error_handling(self, manager: AgentLifecycleManager, failing_agent: Any) -> None:
        manager._registry.register(failing_agent)
        await manager.load("failing_agent")
        await manager.activate("failing_agent")
        exc = ValueError("test error")
        await manager.handle_error("failing_agent", exc)
        info = manager._registry.get_info("failing_agent")
        assert info.status == AgentStatus.ERROR

    @pytest.mark.asyncio
    async def test_retry_from_error(self, manager: AgentLifecycleManager) -> None:
        await manager.load("test_agent")
        await manager.activate("test_agent")
        await manager.handle_error("test_agent", ValueError("err"))
        await manager.retry("test_agent")
        info = manager._registry.get_info("test_agent")
        assert info.status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_retry_from_non_error_raises(self, manager: AgentLifecycleManager) -> None:
        await manager.load("test_agent")
        with pytest.raises(AgentStateError):
            await manager.retry("test_agent")

    @pytest.mark.asyncio
    async def test_retry_exceeds_max_raises(self, manager: AgentLifecycleManager) -> None:
        await manager.load("test_agent")
        await manager.activate("test_agent")
        for _ in range(3):
            await manager.handle_error("test_agent", ValueError("err"))
            info = manager._registry.get_info("test_agent")
            assert info.status == AgentStatus.ERROR
            await manager.retry("test_agent")
            info = manager._registry.get_info("test_agent")
            assert info.status == AgentStatus.ACTIVE
        await manager.handle_error("test_agent", ValueError("err"))
        with pytest.raises(AgentStateError):
            await manager.retry("test_agent")
