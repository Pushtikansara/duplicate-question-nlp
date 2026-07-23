from __future__ import annotations

from pathlib import Path

from ares.memory import (
    MemoryDomain,
    MemoryManager,
    MemoryQuery,
    MemoryTier,
)


class TestMemoryIntegration:
    def test_full_lifecycle(self, tmp_path: Path) -> None:
        mgr = MemoryManager(persistence_base_path=str(tmp_path / "mem"))

        entry = mgr.store(
            "lifecycle_key",
            {"phase": "test"},
            tier=MemoryTier.WORKING,
            domain=MemoryDomain.SEMANTIC,
            agent_id="agent-1",
            tags=["integration"],
        )
        assert entry.key == "lifecycle_key"

        retrieved = mgr.get(entry.memory_id)
        assert retrieved.value == {"phase": "test"}

        result = mgr.query(MemoryQuery(tier=MemoryTier.WORKING))
        assert result.total_count >= 1

        mgr.delete(entry.memory_id)

        stats = mgr.get_stats()
        assert isinstance(stats.total_entries, int)

    def test_session_with_memory(self, tmp_path: Path) -> None:
        mgr = MemoryManager(persistence_base_path=str(tmp_path / "mem_sesh"))
        session = mgr.create_session(ttl_seconds=300.0)

        session.set_working("wm_key", "wm_value")
        assert session.get_working("wm_key") == "wm_value"

        mv = session.to_memory_value("session_data", {"s": 1})
        entry = mgr.store_value(mv)
        assert entry.session_id == session.session_id

        mgr.close_session(session.session_id)
        assert mgr.get_session(session.session_id) is None

    def test_episodic_to_semantic_flow(self, tmp_path: Path) -> None:
        mgr = MemoryManager(persistence_base_path=str(tmp_path / "mem_flow"))

        ep = mgr.store_episodic("trip_paris", "went to paris", agent_id="agent-1", tags=["travel"])
        assert ep.domain == MemoryDomain.EPISODIC

        sem = mgr.store_semantic("fact_paris", "paris is capital", agent_id="agent-1", tags=["knowledge"])
        assert sem.domain == MemoryDomain.SEMANTIC

        ref = mgr.store_reflection("learned_paris", "user likes travel", agent_id="agent-1", tags=["insight"])
        assert ref.domain == MemoryDomain.REFLECTION

        results = mgr.search("paris")
        assert len(results) >= 1

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        base = str(tmp_path / "persist_cross")
        mgr1 = MemoryManager(persistence_base_path=base)
        mgr1.store("persist_key", "hello", tier=MemoryTier.LONG_TERM)

        mgr2 = MemoryManager(persistence_base_path=base)
        loaded = mgr2.load_all()
        found = False
        for tier_entries in loaded.values():
            for e in tier_entries:
                if e.key == "persist_key":
                    assert e.value == "hello"
                    found = True
        assert found

    def test_compression_workflow(self, tmp_path: Path) -> None:
        mgr = MemoryManager(persistence_base_path=str(tmp_path / "compress"))
        session = mgr.create_session(ttl_seconds=300.0)

        mgr.store(
            "hot_data",
            "important",
            tier=MemoryTier.WORKING,
            domain=MemoryDomain.SEMANTIC,
            agent_id="agent-1",
            session_id=session.session_id,
        )

        promoted = mgr.compress_session_working(session.session_id)
        assert len(promoted) >= 1
        assert promoted[0].tier == MemoryTier.SHORT_TERM

    def test_clear(self, tmp_path: Path) -> None:
        mgr = MemoryManager(persistence_base_path=str(tmp_path / "clear"))
        mgr.store("a", 1)
        mgr.store("b", 2)
        assert mgr.clear() >= 2
        assert mgr.get_stats().total_entries == 0
