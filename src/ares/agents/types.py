from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class AgentStatus(Enum):
    DISCOVERED = auto()
    PENDING = auto()
    REGISTERED = auto()
    LOADED = auto()
    ACTIVE = auto()
    PAUSED = auto()
    ERROR = auto()
    DISABLED = auto()


class AgentCapability(Enum):
    INTENT_ANALYSIS = auto()
    SEMANTIC_UNDERSTANDING = auto()
    ENTITY_MATCHING = auto()
    RELATION_MATCHING = auto()
    CONFLICT_DETECTION = auto()
    CONFIDENCE_ASSESSMENT = auto()
    EVIDENCE_ANALYSIS = auto()
    CONSENSUS_BUILDING = auto()
    PLANNING = auto()
    MEMORY = auto()
    REASONING = auto()
    REFLECTION = auto()
    PREDICTION = auto()
    PIPELINE = auto()
    MONITORING = auto()
    GATEWAY = auto()


class AgentExecutionStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILURE = auto()
    PARTIAL = auto()
    BLOCKED = auto()
    TIMEOUT = auto()


@dataclass(frozen=True)
class AgentMetadata:
    agent_id: str
    name: str
    version: str
    description: str = ""
    capabilities: frozenset[AgentCapability] = field(default_factory=frozenset)
    tools_required: tuple[str, ...] = ()
    tools_optional: tuple[str, ...] = ()
    timeout_seconds: float = 30.0
    max_retries: int = 3
    tags: tuple[str, ...] = ()
    author: str = ""


@dataclass(frozen=True)
class AgentPermissions:
    agent_id: str
    allowed_tools: tuple[str, ...] = ()
    allowed_agents: tuple[str, ...] = ()
    max_invocations_per_minute: int = 1000
    memory_types_read: tuple[str, ...] = ()
    memory_types_write: tuple[str, ...] = ()


@dataclass
class AgentConfig:
    max_concurrency: int = 10
    default_timeout_seconds: float = 30.0
    max_retries: int = 3
    audit_log_enabled: bool = True
    enable_event_bus: bool = True


@dataclass
class AgentOutput:
    agent_id: str
    status: AgentExecutionStatus
    result: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    evidence: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    trace_id: str = ""
    error: str | None = None


@dataclass
class AgentInfo:
    metadata: AgentMetadata
    status: AgentStatus
    permissions: AgentPermissions
    error_count: int = 0
    total_invocations: int = 0
    last_invocation_time: float = 0.0
    total_processing_time_ms: float = 0.0
