from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class MemoryTier(Enum):
    WORKING = auto()
    SHORT_TERM = auto()
    LONG_TERM = auto()


class MemoryDomain(Enum):
    EPISODIC = auto()
    SEMANTIC = auto()
    REFLECTION = auto()


@dataclass
class MemoryValue:
    key: str
    value: Any
    tier: MemoryTier = MemoryTier.WORKING
    domain: MemoryDomain = MemoryDomain.SEMANTIC
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""
    session_id: str = ""
    score: float = 1.0
    access_count: int = 0

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds


@dataclass
class MemoryEntry:
    memory_id: str
    key: str
    value: Any
    tier: MemoryTier
    domain: MemoryDomain
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""
    session_id: str = ""
    score: float = 1.0
    access_count: int = 0
    version: int = 1
    tags: list[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds


@dataclass
class MemoryQuery:
    key: str = ""
    tier: MemoryTier | None = None
    domain: MemoryDomain | None = None
    agent_id: str = ""
    session_id: str = ""
    tags: list[str] = field(default_factory=list)
    min_score: float = 0.0
    limit: int = 100
    offset: int = 0
    include_expired: bool = False


@dataclass
class MemoryResult:
    entries: list[MemoryEntry] = field(default_factory=list)
    total_count: int = 0
    query_time_ms: float = 0.0


@dataclass
class MemoryStats:
    total_entries: int = 0
    entries_by_tier: dict[str, int] = field(default_factory=dict)
    entries_by_domain: dict[str, int] = field(default_factory=dict)
    total_size_bytes: int = 0
    oldest_entry: str = ""
    newest_entry: str = ""
    session_count: int = 0
    eviction_count: int = 0
