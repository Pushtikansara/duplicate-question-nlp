"""Tests for DefaultAmbiguityDetector."""

import pytest

from duplicate_question_app._linguistic_intelligence.profile import AnalysisConfidence, Keyword, LinguisticProfile
from duplicate_question_app._semantic.ambiguity_detector import DefaultAmbiguityDetector
from duplicate_question_app._semantic.representation import SemanticRepresentation


@pytest.fixture
def detector():
    return DefaultAmbiguityDetector()


@pytest.fixture
def clean_profile():
    return LinguisticProfile(
        language="en",
        language_confidence=0.98,
        intent="install",
        intent_confidence=0.9,
        domain="technology",
        domain_confidence=0.8,
        question_type="how",
        entity_count=3,
        analysis_confidence=AnalysisConfidence(overall=0.95),
    )


class TestDefaultAmbiguityDetector:
    def test_clean_profile_no_ambiguities(self, detector, clean_profile):
        ambigs = detector.detect(clean_profile, SemanticRepresentation())
        types = [a.type for a in ambigs]
        assert "low_confidence" not in types
        assert "negation_present" not in types
        assert "contradiction_present" not in types

    def test_low_confidence_detected(self, detector):
        profile = LinguisticProfile(
            language="en",
            language_confidence=0.3,
            intent="unknown",
            intent_confidence=0.1,
            domain="general",
            domain_confidence=0.2,
            analysis_confidence=AnalysisConfidence(overall=0.3),
        )
        ambigs = detector.detect(profile, SemanticRepresentation())
        types = [a.type for a in ambigs]
        assert "low_confidence" in types

    def test_negation_detected(self, detector):
        profile = LinguisticProfile(
            language="en",
            language_confidence=1.0,
            negation=True,
            negation_count=1,
            analysis_confidence=AnalysisConfidence(overall=0.8),
        )
        ambigs = detector.detect(profile, SemanticRepresentation())
        types = [a.type for a in ambigs]
        assert "negation_present" in types

    def test_contradiction_detected(self, detector):
        profile = LinguisticProfile(
            language="en",
            language_confidence=1.0,
            contradiction=True,
            contradiction_score=0.7,
            analysis_confidence=AnalysisConfidence(overall=0.8),
        )
        ambigs = detector.detect(profile, SemanticRepresentation())
        types = [a.type for a in ambigs]
        assert "contradiction_present" in types

    def test_unknown_domain_detected(self, detector):
        profile = LinguisticProfile(
            language="en",
            language_confidence=1.0,
            domain="general",
            domain_confidence=0.0,
            analysis_confidence=AnalysisConfidence(overall=0.8),
        )
        ambigs = detector.detect(profile, SemanticRepresentation())
        types = [a.type for a in ambigs]
        assert "unknown_domain" in types

    def test_no_entities_detected(self, detector):
        profile = LinguisticProfile(
            language="en",
            language_confidence=1.0,
            keywords=[Keyword(word="test", score=0.5)],
            entity_count=0,
            analysis_confidence=AnalysisConfidence(overall=0.8),
        )
        ambigs = detector.detect(profile, SemanticRepresentation())
        types = [a.type for a in ambigs]
        assert "no_entities" in types
