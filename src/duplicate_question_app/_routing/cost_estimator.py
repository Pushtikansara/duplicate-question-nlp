from __future__ import annotations

import logging

from duplicate_question_app._routing.interfaces import CostEstimator
from duplicate_question_app._routing.routing_result import ComplexityResult

log = logging.getLogger(__name__)

_BASE_COSTS: dict[str, float] = {
    "cross_encoder_only": 0.1,
    "semantic_reasoning": 0.4,
    "full_cognitive": 0.7,
    "uncertain_full": 1.0,
}


class DefaultCostEstimator(CostEstimator):
    def estimate_cost(
        self,
        pipeline: str,
        complexity: ComplexityResult,
    ) -> float:
        base_cost = _BASE_COSTS.get(pipeline)
        if base_cost is None:
            log.warning("Unknown pipeline '%s', returning max cost", pipeline)
            return 1.0

        try:
            complexity_score = complexity.score
        except (AttributeError, TypeError):
            complexity_score = 0.5

        avg_word_count = complexity.features.get("avg_word_count", 0)
        length_factor = 1.0 + (avg_word_count / 100.0) * 0.2

        complexity_factor = 1.0 + (complexity_score - 0.5) * 0.3

        final_cost = base_cost * length_factor * complexity_factor
        return max(0.0, min(1.0, final_cost))
