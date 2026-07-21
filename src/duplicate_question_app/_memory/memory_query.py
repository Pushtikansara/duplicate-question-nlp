from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryQuery, MemoryType


class MemoryQueryBuilder:
    @staticmethod
    def by_type(memory_type: MemoryType, limit: int = 100) -> MemoryQuery:
        return MemoryQuery(
            query_type="exact",
            memory_types=[memory_type],
            limit=limit,
        )

    @staticmethod
    def by_tags(tags: list[str], limit: int = 100) -> MemoryQuery:
        return MemoryQuery(
            query_type="exact",
            tags=tags,
            limit=limit,
        )

    @staticmethod
    def by_confidence(min_confidence: float, limit: int = 100) -> MemoryQuery:
        return MemoryQuery(
            query_type="exact",
            min_confidence=min_confidence,
            limit=limit,
        )

    @staticmethod
    def by_source(module: str, limit: int = 100) -> MemoryQuery:
        return MemoryQuery(
            query_type="exact",
            source_modules=[module],
            limit=limit,
        )

    @staticmethod
    def text_search(text: str, limit: int = 100) -> MemoryQuery:
        return MemoryQuery(
            query_type="semantic",
            text=text,
            limit=limit,
        )

    @staticmethod
    def hybrid(text: str, memory_types: list[MemoryType], limit: int = 100) -> MemoryQuery:
        return MemoryQuery(
            query_type="hybrid",
            memory_types=memory_types,
            text=text,
            limit=limit,
        )
