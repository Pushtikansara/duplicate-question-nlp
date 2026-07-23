from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ares.agents.context import AgentContext
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput


class Agent(ABC):
    metadata: AgentMetadata
    context: AgentContext | None = None
    _logger: logging.Logger

    def __init__(self) -> None:
        self._logger = logging.getLogger(f"{__name__}.{type(self).__name__}")

    @abstractmethod
    async def execute(self, input: dict[str, Any]) -> AgentOutput: ...

    def get_capabilities(self) -> set[AgentCapability]:
        return set(self.metadata.capabilities)

    def set_context(self, context: AgentContext) -> None:
        self.context = context
        self._logger = context.logger

    async def on_register(self) -> None:  # noqa: B027
        pass

    async def on_load(self) -> None:  # noqa: B027
        pass

    async def on_activate(self) -> None:  # noqa: B027
        pass

    async def on_pause(self) -> None:  # noqa: B027
        pass

    async def on_resume(self) -> None:  # noqa: B027
        pass

    async def on_error(self, exc: Exception) -> None:
        self._logger.error("Agent '%s' error: %s", self.metadata.agent_id, exc)

    async def on_disable(self) -> None:  # noqa: B027
        pass

    def create_output(
        self,
        status: AgentExecutionStatus,
        result: dict[str, Any] | None = None,
        confidence: float = 0.0,
        evidence: list[dict[str, Any]] | None = None,
        warnings: list[str] | None = None,
        processing_time_ms: float = 0.0,
        error: str | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=status,
            result=result or {},
            confidence=confidence,
            evidence=evidence or [],
            warnings=warnings or [],
            processing_time_ms=processing_time_ms,
            trace_id=self.context.trace_id if self.context else "",
            error=error,
        )
