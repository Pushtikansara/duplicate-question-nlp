from __future__ import annotations

from typing import Any

import pytest

from ares.agents.exceptions import AgentNotFoundError, AgentRegistrationError
from ares.agents.registry import AgentRegistry
from ares.agents.types import AgentPermissions, AgentStatus


class TestAgentRegistry:
    def test_register_agent(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        agent_id = registry.register(concrete_agent)
        assert agent_id == "test_agent"
        assert registry.has("test_agent")

    def test_register_duplicate_raises(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        with pytest.raises(AgentRegistrationError):
            registry.register(concrete_agent)

    def test_get_agent(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        agent = registry.get("test_agent")
        assert agent is concrete_agent

    def test_get_nonexistent_raises(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(AgentNotFoundError):
            registry.get("nonexistent")

    def test_unregister_agent(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        registry.unregister("test_agent")
        assert not registry.has("test_agent")

    def test_unregister_nonexistent_raises(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(AgentNotFoundError):
            registry.unregister("nonexistent")

    def test_get_info(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        info = registry.get_info("test_agent")
        assert info.metadata.agent_id == "test_agent"
        assert info.status == AgentStatus.REGISTERED

    def test_get_info_nonexistent_raises(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(AgentNotFoundError):
            registry.get_info("nonexistent")

    def test_list_all(self, concrete_agent: Any, failing_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        registry.register(failing_agent)
        agents = registry.list_all()
        assert len(agents) == 2

    def test_list_by_status(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        agents = registry.list_by_status(AgentStatus.REGISTERED)
        assert len(agents) == 1
        agents = registry.list_by_status(AgentStatus.ACTIVE)
        assert len(agents) == 0

    def test_count(self, concrete_agent: Any, failing_agent: Any) -> None:
        registry = AgentRegistry()
        assert registry.count() == 0
        registry.register(concrete_agent)
        assert registry.count() == 1
        registry.register(failing_agent)
        assert registry.count() == 2

    def test_update_status(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        registry.update_status("test_agent", AgentStatus.ACTIVE)
        info = registry.get_info("test_agent")
        assert info.status == AgentStatus.ACTIVE

    def test_update_status_nonexistent_raises(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(AgentNotFoundError):
            registry.update_status("nonexistent", AgentStatus.ACTIVE)

    def test_record_invocation(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        registry.record_invocation("test_agent", 10.0)
        info = registry.get_info("test_agent")
        assert info.total_invocations == 1
        assert info.total_processing_time_ms == 10.0

    def test_record_invocation_with_error(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        registry.record_invocation("test_agent", 5.0, error=True)
        info = registry.get_info("test_agent")
        assert info.error_count == 1
        assert info.total_invocations == 1

    def test_record_invocation_nonexistent_no_error(self) -> None:
        registry = AgentRegistry()
        registry.record_invocation("nonexistent", 10.0)

    def test_get_permissions(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        perms = AgentPermissions(agent_id="test_agent", allowed_tools=("predict",))
        registry.register(concrete_agent, perms)
        result = registry.get_permissions("test_agent")
        assert result.allowed_tools == ("predict",)

    def test_clear(self, concrete_agent: Any) -> None:
        registry = AgentRegistry()
        registry.register(concrete_agent)
        registry.clear()
        assert registry.count() == 0
