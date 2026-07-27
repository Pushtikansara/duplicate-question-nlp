from __future__ import annotations

import logging

from ares.memory.indexer import MemoryIndexer
from ares.memory.scorer import MemoryScorer
from ares.memory.store import MemoryStore
from ares.memory.types import MemoryEntry, MemoryQuery, MemoryResult, MemoryTier

logger = logging.getLogger(__name__)


class MemoryRetriever:
    def __init__(
        self,
        store: MemoryStore,
        indexer: MemoryIndexer | None = None,
        scorer: MemoryScorer | None = None,
    ) -> None:
        self._store = store
        self._indexer = indexer or MemoryIndexer()
        self._scorer = scorer or MemoryScorer()

    def retrieve(self, query: MemoryQuery) -> MemoryResult:
        return self._store.query(query)

    def retrieve_by_key(self, key: str, tier: MemoryTier | None = None) -> list[MemoryEntry]:
        ids = self._indexer.find_by_key(key)
        entries: list[MemoryEntry] = []
        for mid in ids:
            try:
                entry = self._store.get(mid)
                if tier is None or entry.tier == tier:
                    entries.append(entry)
            except Exception as exc:
                logger.debug("Failed to retrieve memory entry '%s': %s", mid, exc)
                continue
        return entries

    def retrieve_by_agent(
        self,
        agent_id: str,
        tier: MemoryTier | None = None,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        ids = self._indexer.find_by_agent(agent_id)
        return self._resolve_and_filter(ids, tier, limit)

    def retrieve_by_session(
        self,
        session_id: str,
        tier: MemoryTier | None = None,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        ids = self._indexer.find_by_session(session_id)
        return self._resolve_and_filter(ids, tier, limit)

    def retrieve_working_memory(self, agent_id: str) -> list[MemoryEntry]:
        return self._resolve_and_filter(
            self._indexer.find_by_tier(MemoryTier.WORKING.name) & self._indexer.find_by_agent(agent_id),
            None,
            100,
        )

    def retrieve_recent(
        self,
        count: int = 10,
        tier: MemoryTier | None = None,
    ) -> list[MemoryEntry]:
        query = MemoryQuery(tier=tier, limit=count)
        result = self._store.query(query)
        return result.entries

    def search(
        self,
        query_str: str,
        tier: MemoryTier | None = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        query = MemoryQuery(key=query_str, tier=tier, limit=limit)
        return self._store.query(query).entries

    def _resolve_and_filter(
        self,
        ids: set[str],
        tier: MemoryTier | None = None,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for mid in ids:
            if len(entries) >= limit:
                break
            try:
                entry = self._store.get(mid)
                if tier is None or entry.tier == tier:
                    entries.append(entry)
            except Exception as exc:
                logger.debug("Failed to resolve memory entry '%s': %s", mid, exc)
                continue
        entries.sort(key=lambda e: e.score, reverse=True)
        return entries[:limit]
