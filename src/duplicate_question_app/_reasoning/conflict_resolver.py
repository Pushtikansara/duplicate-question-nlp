from __future__ import annotations

import uuid

from duplicate_question_app._reasoning.interfaces import ConflictResolver
from duplicate_question_app._reasoning.reasoning_result import Evidence, EvidenceType, Hypothesis, Premise


def _make_id() -> str:
    return uuid.uuid4().hex[:12]


class DefaultConflictResolver(ConflictResolver):
    def resolve(
        self,
        premises_a: list[Premise],
        premises_b: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> list[Evidence]:
        conflicts: list[Evidence] = []

        for hyp in hypotheses:
            supporting = [
                e for e in evidence if e.hypothesis_id == hyp.id and e.evidence_type == EvidenceType.SUPPORTING
            ]
            contradicting = [
                e for e in evidence if e.hypothesis_id == hyp.id and e.evidence_type == EvidenceType.CONTRADICTING
            ]

            if supporting and contradicting:
                total_support = sum(e.weight * e.confidence for e in supporting)
                total_contra = sum(e.weight * e.confidence for e in contradicting)
                total = total_support + total_contra

                if total > 0:
                    support_ratio = total_support / total
                    contra_ratio = total_contra / total

                    conflicts.append(
                        Evidence(
                            id=_make_id(),
                            hypothesis_id=hyp.id,
                            evidence_type=EvidenceType.CONTRADICTING,
                            text=f"Conflicting evidence for hypothesis '{hyp.text[:50]}': "
                            f"support ratio={support_ratio:.2f}, contra ratio={contra_ratio:.2f}",
                            confidence=min(1.0, abs(support_ratio - contra_ratio)),
                            source_premises=[],
                            weight=max(0.1, contra_ratio),
                            provenance="conflict_resolver",
                        )
                    )

        supported_hypotheses = set()
        for e in evidence:
            if e.evidence_type == EvidenceType.SUPPORTING:
                supported_hypotheses.add(e.hypothesis_id)

        unsupported = [h for h in hypotheses if h.id not in supported_hypotheses]
        for h in unsupported:
            conflicts.append(
                Evidence(
                    id=_make_id(),
                    hypothesis_id=h.id,
                    evidence_type=EvidenceType.NEUTRAL,
                    text=f"No supporting evidence found for hypothesis '{h.text[:50]}'",
                    confidence=0.5,
                    source_premises=[],
                    weight=0.1,
                    provenance="conflict_resolver.no_evidence",
                )
            )

        return conflicts
