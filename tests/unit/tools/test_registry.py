from __future__ import annotations

import pytest

from ares.tools.exceptions import ToolNotFoundError, ToolRegistrationError
from ares.tools.registry import ToolRegistry
from ares.tools.types import ToolPermission, ToolSpec, ToolStatus, ToolType


class ConcreteTool:
    pass


class TestToolRegistry:
    def test_register_and_get(self, success_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        assert reg.has("success")
        assert reg.get("success") is success_tool
        assert reg.count() == 1

    def test_register_duplicate(self, success_tool, failing_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        with pytest.raises(ToolRegistrationError):
            reg.register(success_tool)

    def test_get_not_found(self):
        reg = ToolRegistry()
        with pytest.raises(ToolNotFoundError):
            reg.get("nonexistent")

    def test_unregister(self, success_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        reg.unregister("success")
        assert not reg.has("success")
        assert reg.count() == 0

    def test_register_with_metadata_and_spec(self, success_tool):
        reg = ToolRegistry()
        spec = ToolSpec(tool_id="success", tool_type=ToolType.FILE, description="Test")
        perm = ToolPermission(tool_id="success", allowed_agents=frozenset({"agent_1"}))
        reg.register(success_tool, spec=spec, permission=perm)
        assert reg.get_spec("success") is spec
        assert reg.get_permission("success") is perm

    def test_status_management(self, success_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        assert reg.get_status("success") == ToolStatus.AVAILABLE
        reg.set_status("success", ToolStatus.DISABLED)
        assert reg.get_status("success") == ToolStatus.DISABLED

    def test_list_all(self, success_tool, failing_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        reg.register(failing_tool)
        tools = reg.list_all()
        assert len(tools) == 2
        assert "success" in tools
        assert "failing" in tools

    def test_list_by_type(self, success_tool, failing_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        reg.register(failing_tool)
        file_tools = reg.list_by_type(ToolType.FILE)
        assert "success" in file_tools
        python_tools = reg.list_by_type(ToolType.PYTHON)
        assert "failing" in python_tools

    def test_list_available(self, success_tool, failing_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        reg.register(failing_tool)
        reg.set_status("failing", ToolStatus.DISABLED)
        available = reg.list_available()
        assert "success" in available
        assert "failing" not in available

    def test_clear(self, success_tool, failing_tool):
        reg = ToolRegistry()
        reg.register(success_tool)
        reg.register(failing_tool)
        reg.clear()
        assert reg.count() == 0
        assert reg.list_all() == []
