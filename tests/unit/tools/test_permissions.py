from __future__ import annotations

import pytest

from ares.tools.exceptions import ToolDisabledError, ToolPermissionError
from ares.tools.permissions import ToolPermissionManager
from ares.tools.registry import ToolRegistry
from ares.tools.types import ToolPermission, ToolStatus


class ConcreteTool:
    pass


class TestToolPermissionManager:
    @pytest.fixture
    def registry(self, success_tool, failing_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        reg.register(failing_tool)
        perm = ToolPermission(
            tool_id="success",
            allowed_agents=frozenset({"agent_1", "agent_2"}),
            allowed_roles=frozenset({"admin", "editor"}),
            max_calls_per_minute=5,
        )
        reg._permissions["success"] = perm
        return reg

    def test_allowed_agent(self, registry):
        pm = ToolPermissionManager(registry)
        pm.check_permission("success", agent_id="agent_1")

    def test_denied_agent(self, registry):
        pm = ToolPermissionManager(registry)
        with pytest.raises(ToolPermissionError):
            pm.check_permission("success", agent_id="agent_3")

    def test_allowed_role(self, registry):
        pm = ToolPermissionManager(registry)
        pm.check_permission("success", roles=frozenset({"admin"}))

    def test_denied_role(self, registry):
        pm = ToolPermissionManager(registry)
        with pytest.raises(ToolPermissionError):
            pm.check_permission("success", roles=frozenset({"viewer"}))

    def test_disabled_tool(self, registry):
        registry.set_status("success", ToolStatus.DISABLED)
        pm = ToolPermissionManager(registry)
        with pytest.raises(ToolDisabledError):
            pm.check_permission("success")

    def test_no_permission_config(self, success_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        pm = ToolPermissionManager(reg)
        pm.check_permission("success", agent_id="anyone")

    def test_rate_limit(self, registry):
        pm = ToolPermissionManager(registry)
        for _ in range(5):
            pm.check_permission("success", agent_id="agent_1")
        with pytest.raises(ToolPermissionError):
            pm.check_permission("success", agent_id="agent_1")

    def test_reset_calls(self, registry):
        pm = ToolPermissionManager(registry)
        for _ in range(5):
            pm.check_permission("success", agent_id="agent_1")
        pm.reset_calls()
        pm.check_permission("success", agent_id="agent_1")
