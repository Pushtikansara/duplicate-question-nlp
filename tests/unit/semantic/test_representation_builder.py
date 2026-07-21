"""Tests for RepresentationBuilder integration."""

import pytest

from duplicate_question_app._linguistic_intelligence.profile import AnalysisConfidence, LinguisticProfile
from duplicate_question_app._semantic.representation_builder import RepresentationBuilder


@pytest.fixture
def builder():
    return RepresentationBuilder()


@pytest.fixture
def install_profile():
    return LinguisticProfile(
        language="en",
        language_confidence=0.98,
        entities=[
            {"value": "Python", "type": "language", "confidence": 0.95},
            {"value": "Ubuntu", "type": "OS", "confidence": 0.9},
        ],
        entity_count=2,
        intent="install",
        intent_confidence=0.92,
        domain="technology",
        domain_confidence=0.85,
        question_type="how",
        analysis_confidence=AnalysisConfidence(overall=0.9),
    )


@pytest.fixture
def debug_profile():
    return LinguisticProfile(
        language="en",
        language_confidence=0.97,
        entities=[
            {"value": "Python", "type": "language", "confidence": 0.9},
            {"value": "Windows", "type": "OS", "confidence": 0.85},
        ],
        entity_count=2,
        intent="debug",
        intent_confidence=0.8,
        domain="technology",
        domain_confidence=0.7,
        question_type="why",
        negation=True,
        negation_count=1,
        analysis_confidence=AnalysisConfidence(overall=0.85),
    )


class TestRepresentationBuilder:
    def test_build_returns_semantic_representation(self, builder, install_profile):
        result = builder.build(install_profile)
        assert result is not None
        assert result.domain == "technology"
        assert result.intent_summary == "install"

    def test_build_extracts_concepts(self, builder, install_profile):
        result = builder.build(install_profile)
        assert len(result.concepts) > 0

    def test_build_creates_semantic_graph(self, builder, install_profile):
        result = builder.build(install_profile)
        assert result.semantic_graph is not None
        assert result.semantic_graph.node_count() > 0

    def test_build_creates_relations(self, builder, install_profile):
        result = builder.build(install_profile)
        assert len(result.relationships) > 0

    def test_build_assigns_semantic_roles(self, builder, install_profile):
        result = builder.build(install_profile)
        assert len(result.semantic_roles) > 0

    def test_build_context(self, builder, install_profile):
        result = builder.build(install_profile)
        assert "language" in result.context
        assert result.context["language"] == "en"

    def test_build_confidence(self, builder, install_profile):
        result = builder.build(install_profile)
        assert result.semantic_confidence > 0
        assert "overall" in result.confidence_detail

    def test_build_processing_metadata(self, builder, install_profile):
        result = builder.build(install_profile)
        assert result.processing_metadata.total_concepts > 0
        assert result.processing_metadata.total_relations > 0
        assert result.processing_metadata.processing_time_ms > 0

    def test_build_with_negation(self, builder, debug_profile):
        result = builder.build(debug_profile)
        assert result.intent_summary == "debug"
        assert len(result.ambiguities) > 0

    def test_build_sets_actions_and_objects(self, builder, install_profile):
        result = builder.build(install_profile)
        assert len(result.actions) > 0

    def test_to_dict_from_builder(self, builder, install_profile):
        result = builder.build(install_profile)
        d = result.to_dict()
        assert d["domain"] == "technology"
        assert d["semantic_confidence"] > 0
        assert d["semantic_graph"] is not None
        assert len(d["concepts"]) > 0
        assert len(d["relationships"]) > 0
