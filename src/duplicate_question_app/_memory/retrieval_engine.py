from __future__ import annotations

import logging
import time

from duplicate_question_app._memory.interfaces import (
    MemoryEntry,
    MemoryIndex,
    MemoryQuery,
    MemoryResult,
    MemoryStatus,
    MemoryStore,
    RetrievalEngine,
    RetrievalRanker,
)

logger = logging.getLogger(__name__)


class DefaultRetrievalEngine(RetrievalEngine):
    def __init__(self, index: MemoryIndex | None = None) -> None:
        self._index = index

    def retrieve(
        self,
        query: MemoryQuery,
        store: MemoryStore,
        index: MemoryIndex | None = None,
        ranker: RetrievalRanker | None = None,
    ) -> MemoryResult:
        start = time.perf_counter()
        effective_index = index or self._index

        if effective_index:
            entries = effective_index.search(query, store)
        else:
            all_entries, _ = store.list_all(limit=10000)
            entries = self._filter(query, all_entries)

        if ranker:
            entries = ranker.rank(entries, query)

        total_count = len(entries)
        sliced = entries[query.offset : query.offset + query.limit]
        elapsed = (time.perf_counter() - start) * 1000.0

        return MemoryResult(
            entries=sliced,
            total_count=total_count,
            query_time_ms=elapsed,
            query=query,
        )

    def _filter(self, query: MemoryQuery, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        filtered = list(entries)

        if query.memory_types:
            type_set = set(query.memory_types)
            filtered = [e for e in filtered if e.memory_type in type_set]

        if query.tags:
            tag_set = set(query.tags)
            filtered = [e for e in filtered if tag_set.intersection(e.tags)]

        if query.source_modules:
            src_set = set(query.source_modules)
            filtered = [e for e in filtered if e.source_module in src_set]

        if query.min_confidence > 0.0:
            filtered = [e for e in filtered if e.confidence >= query.min_confidence]

        if query.min_quality > 0.0:
            filtered = [e for e in filtered if e.quality_score >= query.min_quality]

        if query.text:
            text_lower = query.text.lower()
            filtered = [e for e in filtered if self._text_in_entry(e, text_lower)]

        filtered = [e for e in filtered if e.status != MemoryStatus.DELETED]

        for key, value in query.filters.items():
            filtered = [e for e in filtered if e.metadata.get(key) == value or e.content.get(key) == value]

        return filtered

    @staticmethod
    def _text_in_entry(entry: MemoryEntry, text_lower: str) -> bool:
        for val in entry.content.values():
            if isinstance(val, str) and text_lower in val.lower():
                return True
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str) and text_lower in item.lower():
                        return True
        return text_lower in [t.lower() for t in entry.tags]
