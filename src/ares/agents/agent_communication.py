from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any

from ares.orchestration.types import AgentMessage as OrchestrationAgentMessage


class MessagePriority(Enum):
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class MessageType(Enum):
    TASK_ASSIGNMENT = auto()
    TASK_RESULT = auto()
    STATUS_UPDATE = auto()
    ERROR_REPORT = auto()
    QUERY = auto()
    RESPONSE = auto()
    COORDINATION = auto()
    DECISION_REQUEST = auto()


@dataclass
class AgentTaskMessage:
    message_id: str = ""
    sender_id: str = ""
    recipient_id: str = ""
    message_type: MessageType = MessageType.TASK_ASSIGNMENT
    content: dict[str, Any] = field(default_factory=dict)
    task_id: str = ""
    trace_id: str = ""
    priority: MessagePriority = MessagePriority.NORMAL
    requires_response: bool = False
    response_to: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.message_id:
            self.message_id = str(uuid.uuid4())

    def to_orchestration_message(self) -> OrchestrationAgentMessage:
        return OrchestrationAgentMessage(
            sender_id=self.sender_id,
            recipient_id=self.recipient_id,
            content={
                "message_id": self.message_id,
                "message_type": self.message_type.name,
                "task_id": self.task_id,
                "content": self.content,
                "priority": self.priority.name,
                "requires_response": self.requires_response,
                "response_to": self.response_to,
                "metadata": self.metadata,
            },
            message_type=self.message_type.name,
            trace_id=self.trace_id,
            timestamp=self.timestamp,
            metadata=self.metadata,
        )

    @staticmethod
    def from_orchestration_message(msg: OrchestrationAgentMessage) -> AgentTaskMessage:
        content_data = msg.content.get("content", msg.content)
        return AgentTaskMessage(
            message_id=msg.content.get("message_id", str(uuid.uuid4())),
            sender_id=msg.sender_id,
            recipient_id=msg.recipient_id,
            message_type=MessageType[msg.content.get("message_type", "TASK_ASSIGNMENT")],
            content=content_data if isinstance(content_data, dict) else {},
            task_id=msg.content.get("task_id", ""),
            trace_id=msg.trace_id,
            priority=MessagePriority[msg.content.get("priority", "NORMAL")],
            requires_response=msg.content.get("requires_response", False),
            response_to=msg.content.get("response_to", ""),
            timestamp=msg.timestamp,
            metadata=msg.metadata,
        )


class MessageRouter:
    def __init__(self) -> None:
        self._pending_responses: dict[str, AgentTaskMessage] = {}

    def route(self, message: AgentTaskMessage, send_fn: Any, shared_context: Any) -> None:
        if message.requires_response:
            self._pending_responses[message.message_id] = message
        send_fn(
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            content=message.to_orchestration_message().content,
            shared_context=shared_context,
            message_type=message.message_type.name,
        )

    def resolve_response(self, response: AgentTaskMessage) -> AgentTaskMessage | None:
        original_id = response.response_to
        return self._pending_responses.pop(original_id, None)

    def has_pending(self, message_id: str) -> bool:
        return message_id in self._pending_responses
