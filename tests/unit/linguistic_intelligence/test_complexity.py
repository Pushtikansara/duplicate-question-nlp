"""Tests for ComplexityAnalyzer."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.complexity_analyzer import DefaultComplexityAnalyzer


class TestDefaultComplexityAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = DefaultComplexityAnalyzer()

    def test_empty_text(self):
        ts, ss, c, r = self.analyzer.analyze("")
        assert ts.total == 0
        assert ss.total == 0
        assert c.overall == 0.0

    def test_simple_text(self):
        ts, ss, c, r = self.analyzer.analyze("Hello world.")
        assert ts.total == 2
        assert ss.total == 1
        assert c.overall >= 0.0

    def test_complex_text(self):
        text = "The implementation of the convolutional neural network requires substantial computational resources for training."
        ts, ss, c, r = self.analyzer.analyze(text)
        assert ts.total > 5
        assert ss.total >= 1
        assert c.flesch_reading_ease > 0

    def test_multiple_sentences(self):
        text = "What is Python? How do I install it? Is it better than Java?"
        ts, ss, c, r = self.analyzer.analyze(text)
        assert ss.total == 3
        assert ss.question_sentences == 3
        assert ss.avg_sentence_length > 0

    def test_readability_scores(self):
        text = "The cat sat on the mat."
        ts, ss, c, r = self.analyzer.analyze(text)
        assert r.flesch_reading_ease > 0
        assert r.flesch_kincaid_grade >= 0

    def test_type_token_ratio(self):
        text = "the the the the the foo bar baz qux"
        ts, ss, c, r = self.analyzer.analyze(text)
        assert ts.type_token_ratio < 1.0
        assert ts.unique == 5
        assert ts.total == 9
