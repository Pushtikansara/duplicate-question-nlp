"""Tests for DomainDetector."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.domain_detector import DefaultDomainDetector


class TestDefaultDomainDetector:
    def setup_method(self) -> None:
        self.detector = DefaultDomainDetector()

    def test_programming_domain(self):
        domain, conf = self.detector.detect("How to install Python on Ubuntu?")
        assert domain == "programming"
        assert conf > 0.5

    def test_data_science_domain(self):
        domain, conf = self.detector.detect("What is the best way to train a neural network?")
        assert domain == "data-science"
        assert conf > 0.5

    def test_general_domain(self):
        domain, conf = self.detector.detect("What is the weather like today?")
        assert domain == "general"

    def test_empty_text(self):
        domain, conf = self.detector.detect("")
        assert domain is None
        assert conf == 0.0
