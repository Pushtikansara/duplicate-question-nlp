from __future__ import annotations

import numpy as np

from duplicate_question_app._reasoning.interfaces import ConfidenceReasoner
from duplicate_question_app._reasoning.reasoning_result import (
    ConfidenceChain,
    Evidence,
    EvidenceType,
    Hypothesis,
    Premise,
)


class DefaultConfidenceReasoner(ConfidenceReasoner):
    def propagate(
        self,
        premises: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> float:
        hyp_confidences = [h.confidence for h in hypotheses]
        hypothesis_confidence = float(np.max(hyp_confidences)) if hyp_confidences else 0.0

        best_hypothesis = max(hypotheses, key=lambda h: h.confidence, default=None)
        if best_hypothesis is None:
            return 0.0

        hyp_evidence = [e for e in evidence if e.hypothesis_id == best_hypothesis.id]
        supporting = [e for e in hyp_evidence if e.evidence_type == EvidenceType.SUPPORTING]
        contradicting = [e for e in hyp_evidence if e.evidence_type == EvidenceType.CONTRADICTING]

        weighted_support = sum(e.weight * e.confidence for e in supporting)
        weighted_contra = sum(e.weight * e.confidence for e in contradicting)
        total = weighted_support + weighted_contra
        evidence_confidence = weighted_support / max(1, total)

        decision_confidence_contrib = evidence_confidence * hypothesis_confidence

        return float(np.clip(decision_confidence_contrib, 0.0, 1.0))

    def build_chain(
        self,
        premises: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
        decision_confidence: float,
    ) -> ConfidenceChain:
        implied_premise_confidences = [p.confidence for p in premises] or [0.5]
        premise_confidence = float(np.mean(implied_premise_confidences))
        hyp_confidences = [h.confidence for h in hypotheses] or [0.0]
        hypothesis_confidence = float(np.max(hyp_confidences))

        best_hypothesis = max(hypotheses, key=lambda h: h.confidence, default=None)
        if best_hypothesis is None:
            return ConfidenceChain(
                premise_confidence=premise_confidence,
                hypothesis_confidence=0.0,
                evidence_confidence=0.0,
                reasoning_confidence=0.0,
                decision_confidence=decision_confidence,
                sources={},
            )

        hyp_evidence = [e for e in evidence if e.hypothesis_id == best_hypothesis.id]
        supporting = [e for e in hyp_evidence if e.evidence_type == EvidenceType.SUPPORTING]
        contradicting = [e for e in hyp_evidence if e.evidence_type == EvidenceType.CONTRADICTING]
        weighted_support = sum(e.weight * e.confidence for e in supporting)
        weighted_contra = sum(e.weight * e.confidence for e in contradicting)
        total = weighted_support + weighted_contra
        evidence_confidence = weighted_support / max(1, total)

        reasoning_confidence = max(0.0, min(1.0, evidence_confidence * hypothesis_confidence))

        sources: dict[str, float] = {
            "premise_confidence": premise_confidence,
            "hypothesis_confidence": hypothesis_confidence,
            "evidence_confidence": evidence_confidence,
            "reasoning_confidence": reasoning_confidence,
            "weighted_support": weighted_support,
            "weighted_contra": weighted_contra,
        }

        return ConfidenceChain(
            premise_confidence=premise_confidence,
            hypothesis_confidence=hypothesis_confidence,
            evidence_confidence=evidence_confidence,
            reasoning_confidence=reasoning_confidence,
            decision_confidence=decision_confidence,
            sources=sources,
        )
