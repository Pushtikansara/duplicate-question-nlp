from __future__ import annotations

from typing import Any

from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType


class TestTool:
    def test_tool_id_property(self, success_tool):
        assert success_tool.tool_id == "success"

    def test_create_output(self, success_tool):
        result = success_tool.create_output(
            result={"key": "value"},
            processing_time_ms=10.0,
        )
        assert result.tool_id == "success"
        assert result.result == {"key": "value"}
        assert result.processing_time_ms == 10.0
        assert result.status == ToolStatus.AVAILABLE
        assert result.error is None

    def test_create_output_with_error(self, success_tool):
        result = success_tool.create_output(
            error="Something failed",
            status=ToolStatus.ERROR,
        )
        assert result.status == ToolStatus.ERROR
        assert result.error == "Something failed"

    def test_on_register_hook(self):
        class TestTool(Tool):
            metadata = ToolMetadata(
                tool_id="test",
                name="Test",
                tool_type=ToolType.FILE,
            )
            registered = False

            async def on_register(self) -> None:
                self.registered = True

            async def execute(self, input: dict[str, Any]) -> ToolResult:
                return self.create_output(result={})

        tool = TestTool()
        assert hasattr(tool, "on_register")
        assert hasattr(tool, "on_load")
        assert hasattr(tool, "on_unload")
        assert hasattr(tool, "on_error")

    def test_successful_execution(self, success_tool):
        import asyncio

        result = asyncio.run(success_tool.execute({"test": "data"}))
        assert result.tool_id == "success"
        assert result.error is None
        assert result.result == {"echo": {"test": "data"}}

    def test_failing_execution(self, failing_tool):
        import asyncio

        result = asyncio.run(failing_tool.execute({}))
        assert result.tool_id == "failing"
        assert result.error == "Intentional failure"
        assert result.status == ToolStatus.ERROR
