from __future__ import annotations

import pytest

from ares.memory import (
    MemoryCompressor,
    MemoryContext,
    MemoryDomain,
    MemoryEntry,
    MemoryIndexer,
    MemoryManager,
    MemoryPersistence,
    MemoryRetriever,
    MemoryScorer,
    MemorySession,
    MemoryStore,
    MemoryTier,
    MemoryValue,
)


@pytest.fixture
def sample_tiers() -> list[MemoryTier]:
    return [MemoryTier.WORKING, MemoryTier.SHORT_TERM, MemoryTier.LONG_TERM]


@pytest.fixture
def sample_domains() -> list[MemoryDomain]:
    return [MemoryDomain.EPISODIC, MemoryDomain.SEMANTIC, MemoryDomain.REFLECTION]


@pytest.fixture
def sample_memory_value() -> MemoryValue:
    return MemoryValue(
        key="test_key",
        value={"data": 42},
        tier=MemoryTier.WORKING,
        domain=MemoryDomain.SEMANTIC,
        agent_id="agent-1",
        session_id="session-1",
        score=0.9,
    )


@pytest.fixture
def sample_entry() -> MemoryEntry:
    return MemoryEntry(
        memory_id="entry-1",
        key="test_key",
        value={"data": 42},
        tier=MemoryTier.WORKING,
        domain=MemoryDomain.SEMANTIC,
        agent_id="agent-1",
        session_id="session-1",
        score=0.9,
        tags=["test", "example"],
    )


@pytest.fixture
def sample_entries() -> list[MemoryEntry]:
    return [
        MemoryEntry(
            memory_id=f"entry-{i}",
            key=f"key_{i}",
            value={"index": i},
            tier=MemoryTier.WORKING if i < 3 else MemoryTier.SHORT_TERM,
            domain=MemoryDomain.SEMANTIC if i % 2 == 0 else MemoryDomain.EPISODIC,
            agent_id="agent-1",
            session_id="session-1",
            score=1.0 - i * 0.1,
            tags=["test"],
        )
        for i in range(5)
    ]


@pytest.fixture
def memory_persistence(tmp_path) -> MemoryPersistence:
    return MemoryPersistence(base_path=str(tmp_path / ".ares_memory"))


@pytest.fixture
def memory_store(memory_persistence) -> MemoryStore:
    return MemoryStore(persistence=memory_persistence)


@pytest.fixture
def memory_indexer() -> MemoryIndexer:
    return MemoryIndexer()


@pytest.fixture
def memory_scorer() -> MemoryScorer:
    return MemoryScorer()


@pytest.fixture
def memory_retriever(memory_store, memory_indexer, memory_scorer) -> MemoryRetriever:
    return MemoryRetriever(store=memory_store, indexer=memory_indexer, scorer=memory_scorer)


@pytest.fixture
def memory_compressor() -> MemoryCompressor:
    return MemoryCompressor()


@pytest.fixture
def memory_manager(memory_persistence) -> MemoryManager:
    mgr = MemoryManager(persistence_base_path=memory_persistence.base_path)
    return mgr


@pytest.fixture
def memory_session() -> MemorySession:
    return MemorySession(session_id="test-session-1", ttl_seconds=300.0)


@pytest.fixture
def memory_context() -> MemoryContext:
    return MemoryContext(
        agent_id="agent-1",
        workflow_id="workflow-1",
        trace_id="trace-1",
        session_id="session-1",
    )
