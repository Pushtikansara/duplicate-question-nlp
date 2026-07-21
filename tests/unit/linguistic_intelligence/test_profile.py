"""Tests for LinguisticProfile data model."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.profile import (
    ComplexityScore,
    Keyword,
    LexicalFeatures,
    LinguisticProfile,
    QualityMetricsData,
    ReadabilityScore,
    SentenceStatistics,
    TokenStatistics,
)


class TestLinguisticProfile:
    def test_create_empty_profile(self):
        profile = LinguisticProfile()
        assert profile.language == ""
        assert profile.entity_count == 0
        assert len(profile.keywords) == 0
        assert profile.complexity.overall == 0.0

    def test_to_dict_empty(self):
        profile = LinguisticProfile()
        d = profile.to_dict()
        assert d["language"] == ""
        assert d["entity_count"] == 0
        assert d["domain"] is None

    def test_create_populated_profile(self):
        profile = LinguisticProfile(
            language="en",
            language_confidence=0.95,
            intent="installation",
            intent_confidence=0.85,
            question_type="wh-how",
            question_class="installation",
            entity_count=3,
            entities=[{"type": "programming_language", "value": "python", "confidence": 1.0}],
            keywords=[Keyword(word="python", score=0.9, frequency=2)],
            negation=True,
            negation_count=1,
            domain="programming",
            domain_confidence=0.8,
            token_statistics=TokenStatistics(total=10, unique=7, type_token_ratio=0.7),
            sentence_statistics=SentenceStatistics(total=2, avg_sentence_length=5.0),
            lexical_features=LexicalFeatures(lexical_density=0.6, lexical_diversity=0.7),
            complexity=ComplexityScore(overall=0.5, flesch_reading_ease=60.0),
            readability=ReadabilityScore(flesch_reading_ease=60.0, flesch_kincaid_grade=8.0),
            quality_metrics=QualityMetricsData(quality_score=0.85, coverage=0.9, completeness=0.8),
        )
        assert profile.language == "en"
        assert profile.intent == "installation"
        assert profile.entity_count == 3
        d = profile.to_dict()
        assert d["language"] == "en"
        assert d["intent"] == "installation"
        assert d["domain"] == "programming"
        assert d["entity_count"] == 3
        assert len(d["keywords"]) == 1
        assert d["complexity"]["flesch_reading_ease"] == 60.0
        assert d["quality_metrics"]["quality_score"] == 0.85
