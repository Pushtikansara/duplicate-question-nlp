from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ToolStatus(Enum):
    AVAILABLE = auto()
    BUSY = auto()
    ERROR = auto()
    DISABLED = auto()


class ToolType(Enum):
    FILE = auto()
    PYTHON = auto()
    MEMORY = auto()
    PLUGIN = auto()
    SEARCH = auto()
    HTTP = auto()


@dataclass(frozen=True)
class ToolMetadata:
    tool_id: str
    name: str
    version: str = "1.0"
    description: str = ""
    tool_type: ToolType = ToolType.FILE
    timeout_seconds: float = 30.0
    max_retries: int = 0
    requires_permission: bool = True
    author: str = "system"
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    tool_type: ToolType
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ToolPermission:
    tool_id: str
    allowed_agents: frozenset[str] = field(default_factory=frozenset)
    allowed_roles: frozenset[str] = field(default_factory=frozenset)
    max_calls_per_minute: int = 0
    require_approval: bool = False


@dataclass
class ToolResult:
    tool_id: str
    status: ToolStatus
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    processing_time_ms: float = 0.0
    trace_id: str = ""
    agent_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == ToolStatus.AVAILABLE and self.error is None


@dataclass
class ToolCallContext:
    tool_id: str = ""
    agent_id: str = ""
    workflow_id: str = ""
    trace_id: str = ""
    input: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 30.0
    metadata: dict[str, Any] = field(default_factory=dict)
