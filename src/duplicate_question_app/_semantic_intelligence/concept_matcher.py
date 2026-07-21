"""ConceptMatcher — compares normalized concepts between two SemanticRepresentations.

Measures overlap, detects missing concepts, and supports synonym handling
through normalization.
"""

from __future__ import annotations

from duplicate_question_app._semantic.representation import SemanticRepresentation


class DefaultConceptMatcher:
    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict:
        normalized_a = {c.normalized_form for c in rep_a.concepts}
        normalized_b = {c.normalized_form for c in rep_b.concepts}

        shared = normalized_a & normalized_b
        only_a = normalized_a - normalized_b
        only_b = normalized_b - normalized_a

        total = len(normalized_a | normalized_b)
        overlap_score = len(shared) / total if total > 0 else 0.0

        return {
            "overlap_score": overlap_score,
            "shared_concepts": sorted(shared),
            "missing_in_a": sorted(only_b),
            "missing_in_b": sorted(only_a),
            "total_a": len(normalized_a),
            "total_b": len(normalized_b),
            "detail": {
                "normalized_a": sorted(normalized_a),
                "normalized_b": sorted(normalized_b),
            },
        }


ConceptMatcher = DefaultConceptMatcher
