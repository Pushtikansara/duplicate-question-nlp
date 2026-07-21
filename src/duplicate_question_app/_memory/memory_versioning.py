from __future__ import annotations

import logging
from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStore, MemoryVersioning

logger = logging.getLogger(__name__)


class DefaultMemoryVersioning(MemoryVersioning):
    def __init__(self, max_versions: int = 10) -> None:
        self._max_versions = max_versions
        self._chains: dict[str, list[int]] = {}

    def create_version(self, entry: MemoryEntry, parent_id: str | None = None) -> MemoryEntry:
        new_version = entry.version + 1

        new_lineage = MemoryLineage(
            created_by=entry.lineage.created_by if entry.lineage else "versioning",
            created_at=entry.lineage.created_at if entry.lineage else datetime.now(),
            parent_ids=list(entry.lineage.parent_ids if entry.lineage else []),
            module_chain=list(entry.lineage.module_chain if entry.lineage else []),
            reasoning_id=entry.lineage.reasoning_id if entry.lineage else None,
            debate_id=entry.lineage.debate_id if entry.lineage else None,
        )

        if parent_id and parent_id not in new_lineage.parent_ids:
            new_lineage.parent_ids.append(parent_id)

        new_entry = MemoryEntry(
            memory_id=entry.memory_id,
            memory_type=entry.memory_type,
            version=new_version,
            timestamp=datetime.now(),
            source_module=entry.source_module,
            quality_score=entry.quality_score,
            confidence=entry.confidence,
            lineage=new_lineage,
            tags=list(entry.tags),
            metadata=dict(entry.metadata),
            content=dict(entry.content),
            embedding=list(entry.embedding) if entry.embedding is not None else None,
            expires_at=entry.expires_at,
            status=entry.status,
        )

        chain = self._chains.setdefault(entry.memory_id, [])
        chain.append(new_version)
        if len(chain) > self._max_versions:
            chain.pop(0)

        logger.debug(
            "Created version %d for memory %s (parent=%s)",
            new_version,
            entry.memory_id,
            parent_id,
        )
        return new_entry

    def get_version_history(self, memory_id: str, store: MemoryStore) -> list[MemoryEntry]:
        history: list[MemoryEntry] = []
        current = store.retrieve(memory_id)
        if current is not None:
            history.append(current)
        chain = self._chains.get(memory_id, [])
        for ver in sorted(chain):
            if current is None or ver != current.version:
                candidate = store.retrieve(memory_id)
                if candidate is not None and candidate.version == ver:
                    history.append(candidate)
        return sorted(history, key=lambda e: e.version)
