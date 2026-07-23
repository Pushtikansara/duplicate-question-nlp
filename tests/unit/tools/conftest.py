from __future__ import annotations

from typing import Any

import pytest

from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType


class SuccessTool(Tool):
    metadata = ToolMetadata(
        tool_id="success",
        name="Success Tool",
        version="1.0",
        tool_type=ToolType.FILE,
        requires_permission=False,
    )

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        return self.create_output(result={"echo": input})


class FailingTool(Tool):
    metadata = ToolMetadata(
        tool_id="failing",
        name="Failing Tool",
        version="1.0",
        tool_type=ToolType.PYTHON,
        requires_permission=False,
    )

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        return self.create_output(
            error="Intentional failure",
            status=ToolStatus.ERROR,
        )


class SlowTool(Tool):
    metadata = ToolMetadata(
        tool_id="slow",
        name="Slow Tool",
        version="1.0",
        tool_type=ToolType.SEARCH,
        timeout_seconds=0.1,
        requires_permission=False,
    )

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        import asyncio

        await asyncio.sleep(10)
        return self.create_output(result={"done": "too late"})


@pytest.fixture
def success_tool() -> SuccessTool:
    return SuccessTool()


@pytest.fixture
def failing_tool() -> FailingTool:
    return FailingTool()


@pytest.fixture
def slow_tool() -> SlowTool:
    return SlowTool()
