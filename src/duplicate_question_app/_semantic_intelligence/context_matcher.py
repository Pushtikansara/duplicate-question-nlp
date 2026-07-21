"""ContextMatcher — compares context between two SemanticRepresentations.

Compares domain, context dictionaries, and constraints.
"""

from __future__ import annotations

from duplicate_question_app._semantic.representation import SemanticRepresentation


class DefaultContextMatcher:
    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict:
        domain_a = rep_a.domain.lower().strip() if rep_a.domain else None
        domain_b = rep_b.domain.lower().strip() if rep_b.domain else None
        domain_match = domain_a == domain_b if domain_a and domain_b else False

        keys_a = set(rep_a.context.keys())
        keys_b = set(rep_b.context.keys())
        shared_keys = keys_a & keys_b
        total_unique = len(keys_a | keys_b)
        key_overlap = len(shared_keys) / total_unique if total_unique > 0 else 0.0

        value_matches = 0
        for key in shared_keys:
            if rep_a.context[key] == rep_b.context[key]:
                value_matches += 1
        value_agreement = value_matches / len(shared_keys) if shared_keys else 0.0

        constraints_a = {c.lower().strip() for c in rep_a.constraints}
        constraints_b = {c.lower().strip() for c in rep_b.constraints}
        shared_constraints = constraints_a & constraints_b
        total_constraints = len(constraints_a | constraints_b)
        constraints_match = len(shared_constraints) / total_constraints if total_constraints > 0 else 1.0

        score = 0.0
        if domain_a and domain_b:
            score += 0.4 if domain_match else 0.0
        else:
            score += 0.2
        score += 0.3 * key_overlap
        score += 0.3 * value_agreement

        return {
            "score": score,
            "domain_match": domain_match,
            "domain_a": rep_a.domain,
            "domain_b": rep_b.domain,
            "shared_context_keys": sorted(shared_keys),
            "constraints_match": constraints_match,
            "detail": {
                "key_overlap": key_overlap,
                "value_agreement": value_agreement,
                "shared_constraints": sorted(shared_constraints),
                "total_constraints_a": len(constraints_a),
                "total_constraints_b": len(constraints_b),
            },
        }


ContextMatcher = DefaultContextMatcher
