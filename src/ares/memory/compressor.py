from __future__ import annotations

import logging
from datetime import datetime, timezone

from ares.memory.types import MemoryDomain, MemoryEntry, MemoryTier

logger = logging.getLogger(__name__)


class MemoryCompressor:
    def compress_working_to_short_term(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        promoted: list[MemoryEntry] = []
        for entry in entries:
            if entry.tier != MemoryTier.WORKING:
                continue
            promoted.append(
                MemoryEntry(
                    memory_id=entry.memory_id,
                    key=entry.key,
                    value=entry.value,
                    tier=MemoryTier.SHORT_TERM,
                    domain=entry.domain,
                    ttl_seconds=3600.0,
                    metadata=entry.metadata,
                    agent_id=entry.agent_id,
                    session_id=entry.session_id,
                    score=entry.score * 0.9,
                    access_count=entry.access_count,
                    version=entry.version + 1,
                    tags=list(entry.tags),
                )
            )
        return promoted

    def compress_short_to_long_term(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        consolidated: list[MemoryEntry] = []
        for entry in entries:
            if entry.tier != MemoryTier.SHORT_TERM:
                continue
            consolidated.append(
                MemoryEntry(
                    memory_id=entry.memory_id,
                    key=entry.key,
                    value=entry.value,
                    tier=MemoryTier.LONG_TERM,
                    domain=entry.domain,
                    ttl_seconds=None,
                    metadata=entry.metadata,
                    agent_id=entry.agent_id,
                    session_id=entry.session_id,
                    score=entry.score * 0.95,
                    access_count=entry.access_count,
                    version=entry.version + 1,
                    tags=list(entry.tags),
                )
            )
        return consolidated

    def compress_episodic_to_semantic(
        self,
        episodic_entries: list[MemoryEntry],
        max_age_hours: float = 48.0,
    ) -> list[MemoryEntry]:
        semantic: list[MemoryEntry] = []
        for entry in episodic_entries:
            if entry.domain != MemoryDomain.EPISODIC:
                continue
            age = (datetime.now(timezone.utc) - entry.timestamp).total_seconds()
            if age < max_age_hours * 3600:
                continue
            target_tier = MemoryTier.SHORT_TERM if entry.tier == MemoryTier.WORKING else entry.tier
            semantic.append(
                MemoryEntry(
                    memory_id=entry.memory_id,
                    key=entry.key,
                    value=entry.value,
                    tier=target_tier,
                    domain=MemoryDomain.SEMANTIC,
                    ttl_seconds=entry.ttl_seconds,
                    metadata=entry.metadata,
                    agent_id=entry.agent_id,
                    session_id=entry.session_id,
                    score=entry.score * 0.85,
                    access_count=entry.access_count,
                    version=entry.version + 1,
                    tags=list(entry.tags),
                )
            )
        return semantic

    def prune_expired(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        now = datetime.now(timezone.utc)
        pruned: list[MemoryEntry] = []
        for entry in entries:
            if entry.ttl_seconds is not None:
                elapsed = (now - entry.timestamp).total_seconds()
                if elapsed > entry.ttl_seconds:
                    continue
            pruned.append(entry)
        return pruned
