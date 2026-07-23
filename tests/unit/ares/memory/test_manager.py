from __future__ import annotations

from ares.memory import MemoryDomain, MemoryManager, MemoryQuery, MemoryTier


class TestMemoryManager:
    def test_store_and_get(self, memory_manager: MemoryManager) -> None:
        entry = memory_manager.store("k1", "v1")
        retrieved = memory_manager.get(entry.memory_id)
        assert retrieved.key == "k1"
        assert retrieved.value == "v1"

    def test_store_with_tier_and_domain(self, memory_manager: MemoryManager) -> None:
        entry = memory_manager.store(
            "k2",
            {"x": 1},
            tier=MemoryTier.LONG_TERM,
            domain=MemoryDomain.REFLECTION,
            agent_id="agent-2",
            tags=["important"],
        )
        assert entry.tier == MemoryTier.LONG_TERM
        assert entry.domain == MemoryDomain.REFLECTION
        assert entry.agent_id == "agent-2"

    def test_store_value(self, memory_manager: MemoryManager, sample_memory_value) -> None:
        entry = memory_manager.store_value(sample_memory_value)
        assert entry.key == "test_key"
        assert entry.value == {"data": 42}

    def test_delete(self, memory_manager: MemoryManager) -> None:
        entry = memory_manager.store("del_me", "x")
        assert memory_manager.delete(entry.memory_id) is True

    def test_query(self, memory_manager: MemoryManager) -> None:
        memory_manager.store("qa", 1)
        memory_manager.store("qb", 2)
        result = memory_manager.query(MemoryQuery())
        assert result.total_count >= 2

    def test_search(self, memory_manager: MemoryManager) -> None:
        memory_manager.store("unique_key_for_search", 99)
        results = memory_manager.search("unique_key_for_search")
        assert len(results) == 1
        assert results[0].value == 99

    def test_get_stats(self, memory_manager: MemoryManager) -> None:
        memory_manager.store("s1", 1, tier=MemoryTier.WORKING, domain=MemoryDomain.SEMANTIC)
        memory_manager.store("s2", 2, tier=MemoryTier.LONG_TERM, domain=MemoryDomain.EPISODIC)
        stats = memory_manager.get_stats()
        assert stats.total_entries >= 2

    def test_clear(self, memory_manager: MemoryManager) -> None:
        memory_manager.store("c1", 1)
        memory_manager.store("c2", 2)
        count = memory_manager.clear()
        assert count >= 2

    def test_create_and_get_session(self, memory_manager: MemoryManager) -> None:
        session = memory_manager.create_session(ttl_seconds=300.0)
        assert memory_manager.get_session(session.session_id) is not None

    def test_close_session(self, memory_manager: MemoryManager) -> None:
        session = memory_manager.create_session(ttl_seconds=300.0)
        memory_manager.close_session(session.session_id)
        assert memory_manager.get_session(session.session_id) is None

    def test_active_session_count(self, memory_manager: MemoryManager) -> None:
        assert memory_manager.active_session_count() == 0
        memory_manager.create_session(ttl_seconds=300.0)
        memory_manager.create_session(ttl_seconds=300.0)
        assert memory_manager.active_session_count() == 2

    def test_store_episodic(self, memory_manager: MemoryManager) -> None:
        entry = memory_manager.store_episodic("ep_key", {"event": "test"}, agent_id="agent-1")
        assert entry.tier == MemoryTier.SHORT_TERM
        assert entry.domain == MemoryDomain.EPISODIC
        assert entry.ttl_seconds == 86400.0

    def test_store_semantic(self, memory_manager: MemoryManager) -> None:
        entry = memory_manager.store_semantic("sem_key", {"concept": "python"}, agent_id="agent-1")
        assert entry.tier == MemoryTier.LONG_TERM
        assert entry.domain == MemoryDomain.SEMANTIC
        assert entry.ttl_seconds is None

    def test_store_reflection(self, memory_manager: MemoryManager) -> None:
        entry = memory_manager.store_reflection("ref_key", {"insight": "learned"}, agent_id="agent-1")
        assert entry.tier == MemoryTier.LONG_TERM
        assert entry.domain == MemoryDomain.REFLECTION

    def test_save_to_disk(self, memory_manager: MemoryManager) -> None:
        memory_manager.store("disk1", 1)
        memory_manager.store("disk2", 2)
        saved = memory_manager.save_to_disk()
        assert saved >= 2

    def test_load_all(self, memory_manager: MemoryManager) -> None:
        memory_manager.store("load1", 1)
        memory_manager.save_to_disk()
        loaded = memory_manager.load_all()
        assert len(loaded) == len(MemoryTier)
