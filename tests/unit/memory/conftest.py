from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pytest

from duplicate_question_app._memory.interfaces import (
    ForgettingEngine,
    MemoryAudit,
    MemoryConsolidator,
    MemoryEntry,
    MemoryIndex,
    MemoryLineage,
    MemoryPlugin,
    MemoryQuery,
    MemoryResult,
    MemoryStatistics,
    MemoryStatus,
    MemoryStore,
    MemoryType,
    MemoryValidator,
    MemoryVersioning,
    RetrievalEngine,
    RetrievalRanker,
)
from duplicate_question_app._memory.memory_configuration import MemoryConfig
from duplicate_question_app._memory.memory_index import DefaultMemoryIndex
from duplicate_question_app._memory.memory_result import ConsolidationResult, DeleteResult, StoreResult
from duplicate_question_app._memory.memory_statistics import DefaultMemoryStatistics
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore
from duplicate_question_app._memory.memory_validator import DefaultMemoryValidator

# ---------------------------------------------------------------------------
# Inline implementations for modules that do not yet exist as standalone files
# ---------------------------------------------------------------------------

# -- memory_types.py --


def create_episodic_memory(**overrides: Any) -> MemoryEntry:
    base: dict[str, Any] = {
        "memory_id": "",
        "memory_type": MemoryType.EPISODIC,
        "version": 1,
        "timestamp": datetime.now(),
        "source_module": "pipeline",
        "quality_score": 0.8,
        "confidence": 0.9,
        "lineage": MemoryLineage(
            created_by="test",
            created_at=datetime.now(),
            parent_ids=[],
            module_chain=["pipeline"],
            reasoning_id=None,
            debate_id=None,
        ),
        "tags": ["episodic", "test"],
        "metadata": {},
        "content": {
            "question_a": "What is Python?",
            "question_b": "What is Python language?",
            "pipeline_used": "cross_encoder",
            "decision": "duplicate",
        },
        "embedding": None,
        "expires_at": None,
        "status": MemoryStatus.ACTIVE,
    }
    base.update(overrides)
    entry = MemoryEntry(**base)
    if not entry.memory_id:
        entry.memory_id = str(uuid.uuid4())
    return entry


def create_semantic_memory(**overrides: Any) -> MemoryEntry:
    base: dict[str, Any] = {
        "memory_id": "",
        "memory_type": MemoryType.SEMANTIC,
        "version": 1,
        "timestamp": datetime.now(),
        "source_module": "semantic_intelligence",
        "quality_score": 0.85,
        "confidence": 0.88,
        "lineage": MemoryLineage(
            created_by="test",
            created_at=datetime.now(),
            parent_ids=[],
            module_chain=["semantic_intelligence"],
            reasoning_id=None,
            debate_id=None,
        ),
        "tags": ["semantic", "concept"],
        "metadata": {"domain": "general"},
        "content": {
            "concepts": ["python", "programming"],
            "entities": [{"name": "Python", "type": "language"}],
            "relations": [{"source": "Python", "target": "programming", "relation": "is_a"}],
            "intent_pattern": "definition",
        },
        "embedding": [0.1, 0.2, 0.3],
        "expires_at": None,
        "status": MemoryStatus.ACTIVE,
    }
    base.update(overrides)
    entry = MemoryEntry(**base)
    if not entry.memory_id:
        entry.memory_id = str(uuid.uuid4())
    return entry


def create_reasoning_memory(**overrides: Any) -> MemoryEntry:
    base: dict[str, Any] = {
        "memory_id": "",
        "memory_type": MemoryType.REASONING,
        "version": 1,
        "timestamp": datetime.now(),
        "source_module": "reasoning",
        "quality_score": 0.75,
        "confidence": 0.8,
        "lineage": MemoryLineage(
            created_by="test",
            created_at=datetime.now(),
            parent_ids=[],
            module_chain=["reasoning"],
            reasoning_id="reason-001",
            debate_id=None,
        ),
        "tags": ["reasoning", "inference"],
        "metadata": {"reasoning_depth": 3},
        "content": {
            "reasoning_graph": {"nodes": [], "edges": []},
            "premises": ["Python is a language"],
            "evidence_chains": [{"premise": "Python is a language", "confidence": 0.9}],
            "hypotheses": ["Questions are similar"],
            "confidence_chain": {"final": 0.85, "steps": []},
            "reasoning_trace": ["step1", "step2"],
        },
        "embedding": None,
        "expires_at": None,
        "status": MemoryStatus.ACTIVE,
    }
    base.update(overrides)
    entry = MemoryEntry(**base)
    if not entry.memory_id:
        entry.memory_id = str(uuid.uuid4())
    return entry


def create_debate_memory(**overrides: Any) -> MemoryEntry:
    base: dict[str, Any] = {
        "memory_id": "",
        "memory_type": MemoryType.DEBATE,
        "version": 1,
        "timestamp": datetime.now(),
        "source_module": "debate_engine",
        "quality_score": 0.82,
        "confidence": 0.78,
        "lineage": MemoryLineage(
            created_by="test",
            created_at=datetime.now(),
            parent_ids=[],
            module_chain=["debate_engine"],
            reasoning_id=None,
            debate_id="debate-001",
        ),
        "tags": ["debate", "consensus"],
        "metadata": {"num_agents": 3},
        "content": {
            "agent_results": [{"agent": "A", "vote": "duplicate"}],
            "votes": {"duplicate": 2, "not_duplicate": 1},
            "conflicts": [{"type": "semantic", "severity": 0.3}],
            "consensus": True,
            "disagreements": [],
            "confidence_distribution": {"mean": 0.8, "std": 0.1},
        },
        "embedding": None,
        "expires_at": None,
        "status": MemoryStatus.ACTIVE,
    }
    base.update(overrides)
    entry = MemoryEntry(**base)
    if not entry.memory_id:
        entry.memory_id = str(uuid.uuid4())
    return entry


def create_performance_memory(**overrides: Any) -> MemoryEntry:
    base: dict[str, Any] = {
        "memory_id": "",
        "memory_type": MemoryType.PERFORMANCE,
        "version": 1,
        "timestamp": datetime.now(),
        "source_module": "monitoring",
        "quality_score": 0.9,
        "confidence": 0.95,
        "lineage": MemoryLineage(
            created_by="test",
            created_at=datetime.now(),
            parent_ids=[],
            module_chain=["monitoring"],
            reasoning_id=None,
            debate_id=None,
        ),
        "tags": ["performance", "metrics"],
        "metadata": {"host": "localhost"},
        "content": {
            "latency_ms": 145.2,
            "pipeline_cost": 0.05,
            "routing_decision": "cross_encoder",
            "memory_hit_rate": 0.87,
        },
        "embedding": None,
        "expires_at": None,
        "status": MemoryStatus.ACTIVE,
    }
    base.update(overrides)
    entry = MemoryEntry(**base)
    if not entry.memory_id:
        entry.memory_id = str(uuid.uuid4())
    return entry


# -- retrieval_ranker.py --


class RecencyRanker(RetrievalRanker):
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        return sorted(entries, key=lambda e: e.timestamp, reverse=True)


class ConfidenceRanker(RetrievalRanker):
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        return sorted(entries, key=lambda e: e.confidence, reverse=True)


class QualityRanker(RetrievalRanker):
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        return sorted(entries, key=lambda e: e.quality_score, reverse=True)


@dataclass
class CompositeRanker(RetrievalRanker):
    rankers: list[tuple[RetrievalRanker, float]] = field(
        default_factory=lambda: [
            (RecencyRanker(), 0.33),
            (ConfidenceRanker(), 0.33),
            (QualityRanker(), 0.34),
        ]
    )

    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        if not entries:
            return []
        scored: list[tuple[MemoryEntry, float]] = [(e, 0.0) for e in entries]
        for ranker, weight in self.rankers:
            ranked = ranker.rank(entries, query)
            for i, e in enumerate(ranked):
                for j, (scored_entry, score) in enumerate(scored):
                    if scored_entry.memory_id == e.memory_id:
                        scored[j] = (scored_entry, score + weight * (1.0 - i / len(ranked)))
                        break
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored]


# -- retrieval_engine.py --


class DefaultRetrievalEngine(RetrievalEngine):
    def retrieve(
        self,
        query: MemoryQuery,
        store: MemoryStore,
        index: MemoryIndex | None = None,
        ranker: RetrievalRanker | None = None,
    ) -> MemoryResult:
        start = datetime.now()
        if index is not None:
            entries = index.search(query, store)
        else:
            all_entries, _ = store.list_all(limit=100000)
            entries = self._filter(all_entries, query)

        total = len(entries)
        sliced = entries[query.offset : query.offset + query.limit]

        if ranker is not None:
            sliced = ranker.rank(sliced, query)

        elapsed = (datetime.now() - start).total_seconds() * 1000.0
        return MemoryResult(entries=sliced, total_count=total, query_time_ms=elapsed, query=query)

    def _filter(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        result = list(entries)
        if query.memory_types:
            type_values = {mt.value for mt in query.memory_types}
            result = [e for e in result if e.memory_type.value in type_values]
        if query.tags:
            result = [e for e in result if any(t in e.tags for t in query.tags)]
        if query.source_modules:
            result = [e for e in result if e.source_module in query.source_modules]
        if query.min_confidence > 0.0:
            result = [e for e in result if e.confidence >= query.min_confidence]
        if query.min_quality > 0.0:
            result = [e for e in result if e.quality_score >= query.min_quality]
        if query.text:
            text_lower = query.text.lower()
            result = [
                e
                for e in result
                if any(isinstance(v, str) and text_lower in v.lower() for v in e.content.values())
                or any(text_lower in t.lower() for t in e.tags)
            ]
        return [e for e in result if e.status != MemoryStatus.DELETED]


# -- memory_versioning.py --


class DefaultMemoryVersioning(MemoryVersioning):
    def __init__(self, max_versions: int = 10) -> None:
        self._max_versions = max_versions
        self._versions: dict[str, list[MemoryEntry]] = {}

    def create_version(self, entry: MemoryEntry, parent_id: str | None = None) -> MemoryEntry:
        history = self._versions.setdefault(entry.memory_id, [])
        if parent_id:
            parent = next((e for e in history if e.memory_id == parent_id), None)
            if parent is None:
                parent = entry
        else:
            parent = history[-1] if history else entry

        new_version = MemoryEntry(
            memory_id=entry.memory_id,
            memory_type=entry.memory_type,
            version=len(history) + 1,
            timestamp=datetime.now(),
            source_module=entry.source_module,
            quality_score=entry.quality_score,
            confidence=entry.confidence,
            lineage=entry.lineage,
            tags=list(entry.tags),
            metadata=dict(entry.metadata),
            content=dict(entry.content),
            embedding=list(entry.embedding) if entry.embedding is not None else None,
            expires_at=entry.expires_at,
            status=entry.status,
        )
        history.append(new_version)

        if len(history) > self._max_versions:
            history.pop(0)

        return new_version

    def get_version_history(self, memory_id: str, store: MemoryStore) -> list[MemoryEntry]:
        return list(self._versions.get(memory_id, []))


# -- forgetting_engine.py --


class AgingPolicy:
    def __init__(self, threshold_days: int = 90) -> None:
        self.threshold_days = threshold_days

    def should_archive(self, entry: MemoryEntry) -> bool:
        age = (datetime.now() - entry.timestamp).total_seconds()
        return age > self.threshold_days * 86400

    def age_score(self, entry: MemoryEntry) -> float:
        age_hours = (datetime.now() - entry.timestamp).total_seconds() / 3600.0
        return min(1.0, age_hours / (self.threshold_days * 24))

    def apply(self, entry: MemoryEntry) -> MemoryEntry:
        if self.should_archive(entry):
            entry.status = MemoryStatus.ARCHIVED
        return entry


class DefaultForgettingEngine(ForgettingEngine):
    def __init__(
        self,
        aging_policy: AgingPolicy | None = None,
        quality_threshold: float = 0.3,
        confidence_threshold: float = 0.2,
        enabled: bool = True,
    ) -> None:
        self._aging_policy = aging_policy or AgingPolicy()
        self._quality_threshold = quality_threshold
        self._confidence_threshold = confidence_threshold
        self._enabled = enabled

    def apply_policies(self, store: MemoryStore) -> list[str]:
        if not self._enabled:
            return []
        affected: list[str] = []
        entries, _ = store.list_all(limit=100000)
        for entry in entries:
            if entry.status != MemoryStatus.ACTIVE:
                continue
            if (
                self._aging_policy.should_archive(entry)
                or entry.quality_score < self._quality_threshold
                or entry.confidence < self._confidence_threshold
            ):
                entry.status = MemoryStatus.ARCHIVED
                affected.append(entry.memory_id)
        return affected

    def calculate_age_score(self, entry: MemoryEntry) -> float:
        return self._aging_policy.age_score(entry)


# -- memory_audit.py --


@dataclass
class AuditEntry:
    memory_id: str
    action: str
    module: str
    details: str
    timestamp: datetime


class DefaultMemoryAudit(MemoryAudit):
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._lock = threading.Lock()

    def log_access(self, memory_id: str, action: str, module: str, details: str = "") -> None:
        with self._lock:
            self._entries.append(
                AuditEntry(
                    memory_id=memory_id,
                    action=action,
                    module=module,
                    details=details,
                    timestamp=datetime.now(),
                )
            )

    def get_history(self, memory_id: str) -> list[dict]:
        with self._lock:
            return [
                {
                    "memory_id": e.memory_id,
                    "action": e.action,
                    "module": e.module,
                    "details": e.details,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self._entries
                if e.memory_id == memory_id
            ]

    def get_recent_actions(self, limit: int = 100) -> list[dict]:
        with self._lock:
            recent = list(reversed(self._entries))[:limit]
            return [
                {
                    "memory_id": e.memory_id,
                    "action": e.action,
                    "module": e.module,
                    "details": e.details,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in recent
            ]

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            action_counts: dict[str, int] = {}
            module_counts: dict[str, int] = {}
            for e in self._entries:
                action_counts[e.action] = action_counts.get(e.action, 0) + 1
                module_counts[e.module] = module_counts.get(e.module, 0) + 1
            return {
                "total_entries": len(self._entries),
                "action_counts": action_counts,
                "module_counts": module_counts,
            }

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


# -- memory_lineage.py --


class MemoryLineageTracker:
    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}

    def track(self, entry: MemoryEntry) -> None:
        self._entries[entry.memory_id] = entry

    def get_ancestors(self, memory_id: str) -> list[MemoryEntry]:
        ancestors: list[MemoryEntry] = []
        current = self._entries.get(memory_id)
        seen: set[str] = set()
        while current is not None:
            if current.memory_id in seen:
                break
            seen.add(current.memory_id)
            for pid in current.lineage.parent_ids:
                parent = self._entries.get(pid)
                if parent is not None:
                    ancestors.append(parent)
                    current = parent
                    break
            else:
                break
        return ancestors

    def get_descendants(self, memory_id: str) -> list[MemoryEntry]:
        descendants: list[MemoryEntry] = []
        for entry in self._entries.values():
            if memory_id in entry.lineage.parent_ids:
                descendants.append(entry)
        return descendants

    def merge_lineages(self, lineage_a: MemoryLineage, lineage_b: MemoryLineage) -> MemoryLineage:
        all_parents = list(set(lineage_a.parent_ids + lineage_b.parent_ids))
        module_chain = list(dict.fromkeys(lineage_a.module_chain + lineage_b.module_chain))
        return MemoryLineage(
            created_by=lineage_a.created_by,
            created_at=min(lineage_a.created_at, lineage_b.created_at),
            parent_ids=all_parents,
            module_chain=module_chain,
            reasoning_id=lineage_a.reasoning_id or lineage_b.reasoning_id,
            debate_id=lineage_a.debate_id or lineage_b.debate_id,
        )


# -- memory_consolidator.py --


class DefaultMemoryConsolidator(MemoryConsolidator):
    def find_duplicates(self, entries: list[MemoryEntry]) -> list[list[MemoryEntry]]:
        groups: dict[tuple, list[MemoryEntry]] = {}
        for e in entries:
            key = self._duplicate_key(e)
            groups.setdefault(key, []).append(e)
        return [g for g in groups.values() if len(g) > 1]

    def consolidate(self, entries: list[MemoryEntry], store: MemoryStore) -> list[str]:
        merged_ids: list[str] = []
        duplicates = self.find_duplicates(entries)
        for group in duplicates:
            if len(group) < 2:
                continue
            best = max(group, key=lambda e: (e.quality_score, e.confidence))
            for dup in group:
                if dup.memory_id != best.memory_id:
                    store.delete(dup.memory_id, soft=True)
                    merged_ids.append(dup.memory_id)
        return merged_ids

    def _duplicate_key(self, entry: MemoryEntry) -> tuple:
        content_str = str(sorted(entry.content.items()))
        return (entry.memory_type.value, tuple(sorted(entry.tags)), content_str)


# -- knowledge_graph.py --


@dataclass
class KnowledgeNode:
    id: str
    label: str
    node_type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeEdge:
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, KnowledgeNode] = {}
        self._edges: list[KnowledgeEdge] = []
        self._adjacency: dict[str, list[tuple[str, str, float]]] = {}

    def add_node(self, node: KnowledgeNode) -> None:
        self._nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        return self._nodes.get(node_id)

    def add_edge(self, edge: KnowledgeEdge) -> None:
        if edge.source_id not in self._nodes:
            raise KeyError(f"Source node {edge.source_id} not found")
        if edge.target_id not in self._nodes:
            raise KeyError(f"Target node {edge.target_id} not found")
        self._edges.append(edge)
        self._adjacency.setdefault(edge.source_id, []).append((edge.target_id, edge.relation, edge.weight))

    def get_neighbors(self, node_id: str) -> list[tuple[str, str, float]]:
        return list(self._adjacency.get(node_id, []))

    def traverse(self, start_id: str, max_depth: int = 3) -> list[KnowledgeNode]:
        visited: set[str] = set()
        result: list[KnowledgeNode] = []
        queue: list[tuple[str, int]] = [(start_id, 0)]
        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)
            node = self._nodes.get(current_id)
            if node is not None:
                result.append(node)
            for neighbor_id, _, _ in self._adjacency.get(current_id, []):
                if neighbor_id not in visited:
                    queue.append((neighbor_id, depth + 1))
        return result

    def search_nodes(self, query: str) -> list[KnowledgeNode]:
        q = query.lower()
        return [n for n in self._nodes.values() if q in n.label.lower() or q in n.node_type.lower()]

    def search_by_type(self, node_type: str) -> list[KnowledgeNode]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "node_type": n.node_type,
                    "properties": dict(n.properties),
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation": e.relation,
                    "weight": e.weight,
                    "properties": dict(e.properties),
                }
                for e in self._edges
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeGraph:
        g = cls()
        for nd in data.get("nodes", []):
            g.add_node(
                KnowledgeNode(
                    id=nd["id"],
                    label=nd["label"],
                    node_type=nd["node_type"],
                    properties=nd.get("properties", {}),
                )
            )
        for ed in data.get("edges", []):
            g.add_edge(
                KnowledgeEdge(
                    source_id=ed["source_id"],
                    target_id=ed["target_id"],
                    relation=ed["relation"],
                    weight=ed.get("weight", 1.0),
                    properties=ed.get("properties", {}),
                )
            )
        return g

    @staticmethod
    def build_from_memory_entries(entries: list[MemoryEntry]) -> KnowledgeGraph:
        g = KnowledgeGraph()
        for entry in entries:
            g.add_node(
                KnowledgeNode(
                    id=entry.memory_id,
                    label=f"{entry.memory_type.value}:{entry.memory_id[:8]}",
                    node_type=entry.memory_type.value,
                    properties={
                        "quality": entry.quality_score,
                        "confidence": entry.confidence,
                        "source": entry.source_module,
                    },
                )
            )
        return g


# -- memory_quality.py --


class MemoryQualityScorer:
    def score(self, entry: MemoryEntry) -> float:
        confidence_weight = 0.4
        completeness_weight = 0.3
        usage_weight = 0.3

        confidence_score = entry.confidence
        completeness_score = self._compute_completeness(entry)
        usage_score = self._compute_usage(entry)

        raw = (
            confidence_weight * confidence_score + completeness_weight * completeness_score + usage_weight * usage_score
        )
        return max(0.0, min(1.0, raw))

    def _compute_completeness(self, entry: MemoryEntry) -> float:
        if not entry.content:
            return 0.0
        filled = sum(1 for v in entry.content.values() if v is not None and v != "" and v != [])
        return filled / len(entry.content) if entry.content else 0.0

    def _compute_usage(self, entry: MemoryEntry) -> float:
        return entry.quality_score


# -- memory_engine.py --


class MemoryEngine:
    def __init__(
        self,
        store: MemoryStore | None = None,
        index: MemoryIndex | None = None,
        retrieval: RetrievalEngine | None = None,
        consolidator: MemoryConsolidator | None = None,
        versioning: MemoryVersioning | None = None,
        forgetting: ForgettingEngine | None = None,
        audit: MemoryAudit | None = None,
        validator: MemoryValidator | None = None,
        config: MemoryConfig | None = None,
        plugins: list[MemoryPlugin] | None = None,
    ) -> None:
        self.config = config or MemoryConfig()
        self._store = store or InMemoryMemoryStore()
        self.index = index or DefaultMemoryIndex()
        self.retrieval = retrieval or DefaultRetrievalEngine()
        self.consolidator = consolidator or DefaultMemoryConsolidator()
        self.versioning = versioning or DefaultMemoryVersioning(max_versions=self.config.max_versions)
        self.forgetting = forgetting or DefaultForgettingEngine(
            aging_policy=AgingPolicy(threshold_days=self.config.aging_threshold_days),
            quality_threshold=self.config.quality_threshold,
            confidence_threshold=self.config.confidence_threshold,
            enabled=self.config.enable_forgetting,
        )
        self.audit = audit or DefaultMemoryAudit()
        self.validator = validator or DefaultMemoryValidator()
        self.plugins = plugins or []

    def store_entry(self, entry: MemoryEntry) -> StoreResult:
        for plugin in self.plugins:
            entry = plugin.process_before_store(entry)
        valid, errors = self.validator.validate(entry)
        if not valid:
            return StoreResult(
                memory_id=entry.memory_id or "",
                success=False,
                version=0,
                message="; ".join(errors),
            )
        memory_id = self._store.store(entry)
        self.index.index_entry(entry)
        self.versioning.create_version(entry)
        self.audit.log_access(memory_id, "store", entry.source_module)
        return StoreResult(memory_id=memory_id, success=True, version=entry.version, message="stored")

    def retrieve(self, memory_id: str) -> MemoryEntry | None:
        entry = self._store.retrieve(memory_id)
        self.audit.log_access(memory_id, "retrieve", "engine")
        if entry is not None:
            for plugin in self.plugins:
                entry = plugin.process_after_retrieve(entry)
        return entry

    def search(self, query: MemoryQuery, ranker: RetrievalRanker | None = None) -> MemoryResult:
        return self.retrieval.retrieve(query, self._store, self.index, ranker)

    def update(self, entry: MemoryEntry) -> StoreResult:
        try:
            memory_id = self._store.update(entry)
            self.index.rebuild([e for e in [self._store.retrieve(memory_id)] if e is not None])
            self.versioning.create_version(entry)
            self.audit.log_access(memory_id, "update", entry.source_module)
            return StoreResult(memory_id=memory_id, success=True, version=entry.version, message="updated")
        except KeyError:
            return StoreResult(memory_id=entry.memory_id, success=False, version=0, message="not found")

    def delete(self, memory_id: str, soft: bool = True) -> DeleteResult:
        success = self._store.delete(memory_id, soft=soft)
        if success:
            self.index.remove(memory_id)
            action = "soft_delete" if soft else "hard_delete"
        else:
            action = "delete_failed"
        self.audit.log_access(memory_id, action, "engine")
        return DeleteResult(
            memory_id=memory_id,
            success=success,
            soft_deleted=soft,
            message="deleted" if success else "not found",
        )

    def consolidate(self) -> ConsolidationResult:
        all_entries, _ = self._store.list_all(limit=100000)
        merged = self.consolidator.consolidate(all_entries, self._store)
        return ConsolidationResult(
            merged_ids=merged,
            new_entry=None,
            summary=f"Consolidated {len(merged)} entries",
        )

    def get_statistics(self) -> MemoryStatistics:
        stats = DefaultMemoryStatistics()
        return stats.compute(self._store)

    def apply_forgetting(self) -> list[str]:
        return self.forgetting.apply_policies(self._store)

    def get_version_history(self, memory_id: str) -> list[MemoryEntry]:
        return self.versioning.get_version_history(memory_id, self._store)


# -- memory_manager.py --


class MemoryManager:
    def __init__(self, engine: MemoryEngine | None = None) -> None:
        self._engine = engine or MemoryEngine()
        self._graph: KnowledgeGraph | None = None

    @property
    def engine(self) -> MemoryEngine:
        return self._engine

    def store_episodic(self, **overrides: Any) -> StoreResult:
        entry = create_episodic_memory(**overrides)
        return self._engine.store_entry(entry)

    def store_semantic(self, **overrides: Any) -> StoreResult:
        entry = create_semantic_memory(**overrides)
        return self._engine.store_entry(entry)

    def store_reasoning(self, **overrides: Any) -> StoreResult:
        entry = create_reasoning_memory(**overrides)
        return self._engine.store_entry(entry)

    def store_debate(self, **overrides: Any) -> StoreResult:
        entry = create_debate_memory(**overrides)
        return self._engine.store_entry(entry)

    def store_performance(self, **overrides: Any) -> StoreResult:
        entry = create_performance_memory(**overrides)
        return self._engine.store_entry(entry)

    def retrieve(self, memory_id: str) -> MemoryEntry | None:
        return self._engine.retrieve(memory_id)

    def search(self, query: MemoryQuery, ranker: RetrievalRanker | None = None) -> MemoryResult:
        return self._engine.search(query, ranker)

    def delete(self, memory_id: str, soft: bool = True) -> DeleteResult:
        return self._engine.delete(memory_id, soft)

    def consolidate(self) -> ConsolidationResult:
        return self._engine.consolidate()

    def get_statistics(self) -> MemoryStatistics:
        return self._engine.get_statistics()

    def get_knowledge_graph(self) -> KnowledgeGraph:
        if self._graph is None:
            self._graph = KnowledgeGraph()
        return self._graph

    def build_knowledge_graph(self, memory_type: MemoryType | None = None) -> KnowledgeGraph:
        if memory_type is not None:
            entries, _ = self._engine._store.list_by_type(memory_type, limit=10000)
        else:
            entries, _ = self._engine._store.list_all(limit=10000)
        self._graph = KnowledgeGraph.build_from_memory_entries(entries)
        return self._graph

    def audit_history(self, memory_id: str) -> list[dict]:
        return self._engine.audit.get_history(memory_id)

    def recent_audit_actions(self, limit: int = 100) -> list[dict]:
        return self._engine.audit.get_recent_actions(limit)


# -- retrieval_strategy.py --


class RetrievalStrategy(Enum):
    EXACT = "exact"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


def get_retrieval_function(strategy: RetrievalStrategy) -> Callable:
    strategies: dict[RetrievalStrategy, Callable] = {
        RetrievalStrategy.EXACT: lambda q, s, i, r: DefaultRetrievalEngine().retrieve(q, s, i, r),
        RetrievalStrategy.SEMANTIC: lambda q, s, i, r: DefaultRetrievalEngine().retrieve(q, s, i, r),
        RetrievalStrategy.HYBRID: lambda q, s, i, r: DefaultRetrievalEngine().retrieve(q, s, i, r),
    }
    return strategies.get(strategy, strategies[RetrievalStrategy.EXACT])


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_episodic_entry() -> MemoryEntry:
    return create_episodic_memory()


@pytest.fixture
def sample_semantic_entry() -> MemoryEntry:
    return create_semantic_memory()


@pytest.fixture
def sample_reasoning_entry() -> MemoryEntry:
    return create_reasoning_memory()


@pytest.fixture
def sample_debate_entry() -> MemoryEntry:
    return create_debate_memory()


@pytest.fixture
def sample_performance_entry() -> MemoryEntry:
    return create_performance_memory()


@pytest.fixture
def sample_entries_all_types() -> list[MemoryEntry]:
    return [
        create_episodic_memory(tags=["episodic", "qa"]),
        create_semantic_memory(tags=["semantic", "concept"]),
        create_reasoning_memory(tags=["reasoning", "inference"]),
        create_debate_memory(tags=["debate", "consensus"]),
        create_performance_memory(tags=["performance", "metrics"]),
    ]


@pytest.fixture
def memory_store() -> InMemoryMemoryStore:
    return InMemoryMemoryStore()


@pytest.fixture
def memory_index() -> DefaultMemoryIndex:
    return DefaultMemoryIndex()


@pytest.fixture
def memory_engine() -> MemoryEngine:
    return MemoryEngine()


@pytest.fixture
def memory_manager() -> MemoryManager:
    return MemoryManager()


@pytest.fixture
def knowledge_graph() -> KnowledgeGraph:
    return KnowledgeGraph()


@pytest.fixture
def memory_config() -> MemoryConfig:
    return MemoryConfig()


@pytest.fixture
def populated_store(
    memory_store: InMemoryMemoryStore, sample_entries_all_types: list[MemoryEntry]
) -> InMemoryMemoryStore:
    for entry in sample_entries_all_types:
        memory_store.store(entry)
    return memory_store


@pytest.fixture
def populated_engine(memory_engine: MemoryEngine, sample_entries_all_types: list[MemoryEntry]) -> MemoryEngine:
    for entry in sample_entries_all_types:
        memory_engine.store_entry(entry)
    return memory_engine
