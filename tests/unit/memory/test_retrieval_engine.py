from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryQuery, MemoryType
from duplicate_question_app._memory.memory_index import DefaultMemoryIndex
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore

from .conftest import (
    ConfidenceRanker,
    DefaultRetrievalEngine,
    create_episodic_memory,
    create_reasoning_memory,
    create_semantic_memory,
)


class TestRetrievalEngine:
    def test_retrieve_by_type(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory()
        memory_store.store(e)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 1
        assert result.entries[0].memory_type == MemoryType.EPISODIC

    def test_retrieve_by_tags(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory(tags=["find-me"])
        memory_store.store(e)
        query = MemoryQuery(tags=["find-me"])
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 1

    def test_retrieve_by_confidence(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory(confidence=0.95)
        memory_store.store(e)
        query = MemoryQuery(min_confidence=0.9)
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 1

    def test_retrieve_with_ranker(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e1 = create_episodic_memory(confidence=0.5, memory_id="low-conf")
        e2 = create_episodic_memory(confidence=0.95, memory_id="high-conf")
        memory_store.store(e1)
        memory_store.store(e2)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        ranker = ConfidenceRanker()
        result = eng.retrieve(query, memory_store, ranker=ranker)
        assert result.entries[0].memory_id == "high-conf"

    def test_retrieve_empty_result(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store)
        assert result.entries == []
        assert result.total_count == 0

    def test_retrieve_with_index(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        index = DefaultMemoryIndex()
        e = create_episodic_memory()
        memory_store.store(e)
        index.index_entry(e)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store, index=index)
        assert len(result.entries) == 1

    def test_retrieve_without_index(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory()
        memory_store.store(e)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store, index=None)
        assert len(result.entries) == 1

    def test_retrieve_limit(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        for i in range(10):
            memory_store.store(create_episodic_memory(memory_id=f"lim-{i}"))
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC], limit=3)
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 3

    def test_retrieve_offset(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        for i in range(10):
            memory_store.store(create_episodic_memory(memory_id=f"off-{i}"))
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC], limit=100, offset=7)
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 3

    def test_retrieve_pagination(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        for i in range(25):
            memory_store.store(create_episodic_memory(memory_id=f"pg-{i}"))
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC], limit=10, offset=0)
        page1 = eng.retrieve(query, memory_store)
        assert len(page1.entries) == 10
        query.offset = 10
        page2 = eng.retrieve(query, memory_store)
        assert len(page2.entries) == 10
        assert page2.entries[0].memory_id != page1.entries[0].memory_id

    def test_retrieve_hybrid(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory(tags=["hybrid-tag"], source_module="hybrid-src")
        memory_store.store(e)
        query = MemoryQuery(tags=["hybrid-tag"], source_modules=["hybrid-src"])
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 1

    def test_retrieve_time_measured(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        memory_store.store(create_episodic_memory())
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store)
        assert result.query_time_ms >= 0.0

    def test_retrieve_result_fields(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory()
        memory_store.store(e)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store)
        assert hasattr(result, "entries")
        assert hasattr(result, "total_count")
        assert hasattr(result, "query_time_ms")
        assert hasattr(result, "query")

    def test_retrieve_all_entries(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        for entry in [create_episodic_memory(), create_semantic_memory(), create_reasoning_memory()]:
            memory_store.store(entry)
        query = MemoryQuery()
        result = eng.retrieve(query, memory_store)
        assert result.total_count == 3

    def test_retrieve_by_text(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory(
            content={
                "question_a": "unique text search term",
                "question_b": "other",
                "pipeline_used": "test",
                "decision": "duplicate",
            }
        )
        memory_store.store(e)
        query = MemoryQuery(text="unique text search term")
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 1

    def test_retrieve_by_source_module(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory(source_module="custom-source")
        memory_store.store(e)
        query = MemoryQuery(source_modules=["custom-source"])
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 1

    def test_retrieve_multiple_types(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        memory_store.store(create_episodic_memory())
        memory_store.store(create_semantic_memory())
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC])
        result = eng.retrieve(query, memory_store)
        assert result.total_count == 2

    def test_retrieve_with_none_ranker(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory()
        memory_store.store(e)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store, ranker=None)
        assert len(result.entries) == 1

    def test_retrieve_after_delete(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        e = create_episodic_memory()
        mid = memory_store.store(e)
        memory_store.delete(mid, soft=True)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store)
        assert len(result.entries) == 0

    def test_retrieve_preserves_order_without_ranker(self, memory_store: InMemoryMemoryStore) -> None:
        eng = DefaultRetrievalEngine()
        ids = []
        for i in range(5):
            e = create_episodic_memory(memory_id=f"order-{i}")
            memory_store.store(e)
            ids.append(f"order-{i}")
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = eng.retrieve(query, memory_store)
        retrieved_ids = [e.memory_id for e in result.entries]
        assert set(retrieved_ids) == set(ids)
