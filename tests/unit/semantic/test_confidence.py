"""Tests for DefaultSemanticConfidence."""

import pytest

from duplicate_question_app._linguistic_intelligence.profile import AnalysisConfidence, LinguisticProfile
from duplicate_question_app._semantic.confidence import DefaultSemanticConfidence
from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRepresentation
from duplicate_question_app._semantic.semantic_graph import SemanticGraph, SemanticNode
from duplicate_question_app._semantic.semantic_graph import SemanticRelation as GraphRelation


@pytest.fixture
def confidence():
    return DefaultSemanticConfidence()


class TestDefaultSemanticConfidence:
    def test_zero_confidence_on_empty(self, confidence):
        profile = LinguisticProfile(analysis_confidence=AnalysisConfidence())
        detail = confidence.compute(profile, SemanticRepresentation())
        assert "overall" in detail
        assert 0.0 <= detail["overall"] <= 1.0

    def test_high_confidence(self, confidence):
        profile = LinguisticProfile(
            language="en",
            language_confidence=0.98,
            intent="install",
            intent_confidence=0.9,
            domain="technology",
            domain_confidence=0.8,
            entities=[
                {"value": "Python", "type": "language", "confidence": 0.95},
                {"value": "Ubuntu", "type": "OS", "confidence": 0.9},
            ],
            entity_count=2,
            analysis_confidence=AnalysisConfidence(overall=0.95),
        )
        graph = SemanticGraph()
        graph.add_node(SemanticNode(id="INSTALL", label="install", node_type="action"))
        graph.add_node(SemanticNode(id="PYTHON", label="python", node_type="entity"))
        graph.add_edge(GraphRelation(source_id="INSTALL", target_id="PYTHON", relation_type="acts_on"))
        repr = SemanticRepresentation(semantic_graph=graph)
        repr.concepts = [SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL")]
        detail = confidence.compute(profile, repr)
        assert detail["overall"] > 0.4

    def test_confidence_detail_keys(self, confidence):
        profile = LinguisticProfile(analysis_confidence=AnalysisConfidence())
        detail = confidence.compute(profile, SemanticRepresentation())
        expected_keys = {
            "concept_coverage",
            "avg_entity_confidence",
            "relation_completeness",
            "linguistic_confidence",
            "intent_confidence",
            "domain_confidence",
            "overall",
        }
        assert set(detail.keys()) == expected_keys
