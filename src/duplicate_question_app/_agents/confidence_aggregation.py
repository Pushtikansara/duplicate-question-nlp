from __future__ import annotations

import numpy as np

from duplicate_question_app._agents.interfaces import ConfidenceAggregationStrategy


class MeanAggregation(ConfidenceAggregationStrategy):
    def aggregate(self, confidences: list[float], weights: list[float] | None = None) -> float:
        if not confidences:
            return 0.0
        if weights:
            total_w = sum(weights)
            if total_w == 0:
                return float(np.mean(confidences))
            return float(sum(c * w for c, w in zip(confidences, weights, strict=True)) / total_w)
        return float(np.mean(confidences))


class MinAggregation(ConfidenceAggregationStrategy):
    def aggregate(self, confidences: list[float], weights: list[float] | None = None) -> float:
        if not confidences:
            return 0.0
        return float(min(confidences))


class MaxAggregation(ConfidenceAggregationStrategy):
    def aggregate(self, confidences: list[float], weights: list[float] | None = None) -> float:
        if not confidences:
            return 0.0
        return float(max(confidences))


class ProductAggregation(ConfidenceAggregationStrategy):
    def aggregate(self, confidences: list[float], weights: list[float] | None = None) -> float:
        if not confidences:
            return 0.0
        product = 1.0
        for c in confidences:
            product *= c
        return float(product)
