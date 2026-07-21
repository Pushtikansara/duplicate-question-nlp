from __future__ import annotations

import uuid

from duplicate_question_app._reasoning.interfaces import EvidenceChain
from duplicate_question_app._reasoning.reasoning_result import (
    Evidence,
    EvidenceType,
    Hypothesis,
    HypothesisLabel,
    Premise,
)
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


def _make_id() -> str:
    return uuid.uuid4().hex[:12]


class DefaultEvidenceChain(EvidenceChain):
    def build(
        self,
        hypotheses: list[Hypothesis],
        premises_a: list[Premise],
        premises_b: list[Premise],
        assessment: SemanticAssessment | None = None,
    ) -> list[Evidence]:
        evidence: list[Evidence] = []
        premise_map = {p.id: p for p in premises_a + premises_b}

        for hyp in hypotheses:
            hyp_notevidence = self._evidence_against(hyp, premise_map)
            evidence.extend(hyp_notevidence)

        if assessment is not None:
            sie_evidence = self._from_assessment(assessment, hypotheses, premise_map)
            evidence.extend(sie_evidence)

        evidence = self._deduplicate(evidence)
        return evidence

    def _evidence_against(
        self,
        hyp: Hypothesis,
        premise_map: dict[str, Premise],
    ) -> list[Evidence]:
        result: list[Evidence] = []

        if hyp.label == HypothesisLabel.DUPLICATE:
            for source_str in hyp.supporting_premises:
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.SUPPORTING,
                        text=f"Supports duplicate: {source_str}",
                        confidence=0.8,
                        source_premises=[],
                        provenance="hypothesis_derivation",
                    )
                )
            for source_str in hyp.contradicting_premises:
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.CONTRADICTING,
                        text=f"Contradicts duplicate: {source_str}",
                        confidence=0.8,
                        source_premises=[],
                        provenance="hypothesis_derivation",
                    )
                )

        elif hyp.label == HypothesisLabel.NOT_DUPLICATE:
            for source_str in hyp.supporting_premises:
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.SUPPORTING,
                        text=f"Supports not-duplicate: {source_str}",
                        confidence=0.8,
                        source_premises=[],
                        provenance="hypothesis_derivation",
                    )
                )
            for source_str in hyp.contradicting_premises:
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.CONTRADICTING,
                        text=f"Contradicts not-duplicate: {source_str}",
                        confidence=0.8,
                        source_premises=[],
                        provenance="hypothesis_derivation",
                    )
                )

        return result

    def _from_assessment(
        self,
        assessment: SemanticAssessment,
        hypotheses: list[Hypothesis],
        premise_map: dict[str, Premise],
    ) -> list[Evidence]:
        result: list[Evidence] = []

        for hyp in hypotheses:
            if assessment.semantic_similarity >= 0.7 and hyp.label == HypothesisLabel.DUPLICATE:
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.SUPPORTING,
                        text=f"Semantic similarity {assessment.semantic_similarity:.2f} supports duplicate",
                        confidence=min(1.0, assessment.semantic_similarity),
                        source_premises=[],
                        weight=0.6,
                        provenance="SemanticAssessment.semantic_similarity",
                    )
                )
            elif assessment.semantic_similarity < 0.4 and hyp.label == HypothesisLabel.NOT_DUPLICATE:
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.SUPPORTING,
                        text=f"Semantic similarity {assessment.semantic_similarity:.2f} supports not-duplicate",
                        confidence=min(1.0, 1 - assessment.semantic_similarity),
                        source_premises=[],
                        weight=0.6,
                        provenance="SemanticAssessment.semantic_similarity",
                    )
                )

            co = assessment.concept_overlap
            if co.overlap_score > 0 and hyp.label == HypothesisLabel.DUPLICATE:
                shared_text = ", ".join(co.shared_concepts[:5])
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.SUPPORTING,
                        text=f"Concept overlap {co.overlap_score:.2f}: {len(co.shared_concepts)} shared concepts ({shared_text})",
                        confidence=min(1.0, co.overlap_score),
                        source_premises=[],
                        weight=0.4,
                        provenance="SemanticAssessment.concept_overlap",
                    )
                )
            if co.missing_in_a or co.missing_in_b:
                target_hyp = next((h for h in hypotheses if h.label == HypothesisLabel.NOT_DUPLICATE), None)
                if target_hyp:
                    missing_text_a = ", ".join(co.missing_in_a[:5])
                    missing_text_b = ", ".join(co.missing_in_b[:5])
                    parts = []
                    if co.missing_in_a:
                        parts.append(f"A missing concepts: {missing_text_a}")
                    if co.missing_in_b:
                        parts.append(f"B missing concepts: {missing_text_b}")
                    result.append(
                        Evidence(
                            id=_make_id(),
                            hypothesis_id=target_hyp.id,
                            evidence_type=EvidenceType.SUPPORTING,
                            text="; ".join(parts),
                            confidence=0.7,
                            source_premises=[],
                            weight=0.3,
                            provenance="SemanticAssessment.concept_overlap.missing",
                        )
                    )

            eo = assessment.entity_overlap
            if eo.shared_entities and hyp.label == HypothesisLabel.DUPLICATE:
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.SUPPORTING,
                        text=f"Entity overlap: {len(eo.shared_entities)} shared entities",
                        confidence=min(1.0, eo.overlap_score),
                        source_premises=[],
                        weight=0.3,
                        provenance="SemanticAssessment.entity_overlap",
                    )
                )
            if eo.conflicts:
                target_hyp = next((h for h in hypotheses if h.label == HypothesisLabel.NOT_DUPLICATE), None)
                if target_hyp:
                    for conf in eo.conflicts[:5]:
                        result.append(
                            Evidence(
                                id=_make_id(),
                                hypothesis_id=target_hyp.id,
                                evidence_type=EvidenceType.SUPPORTING,
                                text=f"Entity conflict: {conf}",
                                confidence=0.8,
                                source_premises=[],
                                weight=0.5,
                                provenance="SemanticAssessment.entity_overlap.conflicts",
                            )
                        )

            if assessment.intent_similarity.score > 0.7 and hyp.label == HypothesisLabel.DUPLICATE:
                result.append(
                    Evidence(
                        id=_make_id(),
                        hypothesis_id=hyp.id,
                        evidence_type=EvidenceType.SUPPORTING,
                        text=f"Intent similarity {assessment.intent_similarity.score:.2f} matches",
                        confidence=assessment.intent_similarity.confidence,
                        source_premises=[],
                        weight=0.4,
                        provenance="SemanticAssessment.intent_similarity",
                    )
                )

            for conflict in assessment.conflicts:
                if hyp.label == HypothesisLabel.NOT_DUPLICATE:
                    result.append(
                        Evidence(
                            id=_make_id(),
                            hypothesis_id=hyp.id,
                            evidence_type=EvidenceType.SUPPORTING,
                            text=f"Conflict: {conflict.description}",
                            confidence=min(1.0, conflict.severity),
                            source_premises=[],
                            weight=conflict.severity,
                            provenance=f"SemanticAssessment.conflicts[{conflict.conflict_type}]",
                        )
                    )

        return result

    def _deduplicate(self, evidence: list[Evidence]) -> list[Evidence]:
        seen: set[str] = set()
        result: list[Evidence] = []
        for e in evidence:
            key = f"{e.hypothesis_id}:{e.evidence_type.value}:{e.text}"
            if key not in seen:
                seen.add(key)
                result.append(e)
        return result
