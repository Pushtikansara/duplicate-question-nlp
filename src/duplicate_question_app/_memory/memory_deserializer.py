from __future__ import annotations

from datetime import datetime
from typing import Any

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType


class MemoryDeserializer:
    @staticmethod
    def deserialize(data: dict[str, Any]) -> MemoryEntry:
        lineage_data = data.get("lineage", {})
        lineage = MemoryLineage(
            created_by=lineage_data.get("created_by", ""),
            created_at=_parse_dt(lineage_data.get("created_at")),
            parent_ids=list(lineage_data.get("parent_ids", [])),
            module_chain=list(lineage_data.get("module_chain", [])),
            reasoning_id=lineage_data.get("reasoning_id"),
            debate_id=lineage_data.get("debate_id"),
        )

        return MemoryEntry(
            memory_id=data["memory_id"],
            memory_type=MemoryType(data["memory_type"]),
            version=data["version"],
            timestamp=_parse_dt(data["timestamp"]),
            source_module=data.get("source_module", ""),
            quality_score=data["quality_score"],
            confidence=data["confidence"],
            lineage=lineage,
            tags=list(data.get("tags", [])),
            metadata=dict(data.get("metadata", {})),
            content=dict(data.get("content", {})),
            embedding=list(data["embedding"]) if data.get("embedding") is not None else None,
            expires_at=_parse_dt(data["expires_at"]) if data.get("expires_at") is not None else None,
            status=MemoryStatus(data.get("status", "active")),
        )

    @staticmethod
    def deserialize_batch(data_list: list[dict[str, Any]]) -> list[MemoryEntry]:
        return [MemoryDeserializer.deserialize(d) for d in data_list]


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return None
