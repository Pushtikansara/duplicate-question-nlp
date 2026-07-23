from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any

from ares.tools.types import ToolStatus


class ToolEventType(Enum):
    REGISTERED = auto()
    UNREGISTERED = auto()
    INVOKED = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    ERROR = auto()
    PERMISSION_DENIED = auto()


@dataclass
class ToolEvent:
    event_type: ToolEventType
    tool_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: str = ""
    previous_status: ToolStatus | None = None
    new_status: ToolStatus | None = None
    processing_time_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
