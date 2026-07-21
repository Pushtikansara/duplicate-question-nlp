"""Tests for DefaultDecisionSupport."""

import pytest

from duplicate_question_app._semantic_intelligence.decision_support import DefaultDecisionSupport
from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    ConceptOverlap,
    Conflict,
    ContextSimilarity,
    EntityOverlap,
    IntentSimilarity,
    Recommendation,
    RelationSimilarity,
    SemanticAssessment,
)


@pytest.fixture
def decision():
    return DefaultDecisionSupport()


@pytest.fixture
def duplicate_assessment():
    return SemanticAssessment(
        semantic_similarity=0.85,
        confidence=0.8,
        concept_overlap=ConceptOverlap(overlap_score=0.8, shared_concepts=["PYTHON", "INSTALL"]),
        entity_overlap=EntityOverlap(overlap_score=0.75, shared_entities=["python"]),
        intent_similarity=IntentSimilarity(score=0.9, confidence=0.85, reason="Intent matches"),
        relation_similarity=RelationSimilarity(
            score=0.8, matching_relations=[{"source": "INSTALL", "type": "acts_on", "target": "PYTHON"}]
        ),
        context_similarity=ContextSimilarity(
            score=0.7, domain_match=True, domain_a="technology", domain_b="technology"
        ),
        conflicts=[],
    )


@pytest.fixture
def not_duplicate_assessment():
    return SemanticAssessment(
        semantic_similarity=0.15,
        confidence=0.2,
        concept_overlap=ConceptOverlap(overlap_score=0.0),
        entity_overlap=EntityOverlap(overlap_score=0.0),
        intent_similarity=IntentSimilarity(score=0.1, confidence=0.2, reason="Intents differ"),
        relation_similarity=RelationSimilarity(score=0.0),
        context_similarity=ContextSimilarity(score=0.0, domain_match=False, domain_a="tech", domain_b="cooking"),
        conflicts=[Conflict(conflict_type="domain_mismatch", description="Mismatch", severity=0.8)],
    )


@pytest.fixture
def uncertain_assessment():
    return SemanticAssessment(
        semantic_similarity=0.55,
        confidence=0.45,
        intent_similarity=IntentSimilarity(score=0.5, confidence=0.5, reason="Partial match"),
        context_similarity=ContextSimilarity(score=0.5),
        conflicts=[Conflict(conflict_type="low_semantic_confidence", description="Low confidence", severity=0.4)],
    )


class TestDefaultDecisionSupport:
    def test_duplicate_recommendation(self, decision, duplicate_assessment):
        result = decision.evaluate(duplicate_assessment)
        assert result["recommendation"] == Recommendation.DUPLICATE

    def test_not_duplicate_recommendation(self, decision, not_duplicate_assessment):
        result = decision.evaluate(not_duplicate_assessment)
        assert result["recommendation"] == Recommendation.NOT_DUPLICATE

    def test_uncertain_recommendation(self, decision, uncertain_assessment):
        result = decision.evaluate(uncertain_assessment)
        assert result["recommendation"] == Recommendation.UNCERTAIN

    def test_reason_is_provided(self, decision, duplicate_assessment):
        result = decision.evaluate(duplicate_assessment)
        assert len(result["reason"]) > 0

    def test_custom_thresholds(self):
        decision = DefaultDecisionSupport(duplicate_threshold=0.5, uncertain_threshold=0.3)
        assessment = SemanticAssessment(semantic_similarity=0.6, confidence=0.6)
        result = decision.evaluate(assessment)
        assert result["recommendation"] == Recommendation.DUPLICATE

    def test_effective_similarity_with_conflicts(self, decision):
        assessment = SemanticAssessment(
            semantic_similarity=0.9,
            confidence=0.8,
            conflicts=[Conflict(conflict_type="domain_mismatch", description="Mismatch", severity=1.0)],
        )
        result = decision.evaluate(assessment)
        assert result["effective_similarity"] < assessment.semantic_similarity
