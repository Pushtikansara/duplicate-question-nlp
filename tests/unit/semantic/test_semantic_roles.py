"""Tests for DefaultSemanticRoleAnalyzer."""

import pytest

from duplicate_question_app._linguistic_intelligence.profile import AnalysisConfidence, LinguisticProfile
from duplicate_question_app._semantic.semantic_graph import SemanticNode
from duplicate_question_app._semantic.semantic_roles import DefaultSemanticRoleAnalyzer


@pytest.fixture
def analyzer():
    return DefaultSemanticRoleAnalyzer()


@pytest.fixture
def basic_profile():
    return LinguisticProfile(intent="install", intent_confidence=0.9, analysis_confidence=AnalysisConfidence())


class TestDefaultSemanticRoleAnalyzer:
    def test_action_role(self, analyzer, basic_profile):
        concepts = [SemanticNode(id="INSTALL", label="install", node_type="action")]
        roles = analyzer.analyze(basic_profile, concepts)
        assert "ACTION" in roles
        assert any(n.id == "INSTALL" for n in roles["ACTION"])

    def test_target_role_from_entity(self, analyzer, basic_profile):
        concepts = [SemanticNode(id="PYTHON", label="python", node_type="entity")]
        roles = analyzer.analyze(basic_profile, concepts)
        assert "TARGET" in roles
        assert any(n.id == "PYTHON" for n in roles["TARGET"])

    def test_location_role_from_domain(self, analyzer):
        concepts = [SemanticNode(id="LINUX", label="linux", node_type="domain")]
        profile = LinguisticProfile(domain="linux", domain_confidence=0.8, analysis_confidence=AnalysisConfidence())
        roles = analyzer.analyze(profile, concepts)
        assert "LOCATION" in roles

    def test_to_assignments(self, analyzer):
        roles = {
            "ACTION": [SemanticNode(id="A", label="a", node_type="action", confidence=0.9)],
            "TARGET": [SemanticNode(id="B", label="b", node_type="entity", confidence=0.8)],
        }
        assignments = DefaultSemanticRoleAnalyzer.to_assignments(roles)
        assert len(assignments) == 2
        assert any(a.role == "ACTION" and a.concept_ids == ["A"] for a in assignments)
        assert any(a.role == "TARGET" and a.concept_ids == ["B"] for a in assignments)

    def test_empty_roles(self, analyzer, basic_profile):
        roles = analyzer.analyze(basic_profile, [])
        for role_list in roles.values():
            assert role_list == []

    def test_to_assignments_empty(self):
        assert DefaultSemanticRoleAnalyzer.to_assignments({}) == []
