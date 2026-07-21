"""Tests for ConfidenceEstimator."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.confidence_estimator import DefaultConfidenceEstimator
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile


class TestDefaultConfidenceEstimator:
    def setup_method(self) -> None:
        self.estimator = DefaultConfidenceEstimator()

    def test_empty_profile(self):
        profile = LinguisticProfile()
        ac = self.estimator.estimate(profile)
        assert ac.overall == 0.0
        assert ac.language == 0.0

    def test_populated_profile(self):
        profile = LinguisticProfile(
            language="en",
            language_confidence=0.95,
            intent="installation",
            intent_confidence=0.85,
            entity_count=3,
            question_type="wh-how",
            domain="programming",
            domain_confidence=0.8,
        )
        ac = self.estimator.estimate(profile)
        assert ac.overall > 0.0
        assert ac.language == 0.95
        assert ac.intent == 0.85
        assert ac.per_analyzer["language"] == 0.95

    def test_partial_profile(self):
        profile = LinguisticProfile(language="en", language_confidence=0.9)
        ac = self.estimator.estimate(profile)
        assert ac.overall > 0.0
        assert ac.domain == 0.0
