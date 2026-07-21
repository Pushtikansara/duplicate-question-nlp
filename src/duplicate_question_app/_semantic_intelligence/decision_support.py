"""DecisionSupport — produces a recommendation from a SemanticAssessment.

Evaluates the full assessment and generates a decision with reasoning.
"""

from __future__ import annotations

from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    Recommendation,
    SemanticAssessment,
)


class DefaultDecisionSupport:
    def __init__(self, duplicate_threshold: float = 0.7, uncertain_threshold: float = 0.4):
        self._dup_threshold = duplicate_threshold
        self._uncertain_threshold = uncertain_threshold

    def evaluate(self, assessment: SemanticAssessment) -> dict:
        sim = assessment.semantic_similarity
        confidence = assessment.confidence
        conflict_severity = max((c.severity for c in assessment.conflicts), default=0.0)

        effective_sim = sim * (1.0 - conflict_severity * 0.5)
        effective_sim = max(0.0, min(1.0, effective_sim))

        if effective_sim >= self._dup_threshold and confidence >= 0.5:
            recommendation = Recommendation.DUPLICATE
            reason = self._build_duplicate_reason(assessment)
        elif effective_sim < self._uncertain_threshold or conflict_severity > 0.7:
            recommendation = Recommendation.NOT_DUPLICATE
            reason = self._build_not_duplicate_reason(assessment, conflict_severity)
        else:
            recommendation = Recommendation.UNCERTAIN
            reason = self._build_uncertain_reason(assessment)

        return {
            "recommendation": recommendation,
            "reason": reason,
            "effective_similarity": effective_sim,
            "duplicate_threshold": self._dup_threshold,
            "uncertain_threshold": self._uncertain_threshold,
        }

    def _build_duplicate_reason(self, assessment: SemanticAssessment) -> str:
        parts = []
        if assessment.concept_overlap.overlap_score > 0.5:
            parts.append(f"concept overlap {assessment.concept_overlap.overlap_score:.0%}")
        if assessment.intent_similarity.score > 0.7:
            parts.append("intent matches")
        if assessment.context_similarity.domain_match:
            parts.append("domain matches")
        if assessment.entity_overlap.overlap_score > 0.5:
            parts.append(f"entity overlap {assessment.entity_overlap.overlap_score:.0%}")
        return "Likely duplicate: " + ", ".join(parts) if parts else "High semantic similarity"

    def _build_not_duplicate_reason(self, assessment: SemanticAssessment, conflict_severity: float) -> str:
        parts = []
        if conflict_severity > 0.7:
            parts.append("strong conflicts detected")
        if assessment.context_similarity.domain_match is False:
            parts.append("domain mismatch")
        if assessment.intent_similarity.score < 0.3:
            parts.append("intent differs significantly")
        if assessment.concept_overlap.overlap_score < 0.3:
            parts.append("low concept overlap")
        return "Likely not duplicate: " + ", ".join(parts) if parts else "Low semantic similarity"

    def _build_uncertain_reason(self, assessment: SemanticAssessment) -> str:
        parts = []
        if assessment.conflicts:
            parts.append(f"{len(assessment.conflicts)} conflict(s) present")
        if 0.3 <= assessment.semantic_similarity < 0.7:
            parts.append(f"similarity {assessment.semantic_similarity:.0%} in ambiguous range")
        return "Uncertain: " + "; ".join(parts) if parts else "Insufficient evidence for definitive classification"


DecisionSupport = DefaultDecisionSupport
