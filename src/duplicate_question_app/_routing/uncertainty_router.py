from __future__ import annotations

import logging

from duplicate_question_app._reasoning.reasoning_result import ReasoningResult
from duplicate_question_app._routing.interfaces import UncertaintyRouter
from duplicate_question_app._routing.routing_result import UncertaintyResult
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment

log = logging.getLogger(__name__)


class DefaultUncertaintyRouter(UncertaintyRouter):
    def should_escalate(
        self,
        cross_encoder_score: float | None,
        semantic_assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> UncertaintyResult:
        contributing_factors: list[str] = []
        max_uncertainty = 0.0

        if cross_encoder_score is not None:
            try:
                cross_confidence = float(cross_encoder_score)
            except (TypeError, ValueError):
                cross_confidence = 0.0
            if cross_confidence < 0.4:
                contributing_factors.append(f"CrossEncoder confidence too low: {cross_confidence:.3f}")
                max_uncertainty = max(max_uncertainty, 1.0 - cross_confidence)

        if semantic_assessment is not None:
            try:
                semantic_conf = float(semantic_assessment.confidence)
            except (TypeError, ValueError):
                semantic_conf = 0.0
            if semantic_conf < 0.5:
                contributing_factors.append(f"Semantic confidence too low: {semantic_conf:.3f}")
                max_uncertainty = max(max_uncertainty, 1.0 - semantic_conf)

            if semantic_assessment.conflicts:
                num_conflicts = len(semantic_assessment.conflicts)
                max_severity = max(
                    (c.severity for c in semantic_assessment.conflicts),
                    default=0.0,
                )
                contributing_factors.append(
                    f"Assessment has {num_conflicts} conflict(s) (max severity: {max_severity:.2f})"
                )
                max_uncertainty = max(max_uncertainty, max_severity)

            try:
                semantic_sim = float(semantic_assessment.semantic_similarity)
            except (TypeError, ValueError):
                semantic_sim = 0.0
            if semantic_sim < 0.3:
                contributing_factors.append(f"Low semantic similarity: {semantic_sim:.3f}")
                max_uncertainty = max(max_uncertainty, 1.0 - semantic_sim)

        if reasoning_result is not None:
            try:
                reasoning_uncertainty = float(reasoning_result.uncertainty)
            except (TypeError, ValueError):
                reasoning_uncertainty = 0.0
            if reasoning_uncertainty > 0.6:
                contributing_factors.append(f"High reasoning uncertainty: {reasoning_uncertainty:.3f}")
                max_uncertainty = max(max_uncertainty, reasoning_uncertainty)

            try:
                reasoning_conf = float(reasoning_result.confidence)
            except (TypeError, ValueError):
                reasoning_conf = 0.0
            if reasoning_conf < 0.4:
                contributing_factors.append(f"Low reasoning confidence: {reasoning_conf:.3f}")
                max_uncertainty = max(max_uncertainty, 1.0 - reasoning_conf)

        should_escalate = len(contributing_factors) > 0

        if should_escalate:
            reason = "Escalation triggered: " + "; ".join(contributing_factors)
        else:
            reason = "No escalation needed: all confidence scores are acceptable"

        return UncertaintyResult(
            should_escalate=should_escalate,
            reason=reason,
            uncertainty_score=max_uncertainty,
            contributing_factors=contributing_factors,
        )
