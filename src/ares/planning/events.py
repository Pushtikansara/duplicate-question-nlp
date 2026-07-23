from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any

from ares.planning.types import PlanNodeStatus, PlanStatus


class PlanningEventType(Enum):
    GOAL_CREATED = auto()
    GOAL_DECOMPOSED = auto()
    PLAN_CREATED = auto()
    PLAN_VALIDATED = auto()
    PLAN_OPTIMIZED = auto()
    PLAN_STARTED = auto()
    PLAN_PAUSED = auto()
    PLAN_RESUMED = auto()
    PLAN_COMPLETED = auto()
    PLAN_FAILED = auto()
    PLAN_CANCELLED = auto()
    PLAN_NODE_STARTED = auto()
    PLAN_NODE_COMPLETED = auto()
    PLAN_NODE_FAILED = auto()
    PLAN_NODE_RETRYING = auto()
    PLAN_REPLANNING = auto()
    PLAN_REPLANNED = auto()


@dataclass
class PlanningEvent:
    event_type: PlanningEventType
    plan_id: str = ""
    goal_id: str = ""
    node_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    previous_status: PlanStatus | PlanNodeStatus | None = None
    new_status: PlanStatus | PlanNodeStatus | None = None
    error: str | None = None
    processing_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
