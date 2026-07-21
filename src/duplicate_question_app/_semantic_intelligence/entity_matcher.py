"""EntityMatcher — compares entities between two SemanticRepresentations.

Measures entity overlap, detects conflicts, and identifies missing entities.
"""

from __future__ import annotations

from duplicate_question_app._semantic.representation import SemanticRepresentation


class DefaultEntityMatcher:
    def _entity_key(self, entity: dict) -> str:
        return entity.get("name", entity.get("text", entity.get("label", ""))).lower().strip()

    def _entity_type(self, entity: dict) -> str:
        return entity.get("type", entity.get("entity_type", "unknown"))

    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict:
        entities_a = {self._entity_key(e): e for e in rep_a.entities}
        entities_b = {self._entity_key(e): e for e in rep_b.entities}

        keys_a = set(entities_a.keys())
        keys_b = set(entities_b.keys())

        shared = keys_a & keys_b
        only_a = keys_a - keys_b
        only_b = keys_b - keys_a

        total = len(keys_a | keys_b)
        overlap_score = len(shared) / total if total > 0 else 0.0

        conflicts = []
        for key in shared:
            type_a = self._entity_type(entities_a[key])
            type_b = self._entity_type(entities_b[key])
            if type_a != type_b:
                conflicts.append(f"Entity '{key}' has type '{type_a}' in A but '{type_b}' in B")

        return {
            "overlap_score": overlap_score,
            "shared_entities": sorted(shared),
            "missing_in_a": sorted(only_b),
            "missing_in_b": sorted(only_a),
            "conflicts": conflicts,
            "total_a": len(keys_a),
            "total_b": len(keys_b),
            "detail": {
                "entity_keys_a": sorted(keys_a),
                "entity_keys_b": sorted(keys_b),
            },
        }


EntityMatcher = DefaultEntityMatcher
