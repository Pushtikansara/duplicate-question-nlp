from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any

from ares.orchestration.types import OrchestrationStatus, TaskStatus


class OrchestrationEventType(Enum):
    ORCHESTRATION_STARTED = auto()
    ORCHESTRATION_COMPLETED = auto()
    ORCHESTRATION_FAILED = auto()
    ORCHESTRATION_CANCELLED = auto()
    ORCHESTRATION_TIMEOUT = auto()
    TASK_STARTED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()
    TASK_SKIPPED = auto()
    TASK_RETRYING = auto()
    STRATEGY_SELECTED = auto()
    STRATEGY_COMPLETED = auto()
    AGENT_MESSAGE_SENT = auto()
    RUN_POLICY_APPLIED = auto()


@dataclass
class OrchestrationEvent:
    event_type: OrchestrationEventType
    workflow_id: str = ""
    task_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    previous_status: OrchestrationStatus | TaskStatus | None = None
    new_status: OrchestrationStatus | TaskStatus | None = None
    error: str | None = None
    processing_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
