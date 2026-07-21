from __future__ import annotations

import logging
from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStore

logger = logging.getLogger(__name__)


class MemoryLineageTracker:
    def __init__(self) -> None:
        self._parent_map: dict[str, list[str]] = {}

    def track_lineage(self, entry: MemoryEntry) -> MemoryEntry:
        lineage = entry.lineage
        if lineage is None:
            lineage = MemoryLineage(
                created_by="unknown",
                created_at=datetime.now(),
                parent_ids=[],
                module_chain=["_memory"],
            )
            entry.lineage = lineage

        for pid in lineage.parent_ids:
            self._parent_map.setdefault(pid, []).append(entry.memory_id)

        return entry

    def get_ancestors(self, entry: MemoryEntry, store: MemoryStore) -> list[MemoryEntry]:
        ancestors: list[MemoryEntry] = []
        lineage = entry.lineage
        if lineage is None:
            return ancestors

        visited: set[str] = set()

        def _walk(memory_id: str) -> None:
            if memory_id in visited:
                return
            visited.add(memory_id)
            parent_entry = store.retrieve(memory_id)
            if parent_entry is not None:
                ancestors.append(parent_entry)
                if parent_entry.lineage:
                    for pid in parent_entry.lineage.parent_ids:
                        _walk(pid)

        for pid in lineage.parent_ids:
            _walk(pid)

        return ancestors

    def get_descendants(self, memory_id: str, store: MemoryStore) -> list[MemoryEntry]:
        descendants: list[MemoryEntry] = []
        visited: set[str] = set()

        def _walk(mid: str) -> None:
            if mid in visited:
                return
            visited.add(mid)
            children = self._parent_map.get(mid, [])
            for cid in children:
                child_entry = store.retrieve(cid)
                if child_entry is not None:
                    descendants.append(child_entry)
                    _walk(cid)

        _walk(memory_id)
        return descendants

    def merge_lineages(self, entries: list[MemoryEntry]) -> MemoryLineage:
        if not entries:
            return MemoryLineage(created_by="merge", created_at=datetime.now())

        all_parent_ids: list[str] = []
        all_module_chain: list[str] = []
        reasoning_ids: list[str] = []
        debate_ids: list[str] = []

        for e in entries:
            if e.lineage:
                all_parent_ids.extend(e.lineage.parent_ids)
                all_module_chain.extend(e.lineage.module_chain)
                if e.lineage.reasoning_id:
                    reasoning_ids.append(e.lineage.reasoning_id)
                if e.lineage.debate_id:
                    debate_ids.append(e.lineage.debate_id)

        unique_parents = list(dict.fromkeys(all_parent_ids))
        unique_modules = list(dict.fromkeys(all_module_chain))

        return MemoryLineage(
            created_by="merge",
            created_at=datetime.now(),
            parent_ids=unique_parents,
            module_chain=unique_modules,
            reasoning_id=reasoning_ids[0] if reasoning_ids else None,
            debate_id=debate_ids[0] if debate_ids else None,
        )
