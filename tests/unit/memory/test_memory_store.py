from __future__ import annotations

import threading

import pytest

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore


class TestMemoryStore:
    def test_store_and_retrieve(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        mid = memory_store.store(sample_episodic_entry)
        retrieved = memory_store.retrieve(mid)
        assert retrieved is not None
        assert retrieved.memory_id == mid
        assert retrieved.memory_type == MemoryType.EPISODIC

    def test_store_generates_id(self, memory_store: InMemoryMemoryStore) -> None:
        entry = MemoryEntry(
            memory_id="",
            memory_type=MemoryType.EPISODIC,
            version=1,
            timestamp=__import__("datetime").datetime.now(),
            source_module="test",
            quality_score=0.8,
            confidence=0.9,
            lineage=MemoryLineage(created_by="test", created_at=__import__("datetime").datetime.now()),
            tags=["test"],
            metadata={},
            content={"key": "value"},
        )
        mid = memory_store.store(entry)
        assert mid != ""

    def test_retrieve_nonexistent_returns_none(self, memory_store: InMemoryMemoryStore) -> None:
        assert memory_store.retrieve("nonexistent-id") is None

    def test_update_existing(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        mid = memory_store.store(sample_episodic_entry)
        sample_episodic_entry.memory_id = mid
        sample_episodic_entry.quality_score = 0.95
        updated_id = memory_store.update(sample_episodic_entry)
        assert updated_id == mid
        retrieved = memory_store.retrieve(mid)
        assert retrieved is not None
        assert retrieved.version == 2
        assert retrieved.quality_score == 0.95

    def test_update_nonexistent_raises_key_error(self, memory_store: InMemoryMemoryStore) -> None:
        entry = MemoryEntry(
            memory_id="no-such-id",
            memory_type=MemoryType.EPISODIC,
            version=1,
            timestamp=__import__("datetime").datetime.now(),
            source_module="test",
            quality_score=0.8,
            confidence=0.9,
            lineage=MemoryLineage(created_by="test", created_at=__import__("datetime").datetime.now()),
            tags=["test"],
            metadata={},
            content={"key": "value"},
        )
        with pytest.raises(KeyError):
            memory_store.update(entry)

    def test_soft_delete(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        mid = memory_store.store(sample_episodic_entry)
        result = memory_store.delete(mid, soft=True)
        assert result is True
        retrieved = memory_store.retrieve(mid)
        assert retrieved is not None
        assert retrieved.status == MemoryStatus.DELETED

    def test_hard_delete(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        mid = memory_store.store(sample_episodic_entry)
        result = memory_store.delete(mid, soft=False)
        assert result is True
        assert memory_store.retrieve(mid) is None

    def test_deleted_not_in_list(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        mid = memory_store.store(sample_episodic_entry)
        before, total_before = memory_store.list_all()
        assert total_before == 1
        memory_store.delete(mid, soft=True)
        after, total_after = memory_store.list_all()
        assert total_after == 0

    def test_list_by_type(self, populated_store: InMemoryMemoryStore) -> None:
        episodic, count = populated_store.list_by_type(MemoryType.EPISODIC)
        assert count == 1
        assert all(e.memory_type == MemoryType.EPISODIC for e in episodic)

    def test_list_all(self, populated_store: InMemoryMemoryStore) -> None:
        entries, total = populated_store.list_all()
        assert total == 5

    def test_list_all_empty(self, memory_store: InMemoryMemoryStore) -> None:
        entries, total = memory_store.list_all()
        assert total == 0
        assert entries == []

    def test_count(self, populated_store: InMemoryMemoryStore) -> None:
        assert populated_store.count() == 5

    def test_clear(self, populated_store: InMemoryMemoryStore) -> None:
        populated_store.clear()
        assert populated_store.count() == 0
        entries, total = populated_store.list_all()
        assert total == 0

    def test_thread_safety(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        errors: list[Exception] = []

        def _store() -> None:
            try:
                for _ in range(50):
                    entry = sample_episodic_entry.__class__(
                        memory_id="",
                        memory_type=MemoryType.EPISODIC,
                        version=1,
                        timestamp=__import__("datetime").datetime.now(),
                        source_module="test",
                        quality_score=0.8,
                        confidence=0.9,
                        lineage=MemoryLineage(created_by="test", created_at=__import__("datetime").datetime.now()),
                        tags=["t"],
                        metadata={},
                        content={"a": "b"},
                    )
                    memory_store.store(entry)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_store) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert memory_store.count() == 200

    def test_store_with_all_fields(self, memory_store: InMemoryMemoryStore) -> None:
        from datetime import datetime, timedelta

        lineage = MemoryLineage(
            created_by="test-user",
            created_at=datetime.now(),
            parent_ids=["parent-1"],
            module_chain=["mod1", "mod2"],
            reasoning_id="reason-1",
            debate_id="debate-1",
        )
        entry = MemoryEntry(
            memory_id="full-test-id",
            memory_type=MemoryType.PERFORMANCE,
            version=1,
            timestamp=datetime.now(),
            source_module="test_module",
            quality_score=0.95,
            confidence=0.99,
            lineage=lineage,
            tags=["full", "test"],
            metadata={"key": "value", "num": 42},
            content={"metrics": {"latency": 100}},
            embedding=[0.1, 0.2, 0.3],
            expires_at=datetime.now() + timedelta(days=1),
            status=MemoryStatus.ACTIVE,
        )
        mid = memory_store.store(entry)
        retrieved = memory_store.retrieve(mid)
        assert retrieved is not None
        assert retrieved.memory_id == "full-test-id"
        assert retrieved.embedding == [0.1, 0.2, 0.3]
        assert retrieved.expires_at is not None
        assert retrieved.lineage.reasoning_id == "reason-1"

    def test_multiple_versions(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        mid = memory_store.store(sample_episodic_entry)
        for i in range(3):
            sample_episodic_entry.memory_id = mid
            sample_episodic_entry.content["version"] = i
            memory_store.update(sample_episodic_entry)
        retrieved = memory_store.retrieve(mid)
        assert retrieved is not None
        assert retrieved.version == 4

    def test_list_by_type_limit_offset(self, populated_store: InMemoryMemoryStore) -> None:
        entries, total = populated_store.list_by_type(MemoryType.EPISODIC, limit=1, offset=0)
        assert len(entries) == 1
        assert total == 1

    def test_list_all_limit_offset(self, memory_store: InMemoryMemoryStore) -> None:
        from datetime import datetime

        from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage

        for i in range(10):
            e = MemoryEntry(
                memory_id=f"test-{i}",
                memory_type=MemoryType.EPISODIC,
                version=1,
                timestamp=datetime.now(),
                source_module="test",
                quality_score=0.5,
                confidence=0.5,
                lineage=MemoryLineage(created_by="t", created_at=datetime.now()),
                tags=["x"],
                metadata={},
                content={"idx": i},
            )
            memory_store.store(e)
        first_page, total = memory_store.list_all(limit=3, offset=0)
        assert len(first_page) == 3
        assert total == 10
        second_page, _ = memory_store.list_all(limit=3, offset=3)
        assert len(second_page) == 3
        assert second_page[0].memory_id == "test-3"

    def test_delete_twice(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        mid = memory_store.store(sample_episodic_entry)
        assert memory_store.delete(mid, soft=True) is True
        assert memory_store.delete(mid, soft=True) is True

    def test_store_update_cycle(self, memory_store: InMemoryMemoryStore) -> None:
        from datetime import datetime

        from duplicate_question_app._memory.interfaces import MemoryEntry

        e = MemoryEntry(
            memory_id="cycle-id",
            memory_type=MemoryType.SEMANTIC,
            version=1,
            timestamp=datetime.now(),
            source_module="test",
            quality_score=0.5,
            confidence=0.5,
            lineage=MemoryLineage(created_by="t", created_at=datetime.now()),
            tags=["x"],
            metadata={},
            content={"c": 1},
        )
        mid = memory_store.store(e)
        for i in range(5):
            e.memory_id = mid
            e.content["c"] = i
            memory_store.update(e)
        retrieved = memory_store.retrieve(mid)
        assert retrieved is not None
        assert retrieved.version == 6
        assert retrieved.content["c"] == 4

    def test_large_batch_store(self, memory_store: InMemoryMemoryStore) -> None:
        from datetime import datetime

        from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage

        for i in range(100):
            e = MemoryEntry(
                memory_id=f"batch-{i}",
                memory_type=MemoryType.EPISODIC,
                version=1,
                timestamp=datetime.now(),
                source_module="batch",
                quality_score=0.5,
                confidence=0.5,
                lineage=MemoryLineage(created_by="t", created_at=datetime.now()),
                tags=["batch"],
                metadata={},
                content={"i": i},
            )
            memory_store.store(e)
        assert memory_store.count() == 100

    def test_memory_id_collision_handling(self, memory_store: InMemoryMemoryStore) -> None:
        from datetime import datetime

        from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage

        e1 = MemoryEntry(
            memory_id="same-id",
            memory_type=MemoryType.EPISODIC,
            version=1,
            timestamp=datetime.now(),
            source_module="test",
            quality_score=0.5,
            confidence=0.5,
            lineage=MemoryLineage(created_by="t", created_at=datetime.now()),
            tags=["x"],
            metadata={},
            content={"a": 1},
        )
        e2 = MemoryEntry(
            memory_id="same-id",
            memory_type=MemoryType.EPISODIC,
            version=1,
            timestamp=datetime.now(),
            source_module="test",
            quality_score=0.6,
            confidence=0.6,
            lineage=MemoryLineage(created_by="t", created_at=datetime.now()),
            tags=["x"],
            metadata={},
            content={"a": 2},
        )
        memory_store.store(e1)
        memory_store.store(e2)
        retrieved = memory_store.retrieve("same-id")
        assert retrieved is not None
        assert retrieved.quality_score == 0.6

    def test_empty_store_statistics(self, memory_store: InMemoryMemoryStore) -> None:
        assert memory_store.count() == 0
        entries, total = memory_store.list_all()
        assert entries == []
        assert total == 0

    def test_retrieve_after_clear(self, memory_store: InMemoryMemoryStore, sample_episodic_entry: MemoryEntry) -> None:
        mid = memory_store.store(sample_episodic_entry)
        memory_store.clear()
        assert memory_store.retrieve(mid) is None
