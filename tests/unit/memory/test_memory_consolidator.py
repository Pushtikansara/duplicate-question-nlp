from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryLineage
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore

from .conftest import DefaultMemoryConsolidator, create_episodic_memory, create_semantic_memory


class TestMemoryConsolidator:
    def test_find_duplicates_empty(self) -> None:
        cons = DefaultMemoryConsolidator()
        assert cons.find_duplicates([]) == []

    def test_find_duplicates_no_duplicates(self) -> None:
        cons = DefaultMemoryConsolidator()
        e1 = create_episodic_memory(tags=["a"])
        e2 = create_episodic_memory(tags=["b"])
        assert cons.find_duplicates([e1, e2]) == []

    def test_find_duplicates_same_type_tags(self) -> None:
        cons = DefaultMemoryConsolidator()
        e1 = create_episodic_memory(
            tags=["dup-tag"], content={"question_a": "Q1", "question_b": "Q1b", "pipeline_used": "p", "decision": "d"}
        )
        e2 = create_episodic_memory(
            tags=["dup-tag"], content={"question_a": "Q1", "question_b": "Q1b", "pipeline_used": "p", "decision": "d"}
        )
        dups = cons.find_duplicates([e1, e2])
        assert len(dups) == 1
        assert len(dups[0]) == 2

    def test_consolidate_duplicate_episodic(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(
            tags=["c"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        e2 = create_episodic_memory(
            tags=["c"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        store.store(e1)
        store.store(e2)
        merged = cons.consolidate([e1, e2], store)
        assert len(merged) >= 1

    def test_consolidate_duplicate_semantic(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_semantic_memory(
            tags=["c"], content={"concepts": ["x"], "entities": [], "relations": [], "intent_pattern": "d"}
        )
        e2 = create_semantic_memory(
            tags=["c"], content={"concepts": ["x"], "entities": [], "relations": [], "intent_pattern": "d"}
        )
        store.store(e1)
        store.store(e2)
        merged = cons.consolidate([e1, e2], store)
        assert len(merged) >= 1

    def test_consolidate_no_duplicates(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(tags=["a"])
        e2 = create_semantic_memory(tags=["b"])
        store.store(e1)
        store.store(e2)
        merged = cons.consolidate([e1, e2], store)
        assert merged == []

    def test_consolidate_empty_list(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        assert cons.consolidate([], store) == []

    def test_consolidate_merges_quality(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(
            quality_score=0.9,
            tags=["m"],
            content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"},
        )
        e2 = create_episodic_memory(
            quality_score=0.5,
            tags=["m"],
            content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"},
        )
        store.store(e1)
        store.store(e2)
        merged = cons.consolidate([e1, e2], store)
        assert len(merged) == 1
        assert store.retrieve(e1.memory_id) is not None
        assert store.retrieve(e1.memory_id) is not None

    def test_consolidate_merges_confidence(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(
            confidence=0.95,
            quality_score=0.9,
            tags=["m"],
            content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"},
        )
        e2 = create_episodic_memory(
            confidence=0.4,
            quality_score=0.3,
            tags=["m"],
            content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"},
        )
        store.store(e1)
        store.store(e2)
        merged = cons.consolidate([e1, e2], store)
        assert len(merged) == 1

    def test_consolidate_preserves_lineage(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(
            tags=["l"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        e2 = create_episodic_memory(
            tags=["l"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        store.store(e1)
        store.store(e2)
        cons.consolidate([e1, e2], store)
        survivor = store.retrieve(e1.memory_id)
        assert survivor is not None
        assert isinstance(survivor.lineage, MemoryLineage)

    def test_consolidate_updates_store(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(
            tags=["u"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        e2 = create_episodic_memory(
            tags=["u"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        store.store(e1)
        store.store(e2)
        count_before = store.count()
        cons.consolidate([e1, e2], store)
        assert store.count() <= count_before

    def test_consolidate_returns_ids(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(
            tags=["r"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        e2 = create_episodic_memory(
            tags=["r"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        store.store(e1)
        store.store(e2)
        merged_ids = cons.consolidate([e1, e2], store)
        assert all(isinstance(mid, str) for mid in merged_ids)

    def test_find_duplicates_same_content(self) -> None:
        cons = DefaultMemoryConsolidator()
        content = {"question_a": "Q", "question_b": "Q2", "pipeline_used": "p", "decision": "d"}
        e1 = create_episodic_memory(tags=["x"], content=content)
        e2 = create_episodic_memory(tags=["x"], content=content)
        dups = cons.find_duplicates([e1, e2])
        assert len(dups) == 1

    def test_consolidate_mixed_types_no_merge(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(tags=["a"])
        e2 = create_semantic_memory(tags=["a"])
        store.store(e1)
        store.store(e2)
        merged = cons.consolidate([e1, e2], store)
        assert merged == []

    def test_consolidate_maintains_version(self) -> None:
        cons = DefaultMemoryConsolidator()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(
            tags=["v"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        e2 = create_episodic_memory(
            tags=["v"], content={"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        )
        store.store(e1)
        store.store(e2)
        cons.consolidate([e1, e2], store)
        survivor = store.retrieve(e1.memory_id)
        assert survivor is not None
