from __future__ import annotations

from datetime import datetime, timedelta

from duplicate_question_app._memory.interfaces import MemoryEntry


class AgingPolicy:
    def __init__(self, threshold_days: int = 90) -> None:
        self.threshold_days = threshold_days

    def should_archive(self, entry: MemoryEntry) -> bool:
        age = datetime.now() - entry.timestamp
        return age.days >= self.threshold_days

    def age_score(self, entry: MemoryEntry) -> float:
        age = datetime.now() - entry.timestamp
        threshold = timedelta(days=self.threshold_days)
        if age.total_seconds() <= 0:
            return 0.0
        score = min(age.total_seconds() / threshold.total_seconds(), 1.0)
        return round(score, 4)

    def apply(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        return [e for e in entries if not self.should_archive(e)]
