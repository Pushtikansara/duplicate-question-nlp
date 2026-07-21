from __future__ import annotations

import logging

from duplicate_question_app._routing.interfaces import LatencyEstimator
from duplicate_question_app._routing.routing_result import ComplexityResult

log = logging.getLogger(__name__)

_LATENCY_RANGES: dict[str, tuple[float, float]] = {
    "cross_encoder_only": (50.0, 200.0),
    "semantic_reasoning": (200.0, 800.0),
    "full_cognitive": (500.0, 2000.0),
    "uncertain_full": (1000.0, 5000.0),
}


class DefaultLatencyEstimator(LatencyEstimator):
    def estimate_latency(
        self,
        pipeline: str,
        complexity: ComplexityResult,
    ) -> float:
        range_ = _LATENCY_RANGES.get(pipeline)
        if range_ is None:
            log.warning("Unknown pipeline '%s', returning max latency", pipeline)
            return 5000.0

        try:
            complexity_score = complexity.score
        except (AttributeError, TypeError):
            complexity_score = 0.5

        avg_word_count = complexity.features.get("avg_word_count", 0)
        length_factor = 1.0 + (avg_word_count / 50.0) * 0.3

        complexity_factor = 1.0 + (complexity_score - 0.5) * 0.5

        base_latency = (range_[0] + range_[1]) / 2.0
        estimated = base_latency * length_factor * complexity_factor
        return max(range_[0], min(range_[1], estimated))
