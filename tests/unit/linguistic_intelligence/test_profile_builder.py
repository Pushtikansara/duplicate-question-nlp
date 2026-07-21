"""Tests for LinguisticProfileBuilder."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.profile_builder import LinguisticProfileBuilder
from duplicate_question_app._perception.cognitive_representation import (
    CognitiveRepresentation,
    LinguisticFeatures,
    Metadata,
    ValidationReport,
)


def _make_rep(text: str = "How to install Python on Ubuntu?") -> CognitiveRepresentation:
    return CognitiveRepresentation(
        raw_text=text,
        normalized_text=text.lower(),
        language="en",
        language_confidence=0.95,
        tokens=[],
        sentences=[],
        linguistic=LinguisticFeatures(),
        metadata=Metadata(),
        validation=ValidationReport(),
    )


class TestLinguisticProfileBuilder:
    def test_build_populates_language(self):
        builder = LinguisticProfileBuilder()
        rep = _make_rep()
        result = builder.build(rep)
        assert result.success
        assert result.profile.language == "en"
        assert result.profile.language_confidence == 0.95

    def test_build_populates_intent(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep())
        assert result.profile.intent is not None

    def test_build_populates_entities(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep("How to install Python on Ubuntu?"))
        assert result.profile.entity_count >= 0
        if result.profile.entity_count > 0:
            assert len(result.profile.entities) > 0

    def test_build_populates_keywords(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep())
        assert len(result.profile.keywords) > 0

    def test_build_populates_question_type(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep("What is machine learning?"))
        assert result.profile.question_type is not None

    def test_build_populates_complexity(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep())
        assert result.profile.complexity.overall >= 0.0
        assert result.profile.token_statistics.total > 0

    def test_build_populates_domain(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep("How to train a neural network with PyTorch?"))
        assert result.profile.domain is not None
        assert result.profile.domain_confidence > 0

    def test_build_populates_analysis_confidence(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep())
        assert result.profile.analysis_confidence.overall >= 0.0

    def test_build_populates_quality_metrics(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep())
        assert result.profile.quality_metrics.quality_score > 0.0
        assert result.profile.quality_metrics.coverage > 0.0

    def test_build_stage_timing(self):
        builder = LinguisticProfileBuilder()
        result = builder.build(_make_rep())
        assert result.timing_ms > 0
        assert len(result.stage_timing) > 0

    def test_build_empty_text(self):
        builder = LinguisticProfileBuilder()
        rep = _make_rep("")
        result = builder.build(rep)
        assert not result.success
