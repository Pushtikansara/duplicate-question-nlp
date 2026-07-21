from __future__ import annotations

import logging

from duplicate_question_app._memory.interfaces import (
    MemoryEntry,
    MemoryIndex,
    MemoryQuery,
    MemoryStatus,
    MemoryStore,
)

logger = logging.getLogger(__name__)


class DefaultMemoryIndex(MemoryIndex):
    def __init__(self) -> None:
        self._by_type: dict[str, set[str]] = {}
        self._by_tag: dict[str, set[str]] = {}
        self._by_source: dict[str, set[str]] = {}
        self._id_set: set[str] = set()
        self._quality_map: dict[str, float] = {}
        self._confidence_map: dict[str, float] = {}

    def index_entry(self, entry: MemoryEntry) -> None:
        self._id_set.add(entry.memory_id)
        self._by_type.setdefault(entry.memory_type.value, set()).add(entry.memory_id)
        for tag in entry.tags:
            self._by_tag.setdefault(tag, set()).add(entry.memory_id)
        self._by_source.setdefault(entry.source_module, set()).add(entry.memory_id)
        self._quality_map[entry.memory_id] = entry.quality_score
        self._confidence_map[entry.memory_id] = entry.confidence

    def search(self, query: MemoryQuery, store: MemoryStore) -> list[MemoryEntry]:
        candidate_ids: set[str] | None = None

        if query.memory_types:
            type_ids: set[str] = set()
            for mt in query.memory_types:
                type_ids.update(self._by_type.get(mt.value, set()))
            candidate_ids = type_ids if candidate_ids is None else candidate_ids & type_ids

        if query.tags:
            tag_ids: set[str] = set()
            for tag in query.tags:
                tag_ids.update(self._by_tag.get(tag, set()))
            candidate_ids = tag_ids if candidate_ids is None else candidate_ids & tag_ids

        if query.source_modules:
            source_ids: set[str] = set()
            for src in query.source_modules:
                source_ids.update(self._by_source.get(src, set()))
            candidate_ids = source_ids if candidate_ids is None else candidate_ids & source_ids

        if candidate_ids is None:
            candidate_ids = set(self._id_set)

        if query.min_confidence > 0.0:
            candidate_ids = {cid for cid in candidate_ids if self._confidence_map.get(cid, 0.0) >= query.min_confidence}

        if query.min_quality > 0.0:
            candidate_ids = {cid for cid in candidate_ids if self._quality_map.get(cid, 0.0) >= query.min_quality}

        entries: list[MemoryEntry] = []
        for cid in list(candidate_ids):
            entry = store.retrieve(cid)
            if (
                entry is not None
                and entry.status != MemoryStatus.DELETED
                and (not query.text or self._text_match(entry, query.text))
            ):
                entries.append(entry)

        for key, value in query.filters.items():
            entries = [e for e in entries if e.metadata.get(key) == value or e.content.get(key) == value]

        return entries

    def _text_match(self, entry: MemoryEntry, text: str) -> bool:
        text_lower = text.lower()
        for val in entry.content.values():
            if isinstance(val, str) and text_lower in val.lower():
                return True
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str) and text_lower in item.lower():
                        return True
        return text_lower in entry.tags

    def remove(self, memory_id: str) -> None:
        if memory_id in self._id_set:
            self._id_set.discard(memory_id)
            for type_set in self._by_type.values():
                type_set.discard(memory_id)
            for tag_set in self._by_tag.values():
                tag_set.discard(memory_id)
            for src_set in self._by_source.values():
                src_set.discard(memory_id)
            self._quality_map.pop(memory_id, None)
            self._confidence_map.pop(memory_id, None)

    def rebuild(self, entries: list[MemoryEntry]) -> None:
        self._by_type.clear()
        self._by_tag.clear()
        self._by_source.clear()
        self._id_set.clear()
        self._quality_map.clear()
        self._confidence_map.clear()
        for entry in entries:
            self.index_entry(entry)
