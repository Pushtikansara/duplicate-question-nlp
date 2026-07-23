from __future__ import annotations

from ares.memory import MemoryDomain, MemoryQuery, MemoryTier


class TestMemoryRetriever:
    def _store_and_index(self, memory_retriever, **kwargs):
        entry = memory_retriever._store.store(**kwargs)
        memory_retriever._indexer.index_entry(entry)
        return entry

    def test_retrieve(self, memory_retriever, sample_entries) -> None:
        for e in sample_entries:
            self._store_and_index(
                memory_retriever,
                key=e.key,
                value=e.value,
                tier=e.tier,
                domain=e.domain,
                agent_id=e.agent_id,
                session_id=e.session_id,
                score=e.score,
                tags=e.tags,
            )

        result = memory_retriever.retrieve(MemoryQuery())
        assert result.total_count == len(sample_entries)

    def test_retrieve_by_key(self, memory_retriever, sample_entries) -> None:
        for e in sample_entries:
            self._store_and_index(
                memory_retriever,
                key=e.key,
                value=e.value,
                tier=e.tier,
                domain=e.domain,
                agent_id=e.agent_id,
                tags=e.tags,
            )

        entries = memory_retriever.retrieve_by_key("key_0")
        assert len(entries) >= 1
        assert entries[0].key == "key_0"

    def test_retrieve_by_agent(self, memory_retriever, sample_entries) -> None:
        for e in sample_entries:
            self._store_and_index(
                memory_retriever,
                key=e.key,
                value=e.value,
                tier=e.tier,
                domain=e.domain,
                agent_id=e.agent_id,
                tags=e.tags,
            )

        entries = memory_retriever.retrieve_by_agent("agent-1")
        assert len(entries) == len(sample_entries)

    def test_retrieve_by_session(self, memory_retriever, sample_entries) -> None:
        for e in sample_entries:
            self._store_and_index(
                memory_retriever,
                key=e.key,
                value=e.value,
                tier=e.tier,
                domain=e.domain,
                agent_id=e.agent_id,
                session_id=e.session_id,
                tags=e.tags,
            )

        entries = memory_retriever.retrieve_by_session("session-1")
        assert len(entries) == len(sample_entries)

    def test_retrieve_recent(self, memory_retriever, sample_entries) -> None:
        for e in sample_entries:
            memory_retriever._store.store(
                key=e.key,
                value=e.value,
                tier=e.tier,
                domain=e.domain,
                agent_id=e.agent_id,
                tags=e.tags,
            )
            memory_retriever._indexer.index_entry(e)

        recent = memory_retriever.retrieve_recent(count=3)
        assert len(recent) <= 3

    def test_search(self, memory_retriever) -> None:
        memory_retriever._store.store(
            key="unique_target", value=100, tier=MemoryTier.WORKING, domain=MemoryDomain.SEMANTIC
        )
        memory_retriever._store.store(key="other", value=200, tier=MemoryTier.WORKING, domain=MemoryDomain.SEMANTIC)
        results = memory_retriever.search("unique_target")
        assert len(results) == 1
        assert results[0].value == 100
