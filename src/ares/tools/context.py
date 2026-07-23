from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolContext:
    agent_id: str = ""
    workflow_id: str = ""
    trace_id: str = ""
    input: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 30.0
    metadata: dict[str, Any] = field(default_factory=dict)
    shared_store: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.shared_store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.shared_store.get(key, default)
