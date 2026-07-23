from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanningContext:
    workflow_id: str = ""
    trace_id: str = ""
    agent_ids: list[str] = field(default_factory=list)
    tool_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    policies: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)
