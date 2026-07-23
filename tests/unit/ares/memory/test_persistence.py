from __future__ import annotations

from ares.memory import MemoryDomain, MemoryEntry, MemoryPersistence, MemoryTier


class TestMemoryPersistence:
    def test_save_and_load_entry(self, memory_persistence: MemoryPersistence) -> None:
        entry = MemoryEntry(
            memory_id="p001",
            key="persist_key",
            value={"hello": "world"},
            tier=MemoryTier.WORKING,
            domain=MemoryDomain.SEMANTIC,
            agent_id="agent-1",
            tags=["test"],
        )
        path = memory_persistence.save_entry(entry)
        assert path.endswith("p001.json")

        loaded = memory_persistence.load_entry("p001", MemoryTier.WORKING)
        assert loaded is not None
        assert loaded.memory_id == "p001"
        assert loaded.key == "persist_key"
        assert loaded.value == {"hello": "world"}

    def test_load_nonexistent(self, memory_persistence: MemoryPersistence) -> None:
        loaded = memory_persistence.load_entry("nonexistent", MemoryTier.WORKING)
        assert loaded is None

    def test_save_and_load_entries(self, memory_persistence: MemoryPersistence) -> None:
        entries = [
            MemoryEntry(memory_id=f"m{i}", key=f"k{i}", value=i, tier=MemoryTier.WORKING, domain=MemoryDomain.SEMANTIC)
            for i in range(3)
        ]
        memory_persistence.save_entries(entries)
        loaded = memory_persistence.load_entries(MemoryTier.WORKING)
        assert len(loaded) == 3

    def test_delete_entry(self, memory_persistence: MemoryPersistence) -> None:
        entry = MemoryEntry(
            memory_id="del_me",
            key="del_key",
            value="x",
            tier=MemoryTier.WORKING,
            domain=MemoryDomain.SEMANTIC,
        )
        memory_persistence.save_entry(entry)
        assert memory_persistence.entry_exists("del_me", MemoryTier.WORKING) is True
        assert memory_persistence.delete_entry("del_me", MemoryTier.WORKING) is True
        assert memory_persistence.entry_exists("del_me", MemoryTier.WORKING) is False

    def test_delete_nonexistent(self, memory_persistence: MemoryPersistence) -> None:
        assert memory_persistence.delete_entry("no_such_id", MemoryTier.WORKING) is False

    def test_clear_tier(self, memory_persistence: MemoryPersistence) -> None:
        for i in range(5):
            e = MemoryEntry(
                memory_id=f"c{i}",
                key=f"k{i}",
                value=i,
                tier=MemoryTier.WORKING,
                domain=MemoryDomain.SEMANTIC,
            )
            memory_persistence.save_entry(e)
        assert memory_persistence.clear_tier(MemoryTier.WORKING) == 5
        assert memory_persistence.count_entries(MemoryTier.WORKING) == 0

    def test_clear_all(self, memory_persistence: MemoryPersistence) -> None:
        for tier in MemoryTier:
            e = MemoryEntry(
                memory_id=f"{tier.name}_1",
                key="k",
                value=1,
                tier=tier,
                domain=MemoryDomain.SEMANTIC,
            )
            memory_persistence.save_entry(e)
        cleared = memory_persistence.clear_all()
        assert sum(cleared.values()) == len(MemoryTier)

    def test_load_all(self, memory_persistence: MemoryPersistence) -> None:
        for i, tier in enumerate(MemoryTier):
            e = MemoryEntry(
                memory_id=f"a{i}",
                key=f"k{i}",
                value=i,
                tier=tier,
                domain=MemoryDomain.SEMANTIC,
            )
            memory_persistence.save_entry(e)
        all_data = memory_persistence.load_all()
        assert set(all_data.keys()) == set(MemoryTier)
        total = sum(len(v) for v in all_data.values())
        assert total == len(MemoryTier)

    def test_count_entries(self, memory_persistence: MemoryPersistence) -> None:
        assert memory_persistence.count_entries(MemoryTier.WORKING) == 0
        e = MemoryEntry(memory_id="cnt1", key="k", value=1, tier=MemoryTier.WORKING, domain=MemoryDomain.SEMANTIC)
        memory_persistence.save_entry(e)
        assert memory_persistence.count_entries(MemoryTier.WORKING) == 1
