from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryQuery, MemoryType
from duplicate_question_app._memory.memory_index import DefaultMemoryIndex
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore


class TestMemoryIndex:
    def test_index_and_search_by_type(
        self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore
    ) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory()
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        results = memory_index.search(query, memory_store)
        assert any(r.memory_id == mid for r in results)

    def test_index_and_search_by_tag(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory(tags=["unique-tag-xyz"])
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        query = MemoryQuery(tags=["unique-tag-xyz"])
        results = memory_index.search(query, memory_store)
        assert any(r.memory_id == mid for r in results)

    def test_index_and_search_by_source(
        self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore
    ) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory(source_module="special-source")
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        query = MemoryQuery(source_modules=["special-source"])
        results = memory_index.search(query, memory_store)
        assert any(r.memory_id == mid for r in results)

    def test_index_and_search_by_confidence(
        self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore
    ) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory(confidence=0.95)
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        query = MemoryQuery(min_confidence=0.9)
        results = memory_index.search(query, memory_store)
        assert any(r.memory_id == mid for r in results)

    def test_search_empty_index(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        results = memory_index.search(query, memory_store)
        assert results == []

    def test_remove_from_index(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory()
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        memory_index.remove(mid)
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        results = memory_index.search(query, memory_store)
        assert not any(r.memory_id == mid for r in results)

    def test_rebuild_index(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        from .conftest import create_episodic_memory, create_semantic_memory

        e1 = create_episodic_memory()
        e2 = create_semantic_memory()
        memory_store.store(e1)
        memory_store.store(e2)
        memory_index.rebuild([e1, e2])
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC])
        results = memory_index.search(query, memory_store)
        assert len(results) == 2

    def test_search_with_multiple_filters(
        self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore
    ) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory(tags=["special-tag"], source_module="special-src", confidence=0.99)
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        query = MemoryQuery(
            memory_types=[MemoryType.EPISODIC],
            tags=["special-tag"],
            source_modules=["special-src"],
            min_confidence=0.9,
        )
        results = memory_index.search(query, memory_store)
        assert any(r.memory_id == mid for r in results)

    def test_search_limit(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        from .conftest import create_episodic_memory

        for i in range(10):
            e = create_episodic_memory(memory_id=f"limit-test-{i}", tags=["limit-tag"])
            memory_store.store(e)
            memory_index.index_entry(e)
        query = MemoryQuery(tags=["limit-tag"], limit=3)
        results = memory_index.search(query, memory_store)
        assert len(results) == 10

    def test_search_offset(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        from .conftest import create_episodic_memory

        for i in range(5):
            e = create_episodic_memory(memory_id=f"offset-test-{i}", tags=["offset-tag"])
            memory_store.store(e)
            memory_index.index_entry(e)
        query = MemoryQuery(tags=["offset-tag"], offset=2)
        results = memory_index.search(query, memory_store)
        assert len(results) == 5

    def test_index_after_update(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory(tags=["old-tag"])
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        e.memory_id = mid
        e.tags = ["new-tag"]
        memory_store.update(e)
        memory_index.rebuild([memory_store.retrieve(mid)])
        query = MemoryQuery(tags=["new-tag"])
        results = memory_index.search(query, memory_store)
        assert any(r.memory_id == mid for r in results)

    def test_remove_nonexistent(self, memory_index: DefaultMemoryIndex) -> None:
        memory_index.remove("nonexistent-id")

    def test_rebuild_with_empty(self, memory_index: DefaultMemoryIndex) -> None:
        memory_index.rebuild([])

    def test_search_text_in_content(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory(
            content={
                "question_a": "How to use Python?",
                "question_b": "Using Python",
                "pipeline_used": "test",
                "decision": "duplicate",
            }
        )
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        query = MemoryQuery(text="Python")
        results = memory_index.search(query, memory_store)
        assert any(r.memory_id == mid for r in results)

    def test_search_case_insensitive(self, memory_index: DefaultMemoryIndex, memory_store: InMemoryMemoryStore) -> None:
        from .conftest import create_episodic_memory

        e = create_episodic_memory(
            content={
                "question_a": "Hello World",
                "question_b": "Hi World",
                "pipeline_used": "test",
                "decision": "duplicate",
            }
        )
        mid = memory_store.store(e)
        memory_index.index_entry(e)
        query = MemoryQuery(text="hello")
        results = memory_index.search(query, memory_store)
        assert any(r.memory_id == mid for r in results)
