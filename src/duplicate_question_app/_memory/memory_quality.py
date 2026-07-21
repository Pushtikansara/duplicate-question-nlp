from __future__ import annotations

from typing import Any

from duplicate_question_app._memory.interfaces import MemoryEntry
from duplicate_question_app._memory.memory_metadata import MemoryMetadata


class MemoryQualityScorer:
    @staticmethod
    def score(entry: MemoryEntry) -> float:
        confidence_weight = MemoryQualityScorer.score_confidence_weight(entry.confidence)
        completeness = MemoryQualityScorer.score_completeness(entry.content)
        metadata = entry.metadata
        meta_obj: MemoryMetadata | None = None
        if isinstance(metadata, dict) and "created_at" in metadata:
            try:
                from datetime import datetime

                meta_obj = MemoryMetadata(
                    created_at=datetime.fromisoformat(metadata["created_at"])
                    if isinstance(metadata["created_at"], str)
                    else metadata["created_at"],
                    updated_at=datetime.fromisoformat(metadata["updated_at"])
                    if isinstance(metadata["updated_at"], str)
                    else metadata["updated_at"],
                    access_count=metadata.get("access_count", 0),
                    last_access=datetime.fromisoformat(metadata["last_access"])
                    if isinstance(metadata.get("last_access"), str) and metadata["last_access"]
                    else None,
                    usage_frequency=metadata.get("usage_frequency", 0.0),
                )
            except Exception:
                meta_obj = None
        usage = MemoryQualityScorer.score_usage(meta_obj) if meta_obj else 0.5
        evidence = min(entry.quality_score + 0.1, 1.0)

        raw = confidence_weight * 0.4 + evidence * 0.3 + usage * 0.2 + completeness * 0.1
        return round(min(max(raw, 0.0), 1.0), 4)

    @staticmethod
    def score_confidence_weight(confidence: float) -> float:
        return min(max(confidence, 0.0), 1.0)

    @staticmethod
    def score_completeness(content: dict[str, Any]) -> float:
        if not content:
            return 0.0
        total = len(content)
        if total == 0:
            return 0.0
        non_empty = sum(1 for v in content.values() if v is not None and v != "" and v != [] and v != {})
        return non_empty / total

    @staticmethod
    def score_usage(metadata: MemoryMetadata | None) -> float:
        if metadata is None:
            return 0.5
        max_freq = 10.0
        score = min(metadata.usage_frequency / max_freq, 1.0)
        if metadata.access_count > 100:
            score = min(score + 0.2, 1.0)
        return round(score, 4)
