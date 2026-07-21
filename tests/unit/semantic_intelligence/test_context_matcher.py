"""Tests for DefaultContextMatcher."""

import pytest

from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.context_matcher import DefaultContextMatcher


@pytest.fixture
def matcher():
    return DefaultContextMatcher()


class TestDefaultContextMatcher:
    def test_domain_match(self, matcher):
        rep_a = SemanticRepresentation(domain="technology")
        rep_b = SemanticRepresentation(domain="technology")
        result = matcher.match(rep_a, rep_b)
        assert result["domain_match"] is True
        assert result["score"] > 0

    def test_domain_mismatch(self, matcher):
        rep_a = SemanticRepresentation(domain="technology")
        rep_b = SemanticRepresentation(domain="science")
        result = matcher.match(rep_a, rep_b)
        assert result["domain_match"] is False

    def test_context_key_overlap(self, matcher):
        rep_a = SemanticRepresentation(context={"platform": "linux", "version": "3.9"})
        rep_b = SemanticRepresentation(context={"platform": "linux", "arch": "x86"})
        result = matcher.match(rep_a, rep_b)
        assert "platform" in result["shared_context_keys"]
        assert result["score"] > 0

    def test_constraints_match(self, matcher):
        rep_a = SemanticRepresentation(constraints=["python>=3.8", "linux"])
        rep_b = SemanticRepresentation(constraints=["python>=3.8", "linux"])
        result = matcher.match(rep_a, rep_b)
        assert result["constraints_match"] == 1.0

    def test_no_context(self, matcher):
        empty = SemanticRepresentation()
        result = matcher.match(empty, empty)
        assert result["score"] == 0.2

    def test_empty_domain(self, matcher):
        rep_a = SemanticRepresentation(domain="tech")
        empty = SemanticRepresentation()
        result = matcher.match(rep_a, empty)
        assert result["domain_match"] is False
