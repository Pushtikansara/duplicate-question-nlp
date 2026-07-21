"""Tests for DefaultEvidenceBuilder."""

import pytest

from duplicate_question_app._semantic_intelligence.evidence_builder import DefaultEvidenceBuilder
from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    ConceptOverlap,
    Conflict,
    ContextSimilarity,
    EntityOverlap,
    IntentSimilarity,
    RelationSimilarity,
    SemanticAssessment,
)


@pytest.fixture
def builder():
    return DefaultEvidenceBuilder()


@pytest.fixture
def high_similarity_assessment():
    return SemanticAssessment(
        semantic_similarity=0.85,
        concept_overlap=ConceptOverlap(
            overlap_score=0.8, shared_concepts=["PYTHON", "INSTALL"], missing_in_a=[], missing_in_b=[]
        ),
        entity_overlap=EntityOverlap(
            overlap_score=0.75, shared_entities=["python"], missing_in_a=[], missing_in_b=[], conflicts=[]
        ),
        intent_similarity=IntentSimilarity(score=0.9, confidence=0.85, reason="Intent matches"),
        relation_similarity=RelationSimilarity(
            score=0.8, matching_relations=[{"source": "INSTALL", "type": "acts_on", "target": "PYTHON"}]
        ),
        context_similarity=ContextSimilarity(
            score=0.7, domain_match=True, domain_a="technology", domain_b="technology"
        ),
        conflicts=[],
        confidence=0.85,
    )


@pytest.fixture
def low_similarity_assessment():
    return SemanticAssessment(
        semantic_similarity=0.2,
        concept_overlap=ConceptOverlap(
            overlap_score=0.0, shared_concepts=[], missing_in_a=["PYTHON"], missing_in_b=["JAVA"]
        ),
        entity_overlap=EntityOverlap(
            overlap_score=0.0,
            shared_entities=[],
            missing_in_a=["python"],
            missing_in_b=["java"],
            conflicts=["Entity type conflict"],
        ),
        intent_similarity=IntentSimilarity(score=0.1, confidence=0.3, reason="Intents differ"),
        relation_similarity=RelationSimilarity(score=0.0, total_a=1, total_b=1),
        context_similarity=ContextSimilarity(score=0.0, domain_match=False, domain_a="technology", domain_b="science"),
        conflicts=[Conflict(conflict_type="domain_mismatch", description="Domain mismatch", severity=0.7)],
        confidence=0.2,
    )


class TestDefaultEvidenceBuilder:
    def test_build_high_similarity(self, builder, high_similarity_assessment):
        evidence = builder.build(high_similarity_assessment)
        assert len(evidence) > 0
        categories = [e["category"] for e in evidence]
        assert "intent" in categories
        assert "domain" in categories
        assert "concepts" in categories
        assert "entities" in categories
        assert "overall" in categories
        intent_evidence = [e for e in evidence if e["category"] == "intent"]
        assert intent_evidence[0]["status"] == "match"

    def test_build_low_similarity(self, builder, low_similarity_assessment):
        evidence = builder.build(low_similarity_assessment)
        assert len(evidence) > 0
        intent_evidence = [e for e in evidence if e["category"] == "intent"]
        assert intent_evidence[0]["status"] == "mismatch"
        domain_evidence = [e for e in evidence if e["category"] == "domain"]
        assert domain_evidence[0]["status"] == "mismatch"
        overall_evidence = [e for e in evidence if e["category"] == "overall"]
        assert overall_evidence[0]["status"] == "low_confidence"

    def test_evidence_contains_required_fields(self, builder, high_similarity_assessment):
        evidence = builder.build(high_similarity_assessment)
        for item in evidence:
            assert "category" in item
            assert "status" in item
            assert "message" in item
            assert "confidence" in item
