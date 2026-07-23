from __future__ import annotations

import pytest

from ares.memory import MemoryDomain, MemoryQuery, MemoryStore, MemoryTier
from ares.memory.exceptions import MemoryNotFoundError


class TestMemoryStore:
    def test_store_and_get(self, memory_store: MemoryStore) -> None:
        entry = memory_store.store("my_key", {"data": 123})
        assert entry.key == "my_key"
        assert entry.value == {"data": 123}

        retrieved = memory_store.get(entry.memory_id)
        assert retrieved.memory_id == entry.memory_id
        assert retrieved.key == "my_key"

    def test_get_not_found(self, memory_store: MemoryStore) -> None:
        with pytest.raises(MemoryNotFoundError):
            memory_store.get("no_such_id")

    def test_store_with_all_params(self, memory_store: MemoryStore) -> None:
        entry = memory_store.store(
            key="full_key",
            value={"n": 1},
            tier=MemoryTier.LONG_TERM,
            domain=MemoryDomain.REFLECTION,
            ttl_seconds=3600.0,
            metadata={"source": "test"},
            agent_id="agent-1",
            session_id="session-1",
            score=0.8,
            tags=["a", "b"],
        )
        assert entry.tier == MemoryTier.LONG_TERM
        assert entry.domain == MemoryDomain.REFLECTION
        assert entry.agent_id == "agent-1"

    def test_delete(self, memory_store: MemoryStore) -> None:
        entry = memory_store.store("del_key", "val")
        assert memory_store.delete(entry.memory_id) is True
        with pytest.raises(MemoryNotFoundError):
            memory_store.get(entry.memory_id)

    def test_delete_not_found(self, memory_store: MemoryStore) -> None:
        assert memory_store.delete("no_such_id") is False

    def test_query_default(self, memory_store: MemoryStore) -> None:
        for i in range(5):
            memory_store.store(f"key_{i}", i)
        result = memory_store.query(MemoryQuery())
        assert result.total_count >= 5

    def test_query_filter_key(self, memory_store: MemoryStore) -> None:
        memory_store.store("target", 42)
        memory_store.store("other", 99)
        result = memory_store.query(MemoryQuery(key="target"))
        assert result.total_count == 1
        assert result.entries[0].value == 42

    def test_query_filter_tier(self, memory_store: MemoryStore) -> None:
        memory_store.store("w", "working", tier=MemoryTier.WORKING)
        memory_store.store("l", "long", tier=MemoryTier.LONG_TERM)
        result = memory_store.query(MemoryQuery(tier=MemoryTier.WORKING))
        assert result.total_count == 1
        assert result.entries[0].key == "w"

    def test_query_limit_offset(self, memory_store: MemoryStore) -> None:
        for i in range(10):
            memory_store.store(f"k_{i}", i)
        result = memory_store.query(MemoryQuery(limit=3, offset=0))
        assert len(result.entries) <= 3

    def test_update_access(self, memory_store: MemoryStore) -> None:
        entry = memory_store.store("acc_key", "val")
        assert entry.access_count == 0
        memory_store.update_access(entry.memory_id)
        assert memory_store.get(entry.memory_id).access_count == 1

    def test_get_stats(self, memory_store: MemoryStore) -> None:
        memory_store.store("a", 1, tier=MemoryTier.WORKING, domain=MemoryDomain.SEMANTIC)
        memory_store.store("b", 2, tier=MemoryTier.LONG_TERM, domain=MemoryDomain.EPISODIC)
        stats = memory_store.get_stats()
        assert stats.total_entries >= 2
        assert stats.entries_by_tier.get("WORKING", 0) >= 1
        assert stats.entries_by_tier.get("LONG_TERM", 0) >= 1

    def test_clear(self, memory_store: MemoryStore) -> None:
        memory_store.store("a", 1)
        memory_store.store("b", 2)
        count = memory_store.clear()
        assert count >= 2
        result = memory_store.query(MemoryQuery())
        assert result.total_count == 0
