from __future__ import annotations

from typing import Any

import pytest

from ares.orchestration.cancellation import CancellationToken
from ares.tools.exceptions import ToolNotFoundError
from ares.tools.manager import ToolManager
from ares.tools.registry import ToolRegistry
from ares.tools.types import (
    ToolPermission,
    ToolStatus,
)


class TestToolManager:
    async def test_invoke_success(self, success_tool):
        manager = ToolManager()
        manager.registry.register(success_tool)
        result = await manager.invoke_tool("success", {"key": "value"})
        assert result.tool_id == "success"
        assert result.error is None
        assert result.result == {"echo": {"key": "value"}}

    async def test_invoke_failure(self, failing_tool):
        manager = ToolManager()
        manager.registry.register(failing_tool)
        result = await manager.invoke_tool("failing", {})
        assert result.tool_id == "failing"
        assert result.error == "Intentional failure"
        assert result.status == ToolStatus.ERROR

    async def test_invoke_not_found(self):
        manager = ToolManager()
        with pytest.raises(ToolNotFoundError):
            await manager.invoke_tool("nonexistent", {})

    async def test_invoke_with_agent_and_trace(self, success_tool):
        manager = ToolManager()
        manager.registry.register(success_tool)
        result = await manager.invoke_tool(
            "success",
            {},
            agent_id="agent_1",
            workflow_id="wf_1",
            trace_id="trace_1",
        )
        assert result.trace_id == "trace_1"

    async def test_invoke_with_retry(self, success_tool):
        manager = ToolManager()
        manager.registry.register(success_tool)
        result = await manager.invoke_tool_with_retry(
            "success",
            {},
            max_retries=2,
        )
        assert result.error is None
        assert result.status == ToolStatus.AVAILABLE

    async def test_invoke_with_cancellation(self, success_tool):
        manager = ToolManager()
        manager.registry.register(success_tool)
        token = CancellationToken()
        result = await manager.invoke_tool_with_cancellation(
            "success",
            {},
            cancellation_token=token,
        )
        assert result.error is None

    async def test_invoke_cancellation_cancels(self, slow_tool):
        manager = ToolManager()
        manager.registry.register(slow_tool)
        token = CancellationToken()

        async def cancel_after_delay():
            import asyncio

            await asyncio.sleep(0.2)
            token.cancel("Test cancellation")

        import asyncio

        cancel_task = asyncio.create_task(cancel_after_delay())
        result = await manager.invoke_tool_with_cancellation(
            "slow",
            {},
            cancellation_token=token,
        )
        await cancel_task
        assert result.status == ToolStatus.ERROR or "cancelled" in str(result.error).lower()

    async def test_metrics_tracked(self, success_tool, failing_tool):
        manager = ToolManager()
        manager.registry.register(success_tool)
        manager.registry.register(failing_tool)
        await manager.invoke_tool("success", {})
        await manager.invoke_tool("failing", {})
        assert manager.metrics.total_invocations == 2
        assert manager.metrics.completed_invocations == 1
        assert manager.metrics.failed_invocations == 1

    async def test_event_bus_emits_events(self, success_tool):
        events = []

        class MockBus:
            async def emit(self, channel: str, **kwargs: Any) -> None:
                events.append((channel, kwargs.get("tool_event")))

        manager = ToolManager(event_bus=MockBus())
        manager.registry.register(success_tool)
        await manager.invoke_tool("success", {})
        assert len(events) > 0
        channels = [e[0] for e in events]
        assert "tools" in channels

    async def test_registry_property(self, success_tool):
        manager = ToolManager()
        assert isinstance(manager.registry, ToolRegistry)
        manager.registry.register(success_tool)
        assert manager.registry.has("success")

    async def test_shutdown(self, success_tool, failing_tool):
        manager = ToolManager()
        manager.registry.register(success_tool)
        manager.registry.register(failing_tool)
        await manager.invoke_tool("success", {})
        await manager.shutdown()
        assert manager.metrics.total_invocations == 0

    async def test_permission_enforced(self, success_tool):
        manager = ToolManager()
        perm = ToolPermission(
            tool_id="success",
            allowed_agents=frozenset({"allowed_agent"}),
        )
        manager.registry.register(success_tool)
        manager.registry._permissions["success"] = perm

        result = await manager.invoke_tool(
            "success",
            {},
            agent_id="blocked_agent",
        )
        assert result.status == ToolStatus.ERROR
        assert "permission" in str(result.error).lower() or "not allowed" in str(result.error).lower()

    async def test_timeout_returns_error(self, slow_tool):
        manager = ToolManager()
        manager.registry.register(slow_tool)
        result = await manager.invoke_tool(
            "slow",
            {},
            timeout_seconds=0.3,
        )
        assert result.status == ToolStatus.ERROR
        assert "timed out" in str(result.error).lower()
