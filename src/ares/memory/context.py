from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryContext:
    agent_id: str = ""
    workflow_id: str = ""
    trace_id: str = ""
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)
