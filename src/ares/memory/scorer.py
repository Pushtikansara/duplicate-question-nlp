from __future__ import annotations

import math
from datetime import datetime, timezone


class MemoryScorer:
    def score_by_recency(self, timestamp: datetime, decay_hours: float = 24.0) -> float:
        delta = (datetime.now(timezone.utc) - timestamp).total_seconds()
        hours = delta / 3600
        return math.exp(-hours / decay_hours)

    def score_by_access_count(self, access_count: int, max_count: int = 100) -> float:
        return min(1.0, access_count / max_count)

    def score_by_frequency(self, access_count: int, time_span_hours: float = 24.0) -> float:
        if time_span_hours <= 0:
            return 0.0
        freq = access_count / time_span_hours
        return min(1.0, freq / 10.0)

    def combined_score(
        self,
        recency: float = 0.0,
        frequency: float = 0.0,
        base_quality: float = 1.0,
        recency_weight: float = 0.4,
        frequency_weight: float = 0.3,
        quality_weight: float = 0.3,
    ) -> float:
        return recency_weight * recency + frequency_weight * frequency + quality_weight * base_quality
