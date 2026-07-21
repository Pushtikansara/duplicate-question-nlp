"""Tests for DefaultRelationExtractor."""

import pytest

from duplicate_question_app._linguistic_intelligence.profile import AnalysisConfidence, LinguisticProfile
from duplicate_question_app._semantic.relation_extractor import DefaultRelationExtractor
from duplicate_question_app._semantic.semantic_graph import SemanticNode


@pytest.fixture
def extractor():
    return DefaultRelationExtractor()


@pytest.fixture
def basic_profile():
    return LinguisticProfile(
        intent="install",
        intent_confidence=0.9,
        domain="technology",
        domain_confidence=0.8,
        analysis_confidence=AnalysisConfidence(),
    )


class TestDefaultRelationExtractor:
    def test_action_to_entity_relation(self, extractor, basic_profile):
        concepts = [
            SemanticNode(id="INSTALL", label="install", node_type="action", confidence=0.9),
            SemanticNode(id="PYTHON", label="python", node_type="entity", confidence=0.8),
        ]
        relations = extractor.extract(basic_profile, concepts)
        types = [(r.source_id, r.target_id, r.relation_type) for r in relations]
        assert ("INSTALL", "PYTHON", "acts_on") in types

    def test_entity_to_domain_relation(self, extractor, basic_profile):
        concepts = [
            SemanticNode(id="PYTHON", label="python", node_type="entity", confidence=0.8),
            SemanticNode(id="TECHNOLOGY", label="technology", node_type="domain", confidence=0.7),
        ]
        relations = extractor.extract(basic_profile, concepts)
        types = [(r.source_id, r.target_id, r.relation_type) for r in relations]
        assert ("PYTHON", "TECHNOLOGY", "runs_on") in types

    def test_same_type_relation(self, extractor, basic_profile):
        concepts = [
            SemanticNode(id="PYTHON", label="python", node_type="concept", confidence=0.8),
            SemanticNode(id="JAVA", label="java", node_type="concept", confidence=0.7),
        ]
        relations = extractor.extract(basic_profile, concepts)
        types = [(r.source_id, r.target_id, r.relation_type) for r in relations]
        assert ("PYTHON", "JAVA", "related_to") in types

    def test_no_duplicate_relations(self, extractor, basic_profile):
        concepts = [
            SemanticNode(id="INSTALL", label="install", node_type="action"),
            SemanticNode(id="PYTHON", label="python", node_type="entity", confidence=0.8),
        ]
        relations = extractor.extract(basic_profile, concepts)
        pairs = [(r.source_id, r.target_id, r.relation_type) for r in relations]
        assert len(pairs) == len(set(pairs))

    def test_intent_relation(self, extractor, basic_profile):
        concepts = [
            SemanticNode(id="INSTALL", label="install", node_type="action", confidence=0.9),
            SemanticNode(id="DEBUG", label="debug", node_type="action", confidence=0.7),
        ]
        relations = extractor.extract(basic_profile, concepts)
        types = [(r.source_id, r.target_id, r.relation_type) for r in relations]
        assert ("INSTALL", "DEBUG", "requests") in types

    def test_empty_concepts(self, extractor, basic_profile):
        relations = extractor.extract(basic_profile, [])
        assert relations == []
