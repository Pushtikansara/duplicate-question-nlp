"""SemanticSimilarity — computes holistic semantic similarity between two representations.

Aggregates concept, entity, relation, intent, and context similarity scores.
"""

from __future__ import annotations

from duplicate_question_app._semantic.representation import SemanticRepresentation


class DefaultSemanticSimilarity:
    def compute(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> float:
        scores = self.compute_all(rep_a, rep_b)
        return scores.get("overall", 0.0)

    def compute_all(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict:
        from duplicate_question_app._semantic_intelligence.concept_matcher import DefaultConceptMatcher
        from duplicate_question_app._semantic_intelligence.confidence_fusion import DefaultConfidenceFusion
        from duplicate_question_app._semantic_intelligence.context_matcher import DefaultContextMatcher
        from duplicate_question_app._semantic_intelligence.entity_matcher import DefaultEntityMatcher
        from duplicate_question_app._semantic_intelligence.intent_matcher import DefaultIntentMatcher
        from duplicate_question_app._semantic_intelligence.relation_matcher import DefaultRelationMatcher

        concept_result = DefaultConceptMatcher().match(rep_a, rep_b)
        entity_result = DefaultEntityMatcher().match(rep_a, rep_b)
        relation_result = DefaultRelationMatcher().match(rep_a, rep_b)
        intent_result = DefaultIntentMatcher().match(rep_a, rep_b)
        context_result = DefaultContextMatcher().match(rep_a, rep_b)

        scores = {
            "concept_similarity": concept_result["overlap_score"],
            "entity_similarity": entity_result["overlap_score"],
            "relation_similarity": relation_result["score"],
            "intent_similarity": intent_result["score"],
            "context_similarity": context_result["score"],
        }

        fusion = DefaultConfidenceFusion().compute(scores)

        return {
            **scores,
            "overall": fusion["overall"],
            "weighted_scores": fusion["weighted_scores"],
            "weights": fusion["weights"],
        }


SemanticSimilarity = DefaultSemanticSimilarity
