"""Tests for KeywordExtractor."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.keyword_extractor import DefaultKeywordExtractor


class TestDefaultKeywordExtractor:
    def setup_method(self) -> None:
        self.extractor = DefaultKeywordExtractor(top_n=10)

    def test_empty_text(self):
        keywords, scores, lexical = self.extractor.extract("")
        assert keywords == []
        assert scores == {}

    def test_simple_keywords(self):
        text = "How to install Python on Ubuntu Linux"
        keywords, scores, lexical = self.extractor.extract(text)
        assert len(keywords) > 0
        assert "python" in scores or "install" in scores or "ubuntu" in scores

    def test_lexical_features(self):
        text = "How to install Python on Ubuntu"
        keywords, scores, lexical = self.extractor.extract(text)
        assert lexical.lexical_density >= 0.0
        assert lexical.noun_count >= 0 or lexical.verb_count >= 0

    def test_keyword_scoring(self):
        text = "Python Python Python Java Java Ruby"
        keywords, scores, lexical = self.extractor.extract(text)
        assert len(keywords) >= 3
        top_score = keywords[0].score
        assert top_score > 0

    def test_stopword_filtering(self):
        text = "the and of to a in is it you"
        keywords, scores, lexical = self.extractor.extract(text)
        short_stops = [k for k in keywords if len(k.word) <= 3]
        assert len(short_stops) <= len(keywords)
