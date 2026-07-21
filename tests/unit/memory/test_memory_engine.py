from __future__ import annotations

import threading
from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryQuery, MemoryStatus, MemoryType
from duplicate_question_app._memory.memory_configuration import MemoryConfig
from duplicate_question_app._memory.memory_index import DefaultMemoryIndex
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore

from .conftest import (
    ConfidenceRanker,
    ConsolidationResult,
    DefaultForgettingEngine,
    DefaultMemoryAudit,
    DefaultMemoryConsolidator,
    DefaultMemoryValidator,
    DefaultMemoryVersioning,
    DefaultRetrievalEngine,
    MemoryEngine,
    StoreResult,
    create_episodic_memory,
    create_semantic_memory,
)


def _make_entry(mid: str) -> MemoryEntry:
    return MemoryEntry(
        memory_id=mid,
        memory_type=MemoryType.EPISODIC,
        version=1,
        timestamp=datetime.now(),
        source_module="test",
        quality_score=0.8,
        confidence=0.8,
        lineage=MemoryLineage(created_by="test", created_at=datetime.now()),
        tags=["engine"],
        metadata={},
        content={"question_a": "Q", "question_b": "Q2", "pipeline_used": "p", "decision": "d"},
        embedding=None,
        expires_at=None,
        status=MemoryStatus.ACTIVE,
    )


class TestMemoryEngine:
    def test_store_and_retrieve(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory()
        result = memory_engine.store_entry(entry)
        assert result.success is True
        retrieved = memory_engine.retrieve(result.memory_id)
        assert retrieved is not None
        assert retrieved.memory_type == MemoryType.EPISODIC

    def test_store_validates(self, memory_engine: MemoryEngine) -> None:
        entry = MemoryEntry(
            memory_id="invalid",
            memory_type=MemoryType.EPISODIC,
            version=0,
            timestamp=datetime.now(),
            source_module="test",
            quality_score=-0.1,
            confidence=1.5,
            lineage=MemoryLineage(created_by="", created_at=datetime.now()),
            tags=[],
            metadata={},
            content={},
        )
        result = memory_engine.store_entry(entry)
        assert result.success is False

    def test_store_versions(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory()
        result = memory_engine.store_entry(entry)
        history = memory_engine.get_version_history(result.memory_id)
        assert len(history) >= 1

    def test_store_indexes(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory(tags=["index-test"])
        memory_engine.store_entry(entry)
        query = MemoryQuery(tags=["index-test"])
        search_result = memory_engine.search(query)
        assert len(search_result.entries) == 1

    def test_store_audits(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory()
        result = memory_engine.store_entry(entry)
        history = memory_engine.audit.get_history(result.memory_id)
        assert len(history) >= 1

    def test_retrieve_nonexistent(self, memory_engine: MemoryEngine) -> None:
        assert memory_engine.retrieve("no-such") is None

    def test_search_by_type(self, memory_engine: MemoryEngine) -> None:
        memory_engine.store_entry(create_episodic_memory())
        memory_engine.store_entry(create_semantic_memory())
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = memory_engine.search(query)
        assert result.total_count == 1

    def test_search_by_tags(self, memory_engine: MemoryEngine) -> None:
        memory_engine.store_entry(create_episodic_memory(tags=["search-tag"]))
        query = MemoryQuery(tags=["search-tag"])
        result = memory_engine.search(query)
        assert result.total_count == 1

    def test_search_by_confidence(self, memory_engine: MemoryEngine) -> None:
        memory_engine.store_entry(create_episodic_memory(confidence=0.95))
        query = MemoryQuery(min_confidence=0.9)
        result = memory_engine.search(query)
        assert result.total_count >= 1

    def test_search_with_ranker(self, memory_engine: MemoryEngine) -> None:
        memory_engine.store_entry(create_episodic_memory(confidence=0.5))
        memory_engine.store_entry(create_episodic_memory(confidence=0.95))
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = memory_engine.search(query, ranker=ConfidenceRanker())
        assert result.entries[0].confidence == 0.95

    def test_update_entry(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory()
        result = memory_engine.store_entry(entry)
        entry.memory_id = result.memory_id
        entry.quality_score = 0.99
        update_result = memory_engine.update(entry)
        assert update_result.success is True
        retrieved = memory_engine.retrieve(result.memory_id)
        assert retrieved is not None

    def test_soft_delete(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory()
        result = memory_engine.store_entry(entry)
        delete_result = memory_engine.delete(result.memory_id, soft=True)
        assert delete_result.success is True
        assert delete_result.soft_deleted is True
        assert memory_engine.retrieve(result.memory_id) is not None

    def test_consolidate(self, memory_engine: MemoryEngine) -> None:
        content = {"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        e1 = create_episodic_memory(tags=["c"], content=content)
        e2 = create_episodic_memory(tags=["c"], content=content)
        memory_engine.store_entry(e1)
        memory_engine.store_entry(e2)
        result = memory_engine.consolidate()
        assert isinstance(result, ConsolidationResult)
        assert isinstance(result.merged_ids, list)

    def test_get_statistics_empty(self, memory_engine: MemoryEngine) -> None:
        stats = memory_engine.get_statistics()
        assert stats.total_entries == 0

    def test_get_statistics_after_store(self, memory_engine: MemoryEngine) -> None:
        memory_engine.store_entry(create_episodic_memory())
        memory_engine.store_entry(create_semantic_memory())
        stats = memory_engine.get_statistics()
        assert stats.total_entries == 2

    def test_apply_forgetting(self, memory_engine: MemoryEngine) -> None:
        memory_engine.store_entry(create_episodic_memory())
        affected = memory_engine.apply_forgetting()
        assert isinstance(affected, list)

    def test_get_version_history(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory()
        result = memory_engine.store_entry(entry)
        history = memory_engine.get_version_history(result.memory_id)
        assert isinstance(history, list)

    def test_store_with_invalid_entry(self, memory_engine: MemoryEngine) -> None:
        entry = MemoryEntry(
            memory_id="",
            memory_type=MemoryType.EPISODIC,
            version=0,
            timestamp=datetime.now(),
            source_module="",
            quality_score=-1.0,
            confidence=-1.0,
            lineage=MemoryLineage(created_by="", created_at=datetime.now()),
            tags=[],
            metadata={},
            content={},
        )
        result = memory_engine.store_entry(entry)
        assert result.success is False

    def test_engine_default_components(self) -> None:
        engine = MemoryEngine()
        assert isinstance(engine._store, InMemoryMemoryStore)
        assert isinstance(engine.index, DefaultMemoryIndex)
        assert isinstance(engine.retrieval, DefaultRetrievalEngine)
        assert isinstance(engine.consolidator, DefaultMemoryConsolidator)
        assert isinstance(engine.versioning, DefaultMemoryVersioning)
        assert isinstance(engine.forgetting, DefaultForgettingEngine)
        assert isinstance(engine.audit, DefaultMemoryAudit)
        assert isinstance(engine.validator, DefaultMemoryValidator)

    def test_engine_custom_components(self) -> None:
        custom_store = InMemoryMemoryStore()
        custom_index = DefaultMemoryIndex()
        engine = MemoryEngine(store=custom_store, index=custom_index)
        assert engine._store is custom_store
        assert engine.index is custom_index

    def test_engine_config(self) -> None:
        config = MemoryConfig(max_entries=500)
        engine = MemoryEngine(config=config)
        assert engine.config.max_entries == 500

    def test_search_empty(self, memory_engine: MemoryEngine) -> None:
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = memory_engine.search(query)
        assert result.entries == []

    def test_delete_then_retrieve(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory()
        result = memory_engine.store_entry(entry)
        memory_engine.delete(result.memory_id)
        retrieved = memory_engine.retrieve(result.memory_id)
        assert retrieved is not None

    def test_concurrent_operations(self, memory_engine: MemoryEngine) -> None:
        errors: list[Exception] = []

        def _worker() -> None:
            try:
                for _ in range(25):
                    e = create_episodic_memory()
                    memory_engine.store_entry(e)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        stats = memory_engine.get_statistics()
        assert stats.total_entries == 100

    def test_store_returns_store_result(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory()
        result = memory_engine.store_entry(entry)
        assert isinstance(result, StoreResult)
        assert result.memory_id != ""
        assert result.success is True
        assert result.version >= 1
