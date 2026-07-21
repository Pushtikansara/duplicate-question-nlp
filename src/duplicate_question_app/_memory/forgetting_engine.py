from __future__ import annotations

import logging
from datetime import datetime, timedelta

from duplicate_question_app._memory.interfaces import (
    ForgettingEngine,
    MemoryEntry,
    MemoryStatus,
    MemoryStore,
)
from duplicate_question_app._memory.memory_configuration import MemoryConfig

logger = logging.getLogger(__name__)


class DefaultForgettingEngine(ForgettingEngine):
    def __init__(self, config: MemoryConfig | None = None) -> None:
        self._config = config or MemoryConfig()

    def apply_policies(self, store: MemoryStore) -> list[str]:
        affected: list[str] = []
        all_entries: list[MemoryEntry] = []
        offset = 0
        while True:
            batch, _ = store.list_all(limit=1000, offset=offset)
            if not batch:
                break
            all_entries.extend(batch)
            offset += len(batch)

        for entry in all_entries:
            if entry.status != MemoryStatus.ACTIVE:
                continue

            should_archive = False
            reasons: list[str] = []

            age_score = self.calculate_age_score(entry)
            if age_score > 0.8:
                should_archive = True
                reasons.append("age")

            if entry.quality_score < self._config.quality_threshold:
                should_archive = True
                reasons.append("low_quality")

            if entry.confidence < self._config.confidence_threshold:
                should_archive = True
                reasons.append("low_confidence")

            if entry.expires_at is not None and datetime.now() > entry.expires_at:
                should_archive = True
                reasons.append("expired")

            if should_archive:
                entry.status = MemoryStatus.ARCHIVED
                try:
                    store.update(entry)
                    affected.append(entry.memory_id)
                    logger.info(
                        "Archived memory %s due to: %s",
                        entry.memory_id,
                        ", ".join(reasons),
                    )
                except Exception:
                    logger.exception("Failed to archive memory %s", entry.memory_id)

        return affected

    def calculate_age_score(self, entry: MemoryEntry) -> float:
        age = datetime.now() - entry.timestamp
        threshold = timedelta(days=self._config.aging_threshold_days)
        if age.total_seconds() <= 0:
            return 0.0
        score = min(age.total_seconds() / threshold.total_seconds(), 1.0)
        return round(score, 4)
