from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, cast

from ares.tools.events import ToolEvent, ToolEventType
from ares.tools.exceptions import ToolExecutionError
from ares.tools.metrics import ToolMetrics
from ares.tools.permissions import ToolPermissionManager
from ares.tools.registry import ToolRegistry
from ares.tools.types import ToolCallContext, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class ToolManager:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        permissions: ToolPermissionManager | None = None,
        metrics: ToolMetrics | None = None,
        event_bus: Any = None,
    ) -> None:
        self._registry = registry or ToolRegistry()
        self._permissions = permissions or ToolPermissionManager(registry=self._registry)
        self._metrics = metrics or ToolMetrics()
        self._event_bus = event_bus

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    @property
    def metrics(self) -> ToolMetrics:
        return self._metrics

    @property
    def permissions(self) -> ToolPermissionManager:
        return self._permissions

    def set_event_bus(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    async def invoke_tool(
        self,
        tool_id: str,
        input: dict[str, Any],
        agent_id: str = "",
        workflow_id: str = "",
        trace_id: str = "",
        timeout_seconds: float | None = None,
        roles: frozenset[str] | None = None,
    ) -> ToolResult:
        tool = self._registry.get(tool_id)
        start = time.time()

        try:
            self._permissions.check_permission(
                tool_id=tool_id,
                agent_id=agent_id,
                roles=roles,
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            self._metrics.record_permission_denied()
            await self._emit_event(
                ToolEventType.PERMISSION_DENIED,
                tool_id=tool_id,
                agent_id=agent_id,
                trace_id=trace_id,
                error=str(e),
            )
            return ToolResult(
                tool_id=tool_id,
                status=ToolStatus.ERROR,
                error=str(e),
                processing_time_ms=elapsed,
                trace_id=trace_id,
                agent_id=agent_id,
            )

        await self._emit_event(
            ToolEventType.INVOKED,
            tool_id=tool_id,
            agent_id=agent_id,
            trace_id=trace_id,
            metadata={"input_keys": list(input.keys())},
        )

        ctx = ToolCallContext(
            tool_id=tool_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            trace_id=trace_id,
            input=input,
            timeout_seconds=timeout_seconds or tool.metadata.timeout_seconds,
        )

        try:
            timeout = timeout_seconds or tool.metadata.timeout_seconds

            async def execute_with_context() -> ToolResult:
                tool.context = ctx
                result = await tool.execute(input)
                return result

            if timeout > 0:
                result = await asyncio.wait_for(
                    execute_with_context(),
                    timeout=timeout,
                )
            else:
                result = await tool.execute(input)

            elapsed = (time.time() - start) * 1000
            result.processing_time_ms = elapsed
            result.trace_id = trace_id or ctx.trace_id
            result.agent_id = agent_id

            success = result.status == ToolStatus.AVAILABLE and result.error is None
            self._metrics.record_invocation(tool_id, success, elapsed)

            event_type = ToolEventType.COMPLETED if success else ToolEventType.FAILED
            await self._emit_event(
                event_type,
                tool_id=tool_id,
                agent_id=agent_id,
                trace_id=trace_id,
                processing_time_ms=elapsed,
                error=result.error,
            )
            return result

        except asyncio.TimeoutError:
            elapsed = (time.time() - start) * 1000
            self._metrics.record_invocation(tool_id, False, elapsed, timed_out=True)
            await self._emit_event(
                ToolEventType.TIMEOUT,
                tool_id=tool_id,
                agent_id=agent_id,
                trace_id=trace_id,
                processing_time_ms=elapsed,
                error=f"Tool '{tool_id}' timed out after {timeout_seconds or tool.metadata.timeout_seconds}s",
            )
            return ToolResult(
                tool_id=tool_id,
                status=ToolStatus.ERROR,
                error=f"Tool '{tool_id}' timed out",
                processing_time_ms=elapsed,
                trace_id=trace_id or ctx.trace_id,
                agent_id=agent_id,
            )

        except ToolExecutionError:
            raise

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            self._metrics.record_invocation(tool_id, False, elapsed)
            await self._emit_event(
                ToolEventType.ERROR,
                tool_id=tool_id,
                agent_id=agent_id,
                trace_id=trace_id,
                processing_time_ms=elapsed,
                error=str(e),
            )
            return ToolResult(
                tool_id=tool_id,
                status=ToolStatus.ERROR,
                error=str(e),
                processing_time_ms=elapsed,
                trace_id=trace_id or ctx.trace_id,
                agent_id=agent_id,
            )

        finally:
            if hasattr(tool, "context"):
                tool.context = None

    async def invoke_tool_with_retry(
        self,
        tool_id: str,
        input: dict[str, Any],
        agent_id: str = "",
        workflow_id: str = "",
        trace_id: str = "",
        timeout_seconds: float | None = None,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        roles: frozenset[str] | None = None,
    ) -> ToolResult:
        from ares.orchestration.retry import RetryManager
        from ares.orchestration.types import RunPolicies

        rm = RetryManager()
        policies = RunPolicies(
            retry_on_failure=True,
            max_retries=max_retries,
            retry_backoff_base=retry_backoff,
        )

        async def attempt() -> ToolResult:
            return await self.invoke_tool(
                tool_id=tool_id,
                input=input,
                agent_id=agent_id,
                workflow_id=workflow_id,
                trace_id=trace_id,
                timeout_seconds=timeout_seconds,
                roles=roles,
            )

        try:
            result: ToolResult = cast(
                ToolResult,
                await rm.execute_with_retry(
                    task_id=f"tool_{tool_id}",
                    func=attempt,
                    policies=policies,
                ),
            )
            return result
        except Exception as e:
            return ToolResult(
                tool_id=tool_id,
                status=ToolStatus.ERROR,
                error=f"Tool '{tool_id}' failed after retries: {e}",
                trace_id=trace_id,
                agent_id=agent_id,
            )

    async def invoke_tool_with_cancellation(
        self,
        tool_id: str,
        input: dict[str, Any],
        cancellation_token: Any,
        agent_id: str = "",
        workflow_id: str = "",
        trace_id: str = "",
        timeout_seconds: float | None = None,
        roles: frozenset[str] | None = None,
    ) -> ToolResult:
        from ares.orchestration.exceptions import RunCancelledError

        async def run_with_check() -> ToolResult:
            check_interval = 0.1
            main_task = asyncio.create_task(
                self.invoke_tool(
                    tool_id=tool_id,
                    input=input,
                    agent_id=agent_id,
                    workflow_id=workflow_id,
                    trace_id=trace_id,
                    timeout_seconds=timeout_seconds,
                    roles=roles,
                )
            )
            while True:
                if cancellation_token.is_cancelled:
                    main_task.cancel()
                    raise RunCancelledError(detail=f"Tool '{tool_id}' cancelled")
                done, _ = await asyncio.wait(
                    [main_task],
                    timeout=check_interval,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if done:
                    return await main_task

        return await run_with_check()

    async def shutdown(self) -> None:
        for tool_id in self._registry.list_all():
            try:
                tool = self._registry.get(tool_id)
                await tool.on_unload()
            except Exception:
                logger.exception("Error unloading tool '%s'", tool_id)
        self._metrics.reset()

    async def _emit_event(
        self,
        event_type: ToolEventType,
        tool_id: str = "",
        agent_id: str = "",
        trace_id: str = "",
        processing_time_ms: float = 0.0,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._event_bus is None:
            return
        try:
            event = ToolEvent(
                event_type=event_type,
                tool_id=tool_id,
                agent_id=agent_id,
                trace_id=trace_id,
                processing_time_ms=processing_time_ms,
                error=error,
                metadata=metadata or {},
            )
            await self._event_bus.emit("tools", tool_event=event)
        except Exception:
            logger.exception("Failed to emit tool event")
