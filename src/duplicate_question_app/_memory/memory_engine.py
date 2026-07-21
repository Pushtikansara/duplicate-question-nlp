from __future__ import annotations

import logging

from duplicate_question_app._memory.forgetting_engine import DefaultForgettingEngine
from duplicate_question_app._memory.interfaces import (
    ForgettingEngine,
    MemoryAudit,
    MemoryConsolidator,
    MemoryEntry,
    MemoryIndex,
    MemoryPlugin,
    MemoryQuery,
    MemoryResult,
    MemoryStatistics,
    MemoryStore,
    MemoryValidator,
    MemoryVersioning,
    RetrievalEngine,
    RetrievalRanker,
)
from duplicate_question_app._memory.knowledge_graph import KnowledgeGraph
from duplicate_question_app._memory.memory_audit import DefaultMemoryAudit
from duplicate_question_app._memory.memory_configuration import MemoryConfig
from duplicate_question_app._memory.memory_consolidator import DefaultMemoryConsolidator
from duplicate_question_app._memory.memory_index import DefaultMemoryIndex
from duplicate_question_app._memory.memory_quality import MemoryQualityScorer
from duplicate_question_app._memory.memory_result import ConsolidationResult, DeleteResult, StoreResult
from duplicate_question_app._memory.memory_statistics import DefaultMemoryStatistics
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore
from duplicate_question_app._memory.memory_validator import DefaultMemoryValidator
from duplicate_question_app._memory.memory_versioning import DefaultMemoryVersioning
from duplicate_question_app._memory.plugins import DefaultMemoryPlugin
from duplicate_question_app._memory.retrieval_engine import DefaultRetrievalEngine

logger = logging.getLogger(__name__)


class MemoryEngine:
    def __init__(
        self,
        store: MemoryStore | None = None,
        index: MemoryIndex | None = None,
        retrieval: RetrievalEngine | None = None,
        ranker: RetrievalRanker | None = None,
        consolidator: MemoryConsolidator | None = None,
        versioning: MemoryVersioning | None = None,
        audit: MemoryAudit | None = None,
        forgetting: ForgettingEngine | None = None,
        validator: MemoryValidator | None = None,
        quality_scorer: MemoryQualityScorer | None = None,
        graph: KnowledgeGraph | None = None,
        config: MemoryConfig | None = None,
    ) -> None:
        self._config = config or MemoryConfig()
        self._store = store or InMemoryMemoryStore()
        self._index = index or DefaultMemoryIndex()
        self._retrieval = retrieval or DefaultRetrievalEngine(index=self._index)
        self._ranker = ranker
        self._consolidator = consolidator or DefaultMemoryConsolidator(config=self._config)
        self._versioning = versioning or DefaultMemoryVersioning(max_versions=self._config.max_versions)
        self._audit = audit or DefaultMemoryAudit()
        self._forgetting = forgetting or DefaultForgettingEngine(config=self._config)
        self._validator = validator or DefaultMemoryValidator()
        self._quality_scorer = quality_scorer or MemoryQualityScorer()
        self._graph = graph or KnowledgeGraph()
        self._plugin: MemoryPlugin = DefaultMemoryPlugin()
        self._stats = DefaultMemoryStatistics()
        self._store_count = 0

    def store(self, entry: MemoryEntry) -> StoreResult:
        entry = self._plugin.process_before_store(entry)

        valid, errors = self._validator.validate(entry)
        if not valid:
            return StoreResult(
                memory_id=entry.memory_id or "",
                success=False,
                version=0,
                message=f"Validation failed: {'; '.join(errors)}",
            )

        quality = self._quality_scorer.score(entry)
        entry.quality_score = quality

        if entry.memory_id and self._store.retrieve(entry.memory_id) is not None:
            entry = self._versioning.create_version(entry, parent_id=entry.memory_id)
            memory_id = self._store.update(entry)
        else:
            memory_id = self._store.store(entry)

        self._index.index_entry(entry)

        if self._config.enable_audit:
            self._audit.log_access(memory_id, "store", entry.source_module)

        self._store_count += 1
        if self._config.enable_consolidation and self._store_count >= self._config.auto_consolidate_interval:
            try:
                self.consolidate()
            except Exception:
                logger.exception("Auto-consolidation failed")
            self._store_count = 0

        return StoreResult(
            memory_id=memory_id,
            success=True,
            version=entry.version,
            message="Memory stored successfully",
        )

    def retrieve(self, memory_id: str) -> MemoryEntry | None:
        entry = self._store.retrieve(memory_id)
        if self._config.enable_audit:
            self._audit.log_access(memory_id, "retrieve", "memory_engine")
        entry = self._plugin.process_after_retrieve(entry)
        return entry

    def search(self, query: MemoryQuery) -> MemoryResult:
        result = self._retrieval.retrieve(query, self._store, index=self._index, ranker=self._ranker)
        if self._config.enable_audit:
            for entry in result.entries:
                self._audit.log_access(entry.memory_id, "search", "memory_engine", query.query_type)
        return result

    def update(self, entry: MemoryEntry) -> StoreResult:
        valid, errors = self._validator.validate(entry)
        if not valid:
            return StoreResult(
                memory_id=entry.memory_id,
                success=False,
                version=0,
                message=f"Validation failed: {'; '.join(errors)}",
            )

        entry = self._versioning.create_version(entry, parent_id=entry.memory_id)
        quality = self._quality_scorer.score(entry)
        entry.quality_score = quality

        try:
            memory_id = self._store.update(entry)
        except KeyError as e:
            return StoreResult(
                memory_id=entry.memory_id,
                success=False,
                version=0,
                message=str(e),
            )

        self._index.index_entry(entry)

        if self._config.enable_audit:
            self._audit.log_access(memory_id, "update", entry.source_module)

        return StoreResult(
            memory_id=memory_id,
            success=True,
            version=entry.version,
            message="Memory updated successfully",
        )

    def delete(self, memory_id: str, soft: bool = True) -> DeleteResult:
        success = self._store.delete(memory_id, soft=soft)
        if success:
            self._index.remove(memory_id)
            if self._config.enable_audit:
                action = "soft_delete" if soft else "hard_delete"
                self._audit.log_access(memory_id, action, "memory_engine")

        return DeleteResult(
            memory_id=memory_id,
            success=success,
            soft_deleted=soft,
            message="Memory deleted successfully" if success else "Memory not found",
        )

    def consolidate(self) -> ConsolidationResult:
        all_entries: list[MemoryEntry] = []
        offset = 0
        while True:
            batch, _ = self._store.list_all(limit=1000, offset=offset)
            if not batch:
                break
            all_entries.extend(batch)
            offset += len(batch)

        merged_ids = self._consolidator.consolidate(all_entries, self._store)

        if self._config.enable_audit:
            for mid in merged_ids:
                self._audit.log_access(mid, "consolidate", "memory_engine")

        return ConsolidationResult(
            merged_ids=merged_ids,
            new_entry=None,
            summary=f"Consolidated {len(merged_ids)} entries",
        )

    def get_statistics(self) -> MemoryStatistics:
        return self._stats.compute(self._store)

    def apply_forgetting(self) -> list[str]:
        affected = self._forgetting.apply_policies(self._store)
        if self._config.enable_audit:
            for mid in affected:
                self._audit.log_access(mid, "forgetting_archived", "memory_engine")
        return affected

    def get_version_history(self, memory_id: str) -> list[MemoryEntry]:
        return self._versioning.get_version_history(memory_id, self._store)

    @property
    def store_backend(self) -> MemoryStore:
        return self._store

    @property
    def index(self) -> MemoryIndex:
        return self._index

    @property
    def graph(self) -> KnowledgeGraph:
        return self._graph
