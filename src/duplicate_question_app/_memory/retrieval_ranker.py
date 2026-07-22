from __future__ import annotations

from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryQuery, RetrievalRanker


class RecencyRanker(RetrievalRanker):
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        return sorted(entries, key=lambda e: e.timestamp, reverse=True)


class ConfidenceRanker(RetrievalRanker):
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        return sorted(entries, key=lambda e: e.confidence, reverse=True)


class QualityRanker(RetrievalRanker):
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        return sorted(entries, key=lambda e: e.quality_score, reverse=True)


class UsageFrequencyRanker(RetrievalRanker):
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        def _access_count(entry: MemoryEntry) -> int:
            meta = entry.metadata
            if isinstance(meta, dict):
                return int(meta.get("access_count", 0))
            return 0

        return sorted(entries, key=_access_count, reverse=True)


class CompositeRanker(RetrievalRanker):
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or {
            "recency": 0.3,
            "confidence": 0.3,
            "quality": 0.2,
            "frequency": 0.2,
        }

    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        def _score(entry: MemoryEntry) -> float:
            total = 0.0
            if self.weights.get("recency", 0) > 0:
                age_hours = (datetime.now() - entry.timestamp).total_seconds() / 3600
                recency_score = max(0.0, 1.0 - age_hours / (24 * 365))
                total += self.weights["recency"] * recency_score
            if self.weights.get("confidence", 0) > 0:
                total += self.weights["confidence"] * entry.confidence
            if self.weights.get("quality", 0) > 0:
                total += self.weights["quality"] * entry.quality_score
            if self.weights.get("frequency", 0) > 0:
                meta = entry.metadata
                freq = 0.0
                if isinstance(meta, dict):
                    access = meta.get("access_count", 0)
                    freq = min(access / 1000.0, 1.0)
                total += self.weights["frequency"] * freq
            return total

        return sorted(entries, key=_score, reverse=True)
