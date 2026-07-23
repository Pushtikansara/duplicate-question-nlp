from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ares.api.config import Settings


@dataclass
class AgentContext:
    agent_id: str
    logger: logging.Logger
    config: Settings | None = None
    event_bus: Any = None
    workflow_id: str = ""
    trace_id: str = ""
    in_memory_store: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
