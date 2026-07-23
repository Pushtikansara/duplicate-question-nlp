from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any

from ares.agents.types import AgentExecutionStatus, AgentStatus


class AgentEventType(Enum):
    DISCOVERED = auto()
    REGISTERED = auto()
    LOADED = auto()
    ACTIVATED = auto()
    PAUSED = auto()
    RESUMED = auto()
    DISABLED = auto()
    ERROR = auto()
    INVOKED = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()


@dataclass
class AgentEvent:
    event_type: AgentEventType
    agent_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    previous_status: AgentStatus | None = None
    new_status: AgentStatus | None = None
    execution_status: AgentExecutionStatus | None = None
    processing_time_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
