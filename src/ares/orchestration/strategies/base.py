from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ares.agents.base import Agent
from ares.orchestration.types import (
    AgentMessage,
    OrchestrationResult,
    OrchestrationStrategyType,
    RunPolicies,
    SharedAgentContext,
)


class OrchestrationStrategy(ABC):
    @property
    @abstractmethod
    def strategy_type(self) -> OrchestrationStrategyType: ...

    @abstractmethod
    async def execute(
        self,
        agents: list[Agent],
        input: dict[str, Any],
        shared_context: SharedAgentContext,
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult: ...

    def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        content: dict[str, Any],
        shared_context: SharedAgentContext,
        message_type: str = "generic",
    ) -> None:
        shared_context.add_message(
            AgentMessage(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                message_type=message_type,
                trace_id=shared_context.trace_id,
            )
        )
