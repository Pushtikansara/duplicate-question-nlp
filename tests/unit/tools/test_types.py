from __future__ import annotations

from ares.tools.types import (
    ToolCallContext,
    ToolMetadata,
    ToolPermission,
    ToolResult,
    ToolSpec,
    ToolStatus,
    ToolType,
)


class TestToolStatus:
    def test_values(self):
        assert list(ToolStatus) == [
            ToolStatus.AVAILABLE,
            ToolStatus.BUSY,
            ToolStatus.ERROR,
            ToolStatus.DISABLED,
        ]


class TestToolType:
    def test_values(self):
        types = list(ToolType)
        assert ToolType.FILE in types
        assert ToolType.PYTHON in types
        assert ToolType.MEMORY in types
        assert ToolType.PLUGIN in types
        assert ToolType.SEARCH in types
        assert ToolType.HTTP in types


class TestToolMetadata:
    def test_defaults(self):
        m = ToolMetadata(tool_id="test", name="Test")
        assert m.tool_id == "test"
        assert m.version == "1.0"
        assert m.tool_type == ToolType.FILE
        assert m.timeout_seconds == 30.0
        assert m.requires_permission is True

    def test_custom(self):
        m = ToolMetadata(
            tool_id="custom",
            name="Custom",
            version="2.0",
            tool_type=ToolType.HTTP,
            timeout_seconds=60.0,
            requires_permission=False,
        )
        assert m.tool_id == "custom"
        assert m.tool_type == ToolType.HTTP
        assert m.timeout_seconds == 60.0


class TestToolResult:
    def test_success(self):
        r = ToolResult(tool_id="t1", status=ToolStatus.AVAILABLE)
        assert r.success is True
        assert r.error is None

    def test_failure(self):
        r = ToolResult(tool_id="t1", status=ToolStatus.ERROR, error="fail")
        assert r.success is False

    def test_defaults(self):
        r = ToolResult(tool_id="t1", status=ToolStatus.AVAILABLE)
        assert r.result == {}
        assert r.processing_time_ms == 0.0


class TestToolSpec:
    def test_defaults(self):
        s = ToolSpec(tool_id="t1", tool_type=ToolType.FILE)
        assert s.tool_id == "t1"
        assert s.input_schema == {}
        assert s.required_permissions == []


class TestToolPermission:
    def test_defaults(self):
        p = ToolPermission(tool_id="t1")
        assert p.allowed_agents == frozenset()
        assert p.max_calls_per_minute == 0


class TestToolCallContext:
    def test_defaults(self):
        c = ToolCallContext()
        assert c.tool_id == ""
        assert c.input == {}
        assert c.timeout_seconds == 30.0
