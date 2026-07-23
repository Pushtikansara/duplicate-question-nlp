from __future__ import annotations

from ares.memory import MemoryDomain, MemoryEntry, MemoryIndexer, MemoryTier


class TestMemoryIndexer:
    def test_index_and_find_by_key(self, memory_indexer: MemoryIndexer, sample_entry: MemoryEntry) -> None:
        memory_indexer.index_entry(sample_entry)
        ids = memory_indexer.find_by_key("test_key")
        assert "entry-1" in ids

    def test_find_by_agent(self, memory_indexer: MemoryIndexer, sample_entry: MemoryEntry) -> None:
        memory_indexer.index_entry(sample_entry)
        ids = memory_indexer.find_by_agent("agent-1")
        assert "entry-1" in ids

    def test_find_by_session(self, memory_indexer: MemoryIndexer, sample_entry: MemoryEntry) -> None:
        memory_indexer.index_entry(sample_entry)
        ids = memory_indexer.find_by_session("session-1")
        assert "entry-1" in ids

    def test_find_by_tag(self, memory_indexer: MemoryIndexer, sample_entry: MemoryEntry) -> None:
        memory_indexer.index_entry(sample_entry)
        ids = memory_indexer.find_by_tag("test")
        assert "entry-1" in ids

    def test_find_by_tier(self, memory_indexer: MemoryIndexer, sample_entry: MemoryEntry) -> None:
        memory_indexer.index_entry(sample_entry)
        ids = memory_indexer.find_by_tier("WORKING")
        assert "entry-1" in ids

    def test_find_by_domain(self, memory_indexer: MemoryIndexer, sample_entry: MemoryEntry) -> None:
        memory_indexer.index_entry(sample_entry)
        ids = memory_indexer.find_by_domain("SEMANTIC")
        assert "entry-1" in ids

    def test_remove_entry(self, memory_indexer: MemoryIndexer, sample_entry: MemoryEntry) -> None:
        memory_indexer.index_entry(sample_entry)
        memory_indexer.remove_entry(sample_entry)
        assert memory_indexer.find_by_key("test_key") == set()

    def test_clear(self, memory_indexer: MemoryIndexer, sample_entry: MemoryEntry) -> None:
        memory_indexer.index_entry(sample_entry)
        memory_indexer.clear()
        assert memory_indexer.find_by_key("test_key") == set()

    def test_multiple_entries(self, memory_indexer: MemoryIndexer) -> None:
        for i in range(5):
            e = MemoryEntry(
                memory_id=f"e{i}",
                key=f"key_{i}",
                value=i,
                tier=MemoryTier.WORKING,
                domain=MemoryDomain.SEMANTIC,
                agent_id="agent-1",
                tags=["common"],
            )
            memory_indexer.index_entry(e)
        assert len(memory_indexer.find_by_tag("common")) == 5
        assert len(memory_indexer.find_by_agent("agent-1")) == 5
