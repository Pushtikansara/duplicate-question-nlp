from __future__ import annotations

from typing import Any

from duplicate_question_app._reflection.configuration import ReflectionConfig
from duplicate_question_app._reflection.interfaces import RecommendationType


class RecommendationEngine:
    def __init__(self, config: ReflectionConfig | None = None) -> None:
        self.config = config or ReflectionConfig()

    def generate(
        self,
        trust_score: float,
        confidence: float,
        routing_assessment: Any,
        reasoning_assessment: Any,
        debate_assessment: Any,
        memory_assessment: Any,
        consistency_warnings: list[Any],
        evidence_completeness: float,
    ) -> list[RecommendationType]:
        recommendations: list[RecommendationType] = []

        if trust_score >= 80.0 and confidence >= 0.8:
            recommendations.append(RecommendationType.ACCEPT)

        if confidence < self.config.low_confidence_threshold:
            recommendations.append(RecommendationType.LOW_CONFIDENCE_WARNING)

        if trust_score < self.config.human_review_threshold:
            recommendations.append(RecommendationType.HUMAN_REVIEW)

        if reasoning_assessment is not None:
            reasoning_score = getattr(reasoning_assessment, "score", 0.0)
            if reasoning_score < 0.4:
                recommendations.append(RecommendationType.RE_RUN_FULL)

        if routing_assessment is not None:
            routing_score = getattr(routing_assessment, "score", 0.0)
            if routing_score < 0.4:
                recommendations.append(RecommendationType.RE_RUN_DIFFERENT_ROUTING)

        if memory_assessment is not None:
            memory_score = getattr(memory_assessment, "score", 0.0)
            if memory_score < 0.3:
                recommendations.append(RecommendationType.MEMORY_REFRESH_SUGGESTED)

        if (
            len(consistency_warnings) >= self.config.max_warnings_before_review
            and RecommendationType.HUMAN_REVIEW not in recommendations
        ):
            recommendations.append(RecommendationType.HUMAN_REVIEW)

        if (
            evidence_completeness < self.config.evidence_completeness_threshold
            and RecommendationType.LOW_CONFIDENCE_WARNING not in recommendations
        ):
            recommendations.append(RecommendationType.LOW_CONFIDENCE_WARNING)

        if not recommendations:
            recommendations.append(RecommendationType.ACCEPT)

        return recommendations
