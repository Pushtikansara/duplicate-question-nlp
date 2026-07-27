from __future__ import annotations

import time

from ares.query_understanding.entity_detector import EntityDetector
from ares.query_understanding.entity_models import EntityResult
from ares.query_understanding.relationship_models import (
    ComparisonStatistics,
    RelationshipAnalysis,
    RelationshipInfo,
)
from ares.query_understanding.relationship_rules import (
    layer_1_normalize,
    layer_2_token_comparison,
    layer_3_phrase_comparison,
    layer_5_negation,
    layer_6_numeric,
    layer_7_lexical,
    layer_7b_entity_relations,
    layer_8_synthesize,
)


class RelationshipDetector:
    version: str = "1.0.0"

    def __init__(self) -> None:
        self._entity_detector = EntityDetector()

    def detect(
        self,
        question_1: str,
        question_2: str,
        entity_result: EntityResult | None = None,
    ) -> RelationshipAnalysis:
        start = time.time()

        if not question_1 or not question_2 or not question_1.strip() or not question_2.strip():
            elapsed = (time.time() - start) * 1000
            return RelationshipAnalysis(
                relationship_score=0.0,
                relationship_confidence=0.0,
                relationship_summary="Empty input",
                relationship_types=[
                    RelationshipInfo(
                        relationship_type="unknown_relationship",
                        confidence=0.0,
                        human_explanation="One or both inputs are empty",
                    )
                ],
                processing_time=round(elapsed, 2),
                version=self.version,
            )

        # Layer 1: Normalization
        n1, n2, t1, t2 = layer_1_normalize(question_1, question_2)

        # Layer 2: Token comparison
        all_relations: list[RelationshipInfo] = []
        stats: ComparisonStatistics
        all_relations, stats, t1, t2 = layer_2_token_comparison(t1, t2, n1, n2, question_1, question_2)

        # If exact match, return immediately
        if any(r.relationship_type == "exact_match" for r in all_relations):
            elapsed = (time.time() - start) * 1000
            score, conf, chain, sem_flags, risk_flags = layer_8_synthesize(
                all_relations,
                t1,
                t2,
                n1,
                n2,
                stats,
            )
            return RelationshipAnalysis(
                relationship_types=all_relations,
                relationship_score=score,
                relationship_confidence=conf,
                relationship_summary="Exact match",
                semantic_flags=sem_flags,
                risk_flags=risk_flags,
                transformation_chain=chain,
                comparison_statistics=stats,
                processing_time=round(elapsed, 2),
                version=self.version,
            )

        # Layer 3: Phrase comparison
        all_relations = layer_3_phrase_comparison(t1, t2, all_relations, n1, n2)

        # Layer 4: Entity comparison via EntityDetector
        if entity_result is None:
            entity_result = self._entity_detector.detect(question_1, question_2)
        gt1 = [e.text for e in entity_result.entities_1]
        gt2 = [e.text for e in entity_result.entities_2]
        all_relations.extend(layer_7b_entity_relations(gt1, gt2))

        # Layer 5: Negation & Polarity
        all_relations.extend(layer_5_negation(t1, t2))

        # Layer 6: Numeric, Date, Version, etc.
        all_relations.extend(layer_6_numeric(n1, n2, t1, t2))

        # Layer 7: Lexical substitution
        all_relations.extend(layer_7_lexical(t1, t2))

        # Layer 8: Synthesize
        score, conf, chain, sem_flags, risk_flags = layer_8_synthesize(
            all_relations,
            t1,
            t2,
            n1,
            n2,
            stats,
        )

        # Build summary
        summary = self._build_summary(all_relations, score, chain)

        elapsed = (time.time() - start) * 1000

        return RelationshipAnalysis(
            relationship_types=all_relations,
            relationship_score=score,
            relationship_confidence=conf,
            relationship_summary=summary,
            semantic_flags=sem_flags,
            risk_flags=risk_flags,
            transformation_chain=chain,
            comparison_statistics=stats,
            processing_time=round(elapsed, 2),
            version=self.version,
        )

    def _build_summary(
        self,
        relations: list[RelationshipInfo],
        score: float,
        chain: object,
    ) -> str:
        if not relations:
            return "No relationships detected"

        best = max(relations, key=lambda r: r.confidence)
        primary = best.relationship_type.replace("_", " ").title()

        if score >= 95:
            return f"Questions are essentially the same ({primary})"
        elif score >= 80:
            return f"Questions are very similar ({primary})"
        elif score >= 60:
            return f"Questions are somewhat similar ({primary})"
        elif score >= 40:
            return f"Questions have notable differences ({primary})"
        else:
            return f"Questions are substantially different ({primary})"
