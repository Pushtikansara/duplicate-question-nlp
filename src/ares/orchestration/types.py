from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any

from ares.agents.types import AgentOutput


class OrchestrationStrategyType(Enum):
    SEQUENTIAL = auto()
    PARALLEL = auto()
    HIERARCHICAL = auto()
    DEBATE = auto()
    VOTING = auto()
    PIPELINE = auto()
    SUPERVISOR = auto()


class OrchestrationStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    PARTIAL = auto()
    CANCELLED = auto()
    TIMEOUT = auto()


class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()
    CANCELLED = auto()
    TIMEOUT = auto()


@dataclass(frozen=True)
class AgentMessage:
    sender_id: str
    recipient_id: str
    content: dict[str, Any]
    message_type: str = "generic"
    trace_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SharedAgentContext:
    workflow_id: str = ""
    trace_id: str = ""
    messages: list[AgentMessage] = field(default_factory=list)
    shared_store: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: AgentMessage) -> None:
        self.messages.append(message)

    def get_messages(
        self,
        sender_id: str | None = None,
        recipient_id: str | None = None,
    ) -> list[AgentMessage]:
        result = self.messages
        if sender_id is not None:
            result = [m for m in result if m.sender_id == sender_id]
        if recipient_id is not None:
            result = [m for m in result if m.recipient_id == recipient_id]
        return result

    def set(self, key: str, value: Any) -> None:
        self.shared_store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.shared_store.get(key, default)


@dataclass
class TaskNode:
    id: str
    agent_id: str
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    input: dict[str, Any] = field(default_factory=dict)
    output: AgentOutput | None = None
    error: str | None = None
    processing_time_ms: float = 0.0
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskEdge:
    source_id: str
    target_id: str
    condition: str | None = None


@dataclass
class OrchestrationResult:
    workflow_id: str
    status: OrchestrationStatus
    agent_results: list[AgentOutput]
    task_nodes: dict[str, TaskNode]
    shared_context: SharedAgentContext
    processing_time_ms: float = 0.0
    error: str | None = None
    trace_id: str = ""
    stage_timings: dict[str, float] = field(default_factory=dict)
    strategy: OrchestrationStrategyType | None = None


@dataclass
class RunPolicies:
    timeout_seconds: float = 60.0
    max_concurrency: int = 10
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_backoff_base: float = 1.0
    partial_results_on_timeout: bool = True
    stop_on_first_error: bool = False
    enable_cancellation: bool = True
    max_queue_size: int = 1000


class StageStatus(Enum):
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()
