"""EvidenceBuilder — generates explainable evidence from a SemanticAssessment.

Produces structured evidence items with category, status, message, and confidence.
This evidence feeds the downstream Explainability Engine.
"""

from __future__ import annotations

from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    SemanticAssessment,
)


class DefaultEvidenceBuilder:
    def build(self, assessment: SemanticAssessment) -> list[dict]:
        evidence = []

        intent = assessment.intent_similarity
        if intent.score >= 0.8:
            evidence.append(self._item("intent", "match", "Intent matches", intent.confidence))
        elif intent.score >= 0.4:
            evidence.append(
                self._item("intent", "partial", f"Partial intent match: {intent.reason}", intent.confidence)
            )
        else:
            evidence.append(self._item("intent", "mismatch", f"Intent mismatch: {intent.reason}", intent.confidence))

        context = assessment.context_similarity
        if context.domain_match:
            evidence.append(self._item("domain", "match", "Domain matches", 1.0))
        elif context.domain_a and context.domain_b:
            evidence.append(
                self._item("domain", "mismatch", f"Domain mismatch: '{context.domain_a}' vs '{context.domain_b}'", 0.7)
            )
        else:
            evidence.append(self._item("domain", "info", "Domain information incomplete", 0.5))

        concept = assessment.concept_overlap
        if concept.overlap_score >= 0.5:
            evidence.append(
                self._item(
                    "concepts",
                    "match",
                    f"Concept overlap: {concept.overlap_score:.2f} ({len(concept.shared_concepts)} shared)",
                    concept.overlap_score,
                )
            )
        else:
            evidence.append(
                self._item(
                    "concepts",
                    "low_overlap",
                    f"Low concept overlap: {concept.overlap_score:.2f}",
                    concept.overlap_score,
                )
            )

        if concept.missing_in_a:
            evidence.append(
                self._item("concepts", "warning", f"Missing in A: {', '.join(concept.missing_in_a[:5])}", 0.6)
            )
        if concept.missing_in_b:
            evidence.append(
                self._item("concepts", "warning", f"Missing in B: {', '.join(concept.missing_in_b[:5])}", 0.6)
            )

        entity = assessment.entity_overlap
        if entity.overlap_score >= 0.5:
            evidence.append(
                self._item(
                    "entities",
                    "match",
                    f"Entity overlap: {entity.overlap_score:.2f} ({len(entity.shared_entities)} shared)",
                    entity.overlap_score,
                )
            )
        else:
            evidence.append(
                self._item(
                    "entities", "low_overlap", f"Low entity overlap: {entity.overlap_score:.2f}", entity.overlap_score
                )
            )

        for conflict in entity.conflicts:
            evidence.append(self._item("entities", "conflict", conflict, 0.8))

        relation = assessment.relation_similarity
        if relation.matching_relations:
            evidence.append(
                self._item(
                    "relations", "match", f"{len(relation.matching_relations)} matching relations", relation.score
                )
            )
        elif relation.total_a > 0 or relation.total_b > 0:
            evidence.append(self._item("relations", "mismatch", "No matching relations found", relation.score))
        else:
            evidence.append(self._item("relations", "info", "No relations available for comparison", 0.5))

        for conflict in assessment.conflicts:
            evidence.append(
                self._item(
                    conflict.conflict_type,
                    "conflict",
                    conflict.description,
                    1.0 - conflict.severity * 0.5,
                )
            )

        if assessment.confidence >= 0.7:
            evidence.append(
                self._item(
                    "overall",
                    "match",
                    f"High confidence assessment: {assessment.confidence:.2f}",
                    assessment.confidence,
                )
            )
        elif assessment.confidence >= 0.4:
            evidence.append(
                self._item(
                    "overall",
                    "uncertain",
                    f"Moderate confidence assessment: {assessment.confidence:.2f}",
                    assessment.confidence,
                )
            )
        else:
            evidence.append(
                self._item(
                    "overall",
                    "low_confidence",
                    f"Low confidence assessment: {assessment.confidence:.2f}",
                    assessment.confidence,
                )
            )

        return evidence

    def _item(self, category: str, status: str, message: str, confidence: float) -> dict:
        return {
            "category": category,
            "status": status,
            "message": message,
            "confidence": confidence,
        }


EvidenceBuilder = DefaultEvidenceBuilder
