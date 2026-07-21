"""Tests for DefaultContextBuilder."""

import pytest

from duplicate_question_app._linguistic_intelligence.profile import (
    AnalysisConfidence,
    LexicalFeatures,
    LinguisticProfile,
    QualityMetricsData,
    ReadabilityScore,
    SentenceStatistics,
    TokenStatistics,
)
from duplicate_question_app._semantic.context_builder import DefaultContextBuilder
from duplicate_question_app._semantic.representation import SemanticRepresentation


@pytest.fixture
def builder():
    return DefaultContextBuilder()


@pytest.fixture
def profile():
    return LinguisticProfile(
        language="en",
        language_confidence=0.98,
        intent="install",
        intent_confidence=0.9,
        domain="technology",
        domain_confidence=0.8,
        question_type="how",
        entity_count=2,
        analysis_confidence=AnalysisConfidence(overall=0.95),
        lexical_features=LexicalFeatures(lexical_density=0.5),
        readability=ReadabilityScore(flesch_reading_ease=70.0),
        token_statistics=TokenStatistics(total=10),
        sentence_statistics=SentenceStatistics(total=2),
        quality_metrics=QualityMetricsData(quality_score=0.85),
    )


class TestDefaultContextBuilder:
    def test_build_language(self, builder, profile):
        context = builder.build(profile, SemanticRepresentation())
        assert context["language"] == "en"
        assert context["language_confidence"] == 0.98

    def test_build_question(self, builder, profile):
        context = builder.build(profile, SemanticRepresentation())
        assert context["is_question"] is True
        assert context["question_type"] == "how"

    def test_build_negation(self, builder, profile):
        context = builder.build(profile, SemanticRepresentation())
        assert context["has_negation"] is False
        assert "negation_present" not in context

    def test_build_counts(self, builder, profile):
        context = builder.build(profile, SemanticRepresentation())
        assert context["entity_count"] == 2
        assert context["word_count"] == 10

    def test_build_empty_profile(self, builder):
        empty = LinguisticProfile(analysis_confidence=AnalysisConfidence())
        context = builder.build(empty, SemanticRepresentation())
        assert context["language"] == ""
        assert context["is_question"] is False
