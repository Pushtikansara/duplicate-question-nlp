from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from ares.memory.exceptions import MemoryNotFoundError
from ares.memory.persistence import MemoryPersistence
from ares.memory.types import MemoryDomain, MemoryEntry, MemoryQuery, MemoryResult, MemoryStats, MemoryTier
from ares.metrics import MetricsRegistry

logger = logging.getLogger(__name__)


DEFAULT_TIER_CAPACITIES: dict[MemoryTier, int] = {
    MemoryTier.WORKING: 500,
    MemoryTier.SHORT_TERM: 1000,
    MemoryTier.LONG_TERM: 5000,
}


class MemoryStore:
    def __init__(
        self,
        persistence: MemoryPersistence | None = None,
        tier_capacities: dict[MemoryTier, int] | None = None,
    ) -> None:
        self._persistence = persistence or MemoryPersistence()
        self._in_memory: dict[str, MemoryEntry] = {}
        self._tier_capacities = dict(DEFAULT_TIER_CAPACITIES)
        if tier_capacities:
            self._tier_capacities.update(tier_capacities)
        self._eviction_count: int = 0

    def _evict_if_needed(self, tier: MemoryTier) -> None:
        capacity = self._tier_capacities.get(tier, 1000)
        tier_entries = [e for e in self._in_memory.values() if e.tier == tier]
        metrics = MetricsRegistry()
        while len(tier_entries) >= capacity:
            tier_entries.sort(key=lambda e: e.timestamp)
            oldest = tier_entries.pop(0)
            self._in_memory.pop(oldest.memory_id, None)
            self._eviction_count += 1
            metrics.increment("memory.evictions", tags={"tier": tier.name})

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
        for existing in self._in_memory.values():
            if existing.key == key and existing.tier == tier:
                existing.value = value
                existing.score = score
                existing.tags = list(set(existing.tags + (tags or [])))
                if metadata:
                    existing.metadata.update(metadata)
                if session_id:
                    existing.session_id = session_id
                try:
                    self._persistence.save_entry(existing)
                except Exception as e:
                    logger.error("Failed to persist deduplicated entry '%s': %s", existing.memory_id, e)
                return existing

        MetricsRegistry().increment("memory.stores", tags={"tier": tier.name})
        entry = MemoryEntry(
            memory_id=str(uuid.uuid4()),
            key=key,
            value=value,
            tier=tier,
            domain=domain,
            ttl_seconds=ttl_seconds,
            metadata=metadata or {},
            agent_id=agent_id,
            session_id=session_id,
            score=score,
            tags=tags or [],
        )
        self._evict_if_needed(tier)
        self._in_memory[entry.memory_id] = entry
        try:
            self._persistence.save_entry(entry)
        except Exception as e:
            logger.error("Failed to persist entry '%s': %s", entry.memory_id, e)
        return entry

    def get(self, memory_id: str) -> MemoryEntry:
        entry = self._in_memory.get(memory_id)
        if entry is not None:
            return entry
        for tier in MemoryTier:
            persisted = self._persistence.load_entry(memory_id, tier)
            if persisted is not None:
                self._in_memory[persisted.memory_id] = persisted
                return persisted
        raise MemoryNotFoundError(detail=f"Memory entry '{memory_id}' not found")

    def update_access(self, memory_id: str) -> None:
        entry = self._in_memory.get(memory_id)
        if entry:
            entry.access_count += 1

    def delete(self, memory_id: str) -> bool:
        self._in_memory.pop(memory_id, None)
        deleted_any = False
        for tier in MemoryTier:
            if self._persistence.delete_entry(memory_id, tier):
                deleted_any = True
        return deleted_any

    def query(self, query: MemoryQuery) -> MemoryResult:
        start = time.perf_counter()
        results: list[MemoryEntry] = []
        source: dict[str, MemoryEntry] = {}

        source.update(self._in_memory)
        if query.key or query.tier or query.agent_id or query.session_id or query.tags or query.domain:
            loaded = self._persistence.load_all()
            for tier_entries in loaded.values():
                for e in tier_entries:
                    if e.memory_id not in source:
                        source[e.memory_id] = e

        for entry in source.values():
            if not query.include_expired and entry.is_expired:
                continue
            if query.key and query.key not in entry.key:
                continue
            if query.tier and entry.tier != query.tier:
                continue
            if query.domain and entry.domain != query.domain:
                continue
            if query.agent_id and entry.agent_id != query.agent_id:
                continue
            if query.session_id and entry.session_id != query.session_id:
                continue
            if query.min_score and entry.score < query.min_score:
                continue
            if query.tags and not all(t in entry.tags for t in query.tags):
                continue
            results.append(entry)

        total = len(results)
        results.sort(key=lambda e: (e.score, e.timestamp), reverse=True)
        results = results[query.offset : query.offset + query.limit]
        elapsed = (time.perf_counter() - start) * 1000

        return MemoryResult(entries=results, total_count=total, query_time_ms=elapsed)

    @property
    def eviction_count(self) -> int:
        return self._eviction_count

    def get_stats(self) -> MemoryStats:
        all_entries: list[MemoryEntry] = []
        all_entries.extend(self._in_memory.values())
        loaded = self._persistence.load_all()
        for tier_entries in loaded.values():
            seen = {e.memory_id for e in all_entries}
            for e in tier_entries:
                if e.memory_id not in seen:
                    all_entries.append(e)

        stats = MemoryStats(total_entries=len(all_entries), eviction_count=self._eviction_count)
        for e in all_entries:
            tier_name = e.tier.name
            domain_name = e.domain.name
            stats.entries_by_tier[tier_name] = stats.entries_by_tier.get(tier_name, 0) + 1
            stats.entries_by_domain[domain_name] = stats.entries_by_domain.get(domain_name, 0) + 1
        if all_entries:
            sorted_by_time = sorted(all_entries, key=lambda e: e.timestamp)
            stats.oldest_entry = sorted_by_time[0].memory_id
            stats.newest_entry = sorted_by_time[-1].memory_id
        return stats

    def sweep_expired(self) -> int:
        expired_ids = [mid for mid, e in self._in_memory.items() if e.is_expired]
        for mid in expired_ids:
            self._in_memory.pop(mid, None)
        if expired_ids:
            MetricsRegistry().increment("memory.ttl_evictions", amount=len(expired_ids))
        return len(expired_ids)

    def clear(self) -> int:
        count = len(self._in_memory)
        self._in_memory.clear()
        cleared = self._persistence.clear_all()
        total_cleared = count + sum(cleared.values())
        return total_cleared
