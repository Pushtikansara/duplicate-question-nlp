from __future__ import annotations

import numpy as np

from duplicate_question_app._reasoning.interfaces import UncertaintyEstimator
from duplicate_question_app._reasoning.reasoning_result import Evidence, EvidenceType, Hypothesis, Premise


class DefaultUncertaintyEstimator(UncertaintyEstimator):
    def estimate(
        self,
        premises: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
        conflicts: list[Evidence],
    ) -> float:
        premise_unpacked_scores = [p.confidence for p in premises]
        premise_uncertainty = 1.0 - np.mean(premise_unpacked_scores) if premise_unpacked_scores else 0.5

        hyp_confidences = [h.confidence for h in hypotheses]
        if len(hyp_confidences) >= 2:
            hyp_max_separation = max(hyp_confidences) - min(hyp_confidences)
            hypothesis_uncertainty = 1.0 - min(1.0, hyp_max_separation)
        else:
            hypothesis_uncertainty = 0.5

        best_hypothesis = max(hypotheses, key=lambda h: h.confidence, default=None)

        conflict_count = len([c for c in conflicts if c.evidence_type != EvidenceType.NEUTRAL])
        total_evidence = len(evidence) + len(conflicts)
        conflict_ratio = conflict_count / max(1, total_evidence)
        conflict_uncertainty = conflict_ratio

        combined_evidence = evidence + conflicts
        if best_hypothesis is not None:
            combined_evidence = [e for e in combined_evidence if e.hypothesis_id == best_hypothesis.id]
        supporting = [e for e in combined_evidence if e.evidence_type == EvidenceType.SUPPORTING]
        contradicting = [e for e in combined_evidence if e.evidence_type == EvidenceType.CONTRADICTING]

        if supporting or contradicting:
            w_support = sum(e.weight * e.confidence for e in supporting)
            w_contra = sum(e.weight * e.confidence for e in contradicting)
            total = w_support + w_contra
            evidence_uncertainty_contrib = 1.0 - (abs(w_support - w_contra) / max(1, total)) if total > 0 else 0.5
        else:
            evidence_uncertainty_contrib = 0.5

        total_uncertainty = (
            premise_uncertainty * 0.2
            + hypothesis_uncertainty * 0.3
            + conflict_uncertainty * 0.3
            + evidence_uncertainty_contrib * 0.2
        )

        return float(np.clip(total_uncertainty, 0.0, 1.0))
