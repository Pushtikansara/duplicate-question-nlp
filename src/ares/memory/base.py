from __future__ import annotations

import logging
from typing import Any

from ares.memory.compressor import MemoryCompressor
from ares.memory.context import MemoryContext
from ares.memory.indexer import MemoryIndexer
from ares.memory.persistence import MemoryPersistence
from ares.memory.retriever import MemoryRetriever
from ares.memory.scorer import MemoryScorer
from ares.memory.session import MemorySession
from ares.memory.store import MemoryStore
from ares.memory.types import MemoryDomain, MemoryEntry, MemoryQuery, MemoryResult, MemoryStats, MemoryTier, MemoryValue

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(
        self,
        persistence_base_path: str = "",
    ) -> None:
        self._persistence = MemoryPersistence(base_path=persistence_base_path)
        self._store = MemoryStore(persistence=self._persistence)
        self._indexer = MemoryIndexer()
        self._scorer = MemoryScorer()
        self._retriever = MemoryRetriever(store=self._store, indexer=self._indexer, scorer=self._scorer)
        self._compressor = MemoryCompressor()
        self._sessions: dict[str, MemorySession] = {}

    @property
    def store_accessor(self) -> MemoryStore:
        return self._store

    @property
    def retriever(self) -> MemoryRetriever:
        return self._retriever

    @property
    def scorer(self) -> MemoryScorer:
        return self._scorer

    @property
    def indexer(self) -> MemoryIndexer:
        return self._indexer

    @property
    def compressor(self) -> MemoryCompressor:
        return self._compressor

    @property
    def persistence(self) -> MemoryPersistence:
        return self._persistence

    # --- Session management ---

    def create_session(
        self,
        context: MemoryContext | None = None,
        ttl_seconds: float = 300.0,
    ) -> MemorySession:
        session = MemorySession(context=context, ttl_seconds=ttl_seconds)
        self._sessions[session.session_id] = session
        logger.debug("Created memory session '%s'", session.session_id)
        return session

    def get_session(self, session_id: str) -> MemorySession | None:
        session = self._sessions.get(session_id)
        if session is not None and not session.is_active:
            self._sessions.pop(session_id, None)
            return None
        return session

    def close_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is not None:
            session.close()

    def active_session_count(self) -> int:
        return sum(1 for s in self._sessions.values() if s.is_active)

    def cleanup_expired_sessions(self) -> int:
        expired = [sid for sid, session in self._sessions.items() if not session.is_active]
        for sid in expired:
            self._sessions.pop(sid, None)
        return len(expired)

    # --- Store operations ---

    def store(
        self,
        key: str,
        value: Any,
        tier: MemoryTier = MemoryTier.WORKING,
        domain: MemoryDomain = MemoryDomain.SEMANTIC,
        ttl_seconds: float | None = None,
        metadata: dict[str, Any] | None = None,
        agent_id: str = "",
        session_id: str = "",
        score: float = 1.0,
        tags: list[str] | None = None,
    ) -> MemoryEntry:
        entry = self._store.store(
            key=key,
            value=value,
            tier=tier,
            domain=domain,
            ttl_seconds=ttl_seconds,
            metadata=metadata,
            agent_id=agent_id,
            session_id=session_id,
            score=score,
            tags=tags,
        )
        self._indexer.index_entry(entry)
        return entry

    def store_value(self, value: MemoryValue) -> MemoryEntry:
        return self.store(
            key=value.key,
            value=value.value,
            tier=value.tier,
            domain=value.domain,
            ttl_seconds=value.ttl_seconds,
            metadata=value.metadata,
            agent_id=value.agent_id,
            session_id=value.session_id,
            score=value.score,
        )

    def get(self, memory_id: str) -> MemoryEntry:
        entry = self._store.get(memory_id)
        self._store.update_access(memory_id)
        return entry

    def delete(self, memory_id: str) -> bool:
        try:
            entry = self._store.get(memory_id)
            self._indexer.remove_entry(entry)
        except Exception:
            pass
        return self._store.delete(memory_id)

    def query(self, query: MemoryQuery) -> MemoryResult:
        return self._retriever.retrieve(query)

    def search(self, query_str: str, tier: MemoryTier | None = None, limit: int = 20) -> list[MemoryEntry]:
        return self._retriever.search(query_str, tier=tier, limit=limit)

    def get_stats(self) -> MemoryStats:
        return self._store.get_stats()

    def clear(self) -> int:
        self._indexer.clear()
        return self._store.clear()

    # --- Compression & consolidation ---

    def compress_session_working(self, session_id: str) -> list[MemoryEntry]:
        session = self.get_session(session_id)
        if session is None:
            logger.warning("Cannot compress: session '%s' not found", session_id)
            return []
        ids = self._indexer.find_by_session(session_id) & self._indexer.find_by_tier(MemoryTier.WORKING.name)
        entries: list[MemoryEntry] = []
        for mid in ids:
            try:
                entries.append(self._store.get(mid))
            except Exception:
                continue
        promoted = self._compressor.compress_working_to_short_term(entries)
        for p in promoted:
            self._store.store(
                key=p.key,
                value=p.value,
                tier=p.tier,
                domain=p.domain,
                ttl_seconds=p.ttl_seconds,
                metadata=p.metadata,
                agent_id=p.agent_id,
                session_id=p.session_id,
                score=p.score,
                tags=p.tags,
            )
            self._indexer.index_entry(p)
        return promoted

    def consolidate_short_to_long_term(self, session_id: str) -> list[MemoryEntry]:
        session = self.get_session(session_id)
        if session is None:
            logger.warning("Cannot consolidate: session '%s' not found", session_id)
            return []
        ids = self._indexer.find_by_session(session_id) & self._indexer.find_by_tier(MemoryTier.SHORT_TERM.name)
        entries: list[MemoryEntry] = []
        for mid in ids:
            try:
                entries.append(self._store.get(mid))
            except Exception:
                continue
        consolidated = self._compressor.compress_short_to_long_term(entries)
        for c in consolidated:
            self._store.store(
                key=c.key,
                value=c.value,
                tier=c.tier,
                domain=c.domain,
                ttl_seconds=c.ttl_seconds,
                metadata=c.metadata,
                agent_id=c.agent_id,
                session_id=c.session_id,
                score=c.score,
                tags=c.tags,
            )
            self._indexer.index_entry(c)
        return consolidated

    # --- Persistence ---

    def load_all(self) -> dict[MemoryTier, list[MemoryEntry]]:
        return self._persistence.load_all()

    def save_to_disk(self, tier: MemoryTier | None = None) -> int:
        if tier is not None:
            ids = self._indexer.find_by_tier(tier.name)
        else:
            all_ids = set()
            for t in MemoryTier:
                all_ids |= self._indexer.find_by_tier(t.name)
            ids = all_ids
        saved = 0
        for mid in ids:
            try:
                entry = self._store.get(mid)
                self._persistence.save_entry(entry)
                saved += 1
            except Exception:
                continue
        return saved

    # --- Bulk operations ---

    def store_episodic(
        self,
        key: str,
        value: Any,
        agent_id: str = "",
        session_id: str = "",
        tags: list[str] | None = None,
    ) -> MemoryEntry:
        return self.store(
            key=key,
            value=value,
            tier=MemoryTier.SHORT_TERM,
            domain=MemoryDomain.EPISODIC,
            ttl_seconds=86400.0,
            agent_id=agent_id,
            session_id=session_id,
            tags=tags,
        )

    def store_semantic(
        self,
        key: str,
        value: Any,
        agent_id: str = "",
        session_id: str = "",
        tags: list[str] | None = None,
    ) -> MemoryEntry:
        return self.store(
            key=key,
            value=value,
            tier=MemoryTier.LONG_TERM,
            domain=MemoryDomain.SEMANTIC,
            ttl_seconds=None,
            agent_id=agent_id,
            session_id=session_id,
            tags=tags,
        )

    def store_reflection(
        self,
        key: str,
        value: Any,
        agent_id: str = "",
        session_id: str = "",
        tags: list[str] | None = None,
    ) -> MemoryEntry:
        return self.store(
            key=key,
            value=value,
            tier=MemoryTier.LONG_TERM,
            domain=MemoryDomain.REFLECTION,
            ttl_seconds=None,
            agent_id=agent_id,
            session_id=session_id,
            tags=tags,
        )
