from __future__ import annotations

from typing import Any

from duplicate_question_app._reflection.configuration import ReflectionConfig
from duplicate_question_app._reflection.interfaces import RecommendationType


class HumanReviewDecider:
    def __init__(self, config: ReflectionConfig | None = None) -> None:
        self.config = config or ReflectionConfig()

    def should_review(
        self,
        trust_score: float,
        confidence: float,
        routing_assessment: Any,
        reasoning_assessment: Any,
        debate_assessment: Any,
        consistency_warnings: list[Any],
        recommendations: list[RecommendationType],
        explainability_score: float,
    ) -> tuple[bool, str]:
        reasons: list[str] = []

        if trust_score < self.config.human_review_threshold:
            reasons.append(f"Trust score below threshold ({trust_score:.1f} < {self.config.human_review_threshold})")

        if confidence < self.config.low_confidence_threshold:
            reasons.append(f"Low prediction confidence ({confidence:.2f})")

        if debate_assessment is not None:
            debate_score = getattr(debate_assessment, "score", 0.0)
            if debate_score < 0.4:
                reasons.append(f"High agent disagreement (debate score: {debate_score:.2f})")

        if reasoning_assessment is not None:
            reasoning_score = getattr(reasoning_assessment, "score", 0.0)
            if reasoning_score < 0.4:
                reasons.append(f"Low reasoning quality ({reasoning_score:.2f})")

        if len(consistency_warnings) >= self.config.max_warnings_before_review:
            reasons.append(f"Excessive consistency warnings ({len(consistency_warnings)})")

        if RecommendationType.HUMAN_REVIEW in recommendations and not any("Human review" in r for r in reasons):
            reasons.append("Recommendation engine flags human review")

        if not reasons:
            return False, ""

        return True, "; ".join(reasons)
