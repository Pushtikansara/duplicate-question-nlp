from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ares.tools.types import ToolCallContext, ToolMetadata, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class Tool(ABC):
    metadata: ToolMetadata
    context: ToolCallContext | None = None

    @abstractmethod
    async def execute(self, input: dict[str, Any]) -> ToolResult: ...

    async def on_register(self) -> None:  # noqa: B027
        pass

    async def on_load(self) -> None:  # noqa: B027
        pass

    async def on_unload(self) -> None:  # noqa: B027
        pass

    async def on_error(self, error: Exception) -> None:
        logger.error("Tool '%s' error: %s", self.metadata.tool_id, error)

    def create_output(
        self,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        status: ToolStatus = ToolStatus.AVAILABLE,
        processing_time_ms: float = 0.0,
        trace_id: str = "",
        agent_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        return ToolResult(
            tool_id=self.metadata.tool_id,
            status=status,
            result=result or {},
            error=error,
            processing_time_ms=processing_time_ms,
            trace_id=trace_id or (self.context.trace_id if self.context else ""),
            agent_id=agent_id or (self.context.agent_id if self.context else ""),
            metadata=metadata or {},
        )

    @property
    def tool_id(self) -> str:
        return self.metadata.tool_id
