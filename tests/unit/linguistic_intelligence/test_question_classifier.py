"""Tests for QuestionClassifier."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.question_classifier import DefaultQuestionClassifier


class TestDefaultQuestionClassifier:
    def setup_method(self) -> None:
        self.classifier = DefaultQuestionClassifier()

    def test_wh_what_question(self):
        qt, qc, conf = self.classifier.classify("What is machine learning?")
        assert qt == "wh-what"
        assert qc is not None
        assert conf > 0.5

    def test_wh_how_question(self):
        qt, qc, conf = self.classifier.classify("How to install Python?")
        assert qt == "wh-how"
        assert qc is not None
        assert conf > 0.5

    def test_wh_why_question(self):
        qt, qc, conf = self.classifier.classify("Why does this error occur?")
        assert qt == "wh-why"

    def test_yes_no_question(self):
        qt, qc, conf = self.classifier.classify("Is Python better than Java?")
        assert qt == "yes-no"

    def test_declarative_statement(self):
        qt, qc, conf = self.classifier.classify("Python is a programming language.")
        assert qt == "declarative"

    def test_exclamatory(self):
        qt, qc, conf = self.classifier.classify("This is amazing!")
        assert qt == "exclamatory"

    def test_imperative(self):
        qt, qc, conf = self.classifier.classify("Show me how to debug this code")
        assert qt == "imperative"

    def test_empty_text(self):
        qt, qc, conf = self.classifier.classify("")
        assert qt is None
        assert qc is None
        assert conf == 0.0

    def test_whitespace_only(self):
        qt, qc, conf = self.classifier.classify("   ")
        assert qt is None
