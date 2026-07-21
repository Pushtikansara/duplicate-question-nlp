from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from duplicate_question_app._memory.interfaces import (
    MemoryEntry,
    MemoryStatistics,
    MemoryStatus,
    MemoryStore,
    MemoryType,
)

logger = logging.getLogger(__name__)


class DefaultMemoryStatistics:
    def compute(self, store: MemoryStore) -> MemoryStatistics:
        all_entries: list[MemoryEntry] = []
        offset = 0
        while True:
            batch, _ = store.list_all(limit=1000, offset=offset)
            if not batch:
                break
            all_entries.extend(batch)
            offset += len(batch)

        total = len(all_entries)
        if total == 0:
            return MemoryStatistics(
                total_entries=0,
                total_by_type={},
                total_size_bytes=0,
                avg_quality=0.0,
                avg_confidence=0.0,
                version_count=0,
                deleted_count=0,
            )

        by_type: dict[str, int] = {}
        total_quality = 0.0
        total_confidence = 0.0
        version_count = 0
        size_bytes = 0
        oldest: datetime | None = None
        newest: datetime | None = None

        for e in all_entries:
            mt = e.memory_type.value
            by_type[mt] = by_type.get(mt, 0) + 1
            total_quality += e.quality_score
            total_confidence += e.confidence
            version_count += e.version
            size_bytes += len(str(e.to_dict()))
            if oldest is None or e.timestamp < oldest:
                oldest = e.timestamp
            if newest is None or e.timestamp > newest:
                newest = e.timestamp

        deleted_count = 0
        offset = 0
        while True:
            batch, _ = store.list_all(limit=1000, offset=offset)
            if not batch:
                break
            for e in batch:
                if e.status == MemoryStatus.DELETED:
                    deleted_count += 1
            offset += len(batch)

        return MemoryStatistics(
            total_entries=total,
            total_by_type=by_type,
            total_size_bytes=size_bytes,
            avg_quality=total_quality / total,
            avg_confidence=total_confidence / total,
            oldest_entry=oldest,
            newest_entry=newest,
            version_count=version_count,
            deleted_count=deleted_count,
        )

    def compute_by_type(self, store: MemoryStore, memory_type: MemoryType) -> dict[str, Any]:
        entries, total = store.list_by_type(memory_type, limit=10000)
        if total == 0:
            return {"type": memory_type.value, "count": 0}

        avg_quality = sum(e.quality_score for e in entries) / total
        avg_confidence = sum(e.confidence for e in entries) / total
        size_bytes = sum(len(str(e.to_dict())) for e in entries)

        return {
            "type": memory_type.value,
            "count": total,
            "avg_quality": avg_quality,
            "avg_confidence": avg_confidence,
            "total_size_bytes": size_bytes,
        }

    def compute_growth_rate(self, store: MemoryStore, hours: int = 24) -> float:
        cutoff = datetime.now() - timedelta(hours=hours)
        all_entries: list[MemoryEntry] = []
        offset = 0
        while True:
            batch, _ = store.list_all(limit=1000, offset=offset)
            if not batch:
                break
            all_entries.extend(batch)
            offset += len(batch)

        recent = sum(1 for e in all_entries if e.timestamp >= cutoff)
        if hours <= 0:
            return 0.0
        return recent / hours
