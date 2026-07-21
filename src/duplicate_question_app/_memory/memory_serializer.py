from __future__ import annotations

from typing import Any

from duplicate_question_app._memory.interfaces import MemoryEntry


class MemorySerializer:
    @staticmethod
    def serialize(entry: MemoryEntry) -> dict[str, Any]:
        return entry.to_dict()

    @staticmethod
    def serialize_batch(entries: list[MemoryEntry]) -> list[dict[str, Any]]:
        return [entry.to_dict() for entry in entries]
