from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    REASONING = "reasoning"
    DEBATE = "debate"
    PERFORMANCE = "performance"


class MemoryStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class MemoryLineage:
    created_by: str
    created_at: datetime
    parent_ids: list[str] = field(default_factory=list)
    module_chain: list[str] = field(default_factory=list)
    reasoning_id: str | None = None
    debate_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "parent_ids": list(self.parent_ids),
            "module_chain": list(self.module_chain),
            "reasoning_id": self.reasoning_id,
            "debate_id": self.debate_id,
        }


@dataclass
class MemoryEntry:
    memory_id: str
    memory_type: MemoryType
    version: int
    timestamp: datetime
    source_module: str
    quality_score: float
    confidence: float
    lineage: MemoryLineage
    tags: list[str]
    metadata: dict[str, Any]
    content: dict[str, Any]
    embedding: list[float] | None = None
    expires_at: datetime | None = None
    status: MemoryStatus = MemoryStatus.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "source_module": self.source_module,
            "quality_score": self.quality_score,
            "confidence": self.confidence,
            "lineage": self.lineage.to_dict(),
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "content": dict(self.content),
            "embedding": list(self.embedding) if self.embedding is not None else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at is not None else None,
            "status": self.status.value,
        }


@dataclass
class MemoryQuery:
    query_type: str = "exact"
    memory_types: list[MemoryType] | None = None
    tags: list[str] | None = None
    source_modules: list[str] | None = None
    min_confidence: float = 0.0
    min_quality: float = 0.0
    text: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    limit: int = 100
    offset: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_type": self.query_type,
            "memory_types": [t.value for t in self.memory_types] if self.memory_types is not None else None,
            "tags": list(self.tags) if self.tags is not None else None,
            "source_modules": list(self.source_modules) if self.source_modules is not None else None,
            "min_confidence": self.min_confidence,
            "min_quality": self.min_quality,
            "text": self.text,
            "filters": dict(self.filters),
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass
class MemoryResult:
    entries: list[MemoryEntry]
    total_count: int
    query_time_ms: float
    query: MemoryQuery

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "total_count": self.total_count,
            "query_time_ms": self.query_time_ms,
            "query": self.query.to_dict(),
        }


@dataclass
class MemoryStatistics:
    total_entries: int
    total_by_type: dict[str, int]
    total_size_bytes: int
    avg_quality: float
    avg_confidence: float
    oldest_entry: datetime | None = None
    newest_entry: datetime | None = None
    version_count: int = 0
    deleted_count: int = 0


class MemoryStore(ABC):
    @abstractmethod
    def store(self, entry: MemoryEntry) -> str: ...

    @abstractmethod
    def retrieve(self, memory_id: str) -> MemoryEntry | None: ...

    @abstractmethod
    def update(self, entry: MemoryEntry) -> str: ...

    @abstractmethod
    def delete(self, memory_id: str, soft: bool = True) -> bool: ...

    @abstractmethod
    def list_by_type(
        self, memory_type: MemoryType, limit: int = 100, offset: int = 0
    ) -> tuple[list[MemoryEntry], int]: ...

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> tuple[list[MemoryEntry], int]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clear(self) -> None: ...


class MemoryIndex(ABC):
    @abstractmethod
    def index_entry(self, entry: MemoryEntry) -> None: ...

    @abstractmethod
    def search(self, query: MemoryQuery, store: MemoryStore) -> list[MemoryEntry]: ...

    @abstractmethod
    def remove(self, memory_id: str) -> None: ...

    @abstractmethod
    def rebuild(self, entries: list[MemoryEntry]) -> None: ...


class RetrievalEngine(ABC):
    @abstractmethod
    def retrieve(
        self,
        query: MemoryQuery,
        store: MemoryStore,
        index: MemoryIndex | None = None,
        ranker: RetrievalRanker | None = None,
    ) -> MemoryResult: ...


class RetrievalRanker(ABC):
    @abstractmethod
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]: ...


class MemoryConsolidator(ABC):
    @abstractmethod
    def consolidate(self, entries: list[MemoryEntry], store: MemoryStore) -> list[str]: ...

    @abstractmethod
    def find_duplicates(self, entries: list[MemoryEntry]) -> list[list[MemoryEntry]]: ...


class MemoryVersioning(ABC):
    @abstractmethod
    def create_version(self, entry: MemoryEntry, parent_id: str | None = None) -> MemoryEntry: ...

    @abstractmethod
    def get_version_history(self, memory_id: str, store: MemoryStore) -> list[MemoryEntry]: ...


class ForgettingEngine(ABC):
    @abstractmethod
    def apply_policies(self, store: MemoryStore) -> list[str]: ...

    @abstractmethod
    def calculate_age_score(self, entry: MemoryEntry) -> float: ...


class MemoryAudit(ABC):
    @abstractmethod
    def log_access(self, memory_id: str, action: str, module: str, details: str = "") -> None: ...

    @abstractmethod
    def get_history(self, memory_id: str) -> list[dict]: ...

    @abstractmethod
    def get_recent_actions(self, limit: int = 100) -> list[dict]: ...


class MemoryValidator(ABC):
    @abstractmethod
    def validate(self, entry: MemoryEntry) -> tuple[bool, list[str]]: ...

    @abstractmethod
    def validate_batch(self, entries: list[MemoryEntry]) -> list[tuple[bool, list[str]]]: ...


class MemoryPlugin(ABC):
    @abstractmethod
    def process_before_store(self, entry: MemoryEntry) -> MemoryEntry: ...

    @abstractmethod
    def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None: ...
