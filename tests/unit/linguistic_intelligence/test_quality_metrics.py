"""Tests for QualityMetrics."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._linguistic_intelligence.quality_metrics import DefaultQualityMetrics


class TestDefaultQualityMetrics:
    def setup_method(self) -> None:
        self.metrics = DefaultQualityMetrics()

    def test_empty_profile(self):
        profile = LinguisticProfile()
        result = self.metrics.evaluate(profile)
        assert result.coverage == 0.0
        assert result.completeness == 0.0
        assert result.quality_score == 0.2

    def test_populated_profile(self):
        profile = LinguisticProfile(
            language="en",
            language_confidence=0.95,
            intent="installation",
            intent_confidence=0.8,
            question_type="wh-how",
            entity_count=2,
            keywords=[
                type("KW", (), {"word": "python", "score": 0.9})(),
                type("KW", (), {"word": "install", "score": 0.7})(),
                type("KW", (), {"word": "ubuntu", "score": 0.5})(),
            ],
            domain="programming",
            domain_confidence=0.8,
        )
        profile.complexity.overall = 0.5
        profile.readability.flesch_reading_ease = 60.0
        result = self.metrics.evaluate(profile, latency_ms=10.0)
        assert result.coverage > 0.0
        assert result.completeness > 0.0
        assert result.quality_score > 0.5
        assert result.latency_ms == 10.0
