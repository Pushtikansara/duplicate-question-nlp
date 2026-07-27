from __future__ import annotations

from ares.query_understanding.entity_matcher import match_entities
from ares.query_understanding.entity_models import (
    Entity,
    EntityPairMatch,
    EntityResult,
)
from ares.query_understanding.entity_rules import extract_entities


class EntityDetector:
    def detect(self, question_1: str, question_2: str) -> EntityResult:
        if not question_1 and not question_2:
            return EntityResult(entity_relationship="no_entities")

        entities_1 = extract_entities(question_1) if question_1 else []
        entities_2 = extract_entities(question_2) if question_2 else []

        shared, unique_1, unique_2 = match_entities(entities_1, entities_2)

        scores = self._compute_overlap(entities_1, entities_2, shared)
        relationship = self._determine_relationship(entities_1, entities_2, shared)

        return EntityResult(
            entities_1=entities_1,
            entities_2=entities_2,
            shared_entities=shared,
            unique_entities_q1=unique_1,
            unique_entities_q2=unique_2,
            entity_overlap_score=round(scores["overall"], 4),
            entity_relationship=relationship,
        )

    def _compute_overlap(
        self,
        entities_1: list[Entity],
        entities_2: list[Entity],
        shared: list[EntityPairMatch],
    ) -> dict[str, float]:
        if not entities_1 and not entities_2:
            return {"overall": 0.0, "exact": 0.0, "partial": 0.0}

        exact = sum(1 for m in shared if m.match_type == "exact_match")
        partial = sum(
            1
            for m in shared
            if m.match_type
            in (
                "case_difference",
                "partial_match",
                "abbreviation",
                "version_difference",
                "numeric_difference",
            )
        )

        total_unique = len(entities_1) + len(entities_2)
        matched_pairs = len(shared)

        if total_unique == 0:
            return {"overall": 0.0, "exact": 0.0, "partial": 0.0}

        base_score = (exact + partial * 0.5) / max(total_unique / 2, 1)
        overall = min(1.0, base_score * 1.5)

        return {
            "overall": overall,
            "exact": round(exact / max(matched_pairs, 1), 4) if matched_pairs else 0.0,
            "partial": round(partial / max(matched_pairs, 1), 4) if matched_pairs else 0.0,
        }

    def _determine_relationship(
        self,
        entities_1: list[Entity],
        entities_2: list[Entity],
        shared: list[EntityPairMatch],
    ) -> str:
        if not entities_1 and not entities_2:
            return "no_entities"

        exact_matches = [m for m in shared if m.match_type == "exact_match"]
        partial_matches = [m for m in shared if m not in exact_matches]

        if exact_matches:
            return "same_entity"
        if partial_matches:
            return "related_entities"
        if entities_1 and entities_2 and not shared:
            return "different_entities"
        if entities_1 or entities_2:
            return "overlapping"

        return "unknown"
