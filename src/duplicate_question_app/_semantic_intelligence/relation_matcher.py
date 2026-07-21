"""RelationMatcher — compares semantic relations between two SemanticRepresentations.

Matches relations through normalized concept identities.

Example:
    INSTALL acts_on PYTHON  should match  SETUP acts_on PYTHON
    because both involve the same normalized concepts and relation type.
"""

from __future__ import annotations

from duplicate_question_app._semantic.representation import SemanticRepresentation


class DefaultRelationMatcher:
    def _concept_normalized_map(self, rep: SemanticRepresentation) -> dict[str, str]:
        return {c.id: c.normalized_form for c in rep.concepts}

    def _relation_signature(self, relation, norm_map: dict[str, str]) -> tuple:
        src = norm_map.get(relation.source_id, relation.source_id)
        tgt = norm_map.get(relation.target_id, relation.target_id)
        return (src, relation.relation_type, tgt)

    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict:
        norm_a = self._concept_normalized_map(rep_a)
        norm_b = self._concept_normalized_map(rep_b)

        sigs_a = {self._relation_signature(r, norm_a) for r in rep_a.relationships}
        sigs_b = {self._relation_signature(r, norm_b) for r in rep_b.relationships}

        matching = sigs_a & sigs_b
        only_a = sigs_a - sigs_b
        only_b = sigs_b - sigs_a

        total = len(sigs_a | sigs_b)
        score = len(matching) / total if total > 0 else 0.0

        return {
            "score": score,
            "matching_relations": [{"source": s, "type": t, "target": tg} for s, t, tg in sorted(matching)],
            "missing_in_a": [{"source": s, "type": t, "target": tg} for s, t, tg in sorted(only_b)],
            "missing_in_b": [{"source": s, "type": t, "target": tg} for s, t, tg in sorted(only_a)],
            "total_a": len(sigs_a),
            "total_b": len(sigs_b),
            "detail": {
                "signatures_a": sorted(sigs_a),
                "signatures_b": sorted(sigs_b),
            },
        }


RelationMatcher = DefaultRelationMatcher
