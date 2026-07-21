from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from duplicate_question_app._memory.interfaces import MemoryEntry


@dataclass
class StoreResult:
    memory_id: str
    success: bool
    version: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "success": self.success,
            "version": self.version,
            "message": self.message,
        }


@dataclass
class DeleteResult:
    memory_id: str
    success: bool
    soft_deleted: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "success": self.success,
            "soft_deleted": self.soft_deleted,
            "message": self.message,
        }


@dataclass
class ConsolidationResult:
    merged_ids: list[str]
    new_entry: MemoryEntry | None
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "merged_ids": list(self.merged_ids),
            "new_entry": self.new_entry.to_dict() if self.new_entry is not None else None,
            "summary": self.summary,
        }
