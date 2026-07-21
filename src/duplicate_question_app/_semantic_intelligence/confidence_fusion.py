"""ConfidenceFusion — computes holistic confidence from all intermediate similarity scores.

Weights are configurable via constructor injection.
"""

from __future__ import annotations

DEFAULT_WEIGHTS: dict[str, float] = {
    "concept_similarity": 0.25,
    "relation_similarity": 0.20,
    "intent_similarity": 0.25,
    "entity_similarity": 0.15,
    "context_similarity": 0.15,
}


class DefaultConfidenceFusion:
    def __init__(self, weights: dict[str, float] | None = None):
        self._weights = weights or DEFAULT_WEIGHTS

        total = sum(self._weights.values())
        if abs(total - 1.0) > 1e-6:
            self._weights = {k: v / total for k, v in self._weights.items()}

    def compute(self, scores: dict[str, float]) -> dict:
        weighted = {}
        for key, weight in self._weights.items():
            score = scores.get(key, 0.0)
            weighted[key] = score * weight

        overall = sum(weighted.values())

        return {
            "overall": overall,
            "weights": dict(self._weights),
            "weighted_scores": weighted,
            "raw_scores": dict(scores),
        }


ConfidenceFusion = DefaultConfidenceFusion
