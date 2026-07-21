from __future__ import annotations

from duplicate_question_app._reasoning.interfaces import DecisionReasoner
from duplicate_question_app._reasoning.reasoning_result import Evidence, EvidenceType, Hypothesis, HypothesisLabel


class DefaultDecisionReasoner(DecisionReasoner):
    def decide(
        self,
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
        confidence: float,
        uncertainty: float,
        cross_encoder_score: float | None = None,
    ) -> str:
        best_hypothesis = max(hypotheses, key=lambda h: h.confidence, default=None)

        if best_hypothesis is None:
            return "uncertain"

        hyp_evidence = [e for e in evidence if e.hypothesis_id == best_hypothesis.id]
        supporting = [e for e in hyp_evidence if e.evidence_type == EvidenceType.SUPPORTING]
        contradicting = [e for e in hyp_evidence if e.evidence_type == EvidenceType.CONTRADICTING]
        w_support = sum(e.weight * e.confidence for e in supporting)
        w_contra = sum(e.weight * e.confidence for e in contradicting)

        evidence_net = w_support - w_contra
        evidence_net_normalized = max(-1.0, min(1.0, evidence_net / max(1, w_support + w_contra)))

        hyp_confidence = best_hypothesis.confidence
        label = best_hypothesis.label

        combined = confidence * 0.6 + hyp_confidence * 0.2 + max(0, evidence_net_normalized) * 0.2

        if cross_encoder_score is not None:
            ce_weight = 0.2
            ce_signal = cross_encoder_score if label == HypothesisLabel.DUPLICATE else (1 - cross_encoder_score)
            combined = combined * (1 - ce_weight) + ce_signal * ce_weight

        if uncertainty > 0.6:
            return "uncertain"

        if len(hypotheses) >= 2:
            sorted_h = sorted(hypotheses, key=lambda h: h.confidence, reverse=True)
            if sorted_h[0].confidence - sorted_h[1].confidence < 0.05:
                return "uncertain"

        if combined >= 0.5 and label == HypothesisLabel.DUPLICATE:
            return "duplicate"
        if combined >= 0.5 and label == HypothesisLabel.NOT_DUPLICATE:
            return "not_duplicate"
        if combined < 0.5 and label == HypothesisLabel.NOT_DUPLICATE:
            return "not_duplicate"
        if label == HypothesisLabel.UNCERTAIN:
            return "uncertain"

        if abs(hyp_confidence - 0.5) < 0.1 or abs(combined - 0.5) < 0.1:
            return "uncertain"

        if combined >= 0.5:
            return "duplicate"
        return "not_duplicate"

    def build_reason(self, decision: str, confidence: float, uncertainty: float, evidence: list[Evidence]) -> str:
        supporting = [e for e in evidence if e.evidence_type == EvidenceType.SUPPORTING]
        contradicting = [e for e in evidence if e.evidence_type == EvidenceType.CONTRADICTING]

        parts: list[str] = [f"Decision: {decision}"]
        parts.append(f"Confidence: {confidence:.3f}, Uncertainty: {uncertainty:.3f}")
        parts.append(f"Evidence: {len(supporting)} supporting, {len(contradicting)} contradicting")

        if supporting:
            top_support = sorted(supporting, key=lambda e: e.weight * e.confidence, reverse=True)[:3]
            parts.append("Key supporting evidence:")
            for e in top_support:
                parts.append(f"  - {e.text} (confidence={e.confidence:.2f}, weight={e.weight:.2f})")

        if contradicting:
            top_contra = sorted(contradicting, key=lambda e: e.weight * e.confidence, reverse=True)[:3]
            parts.append("Key contradicting evidence:")
            for e in top_contra:
                parts.append(f"  - {e.text} (confidence={e.confidence:.2f}, weight={e.weight:.2f})")

        return "\n".join(parts)
