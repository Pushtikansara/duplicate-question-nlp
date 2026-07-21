"""Tests for the Language Detector."""

from __future__ import annotations

from duplicate_question_app._perception.language_detector import HeuristicLanguageDetector, NoOpLanguageDetector


class TestHeuristicLanguageDetector:
    def test_detect_english_question(self):
        detector = HeuristicLanguageDetector()
        lang, confidence = detector.detect("How do I install Python?")
        assert lang == "en"
        assert confidence > 0.5

    def test_detect_english_declarative(self):
        detector = HeuristicLanguageDetector()
        lang, confidence = detector.detect("The quick brown fox jumps over the lazy dog.")
        assert lang == "en"
        assert confidence > 0.0

    def test_detect_empty_text(self):
        detector = HeuristicLanguageDetector()
        lang, confidence = detector.detect("")
        assert lang == "en"
        assert confidence == 0.0

    def test_detect_whitespace_only(self):
        detector = HeuristicLanguageDetector()
        lang, confidence = detector.detect("   ")
        assert lang == "en"
        assert confidence == 0.0

    def test_detect_short_text(self):
        detector = HeuristicLanguageDetector()
        lang, confidence = detector.detect("Hello")
        assert lang == "en"
        assert confidence >= 0.0

    def test_detect_with_numbers_and_symbols(self):
        detector = HeuristicLanguageDetector()
        lang, confidence = detector.detect("Python 3.12 vs 3.11: what changed?")
        assert lang == "en"
        assert confidence > 0.0


class TestNoOpLanguageDetector:
    def test_always_english(self):
        detector = NoOpLanguageDetector()
        lang, confidence = detector.detect("any text at all")
        assert lang == "en"
        assert confidence == 1.0

    def test_empty_text(self):
        detector = NoOpLanguageDetector()
        lang, confidence = detector.detect("")
        assert lang == "en"
        assert confidence == 1.0
