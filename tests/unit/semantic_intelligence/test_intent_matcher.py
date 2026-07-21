"""Tests for DefaultIntentMatcher."""

import pytest

from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.intent_matcher import DefaultIntentMatcher


@pytest.fixture
def matcher():
    return DefaultIntentMatcher()


class TestDefaultIntentMatcher:
    def test_exact_intent_match(self, matcher):
        rep_a = SemanticRepresentation(intent_summary="install python", actions=["install"], objects=["python"])
        rep_b = SemanticRepresentation(intent_summary="install python", actions=["install"], objects=["python"])
        result = matcher.match(rep_a, rep_b)
        assert result["score"] == 1.0
        assert result["confidence"] > 0.5

    def test_partial_intent_overlap(self, matcher):
        rep_a = SemanticRepresentation(intent_summary="how to install python", actions=["install"], objects=["python"])
        rep_b = SemanticRepresentation(
            intent_summary="installing python on linux", actions=["install"], objects=["python"]
        )
        result = matcher.match(rep_a, rep_b)
        assert result["score"] == pytest.approx(0.45, rel=1e-3)

    def test_different_intents(self, matcher):
        rep_a = SemanticRepresentation(intent_summary="install python", actions=["install"], objects=["python"])
        rep_b = SemanticRepresentation(intent_summary="delete java", actions=["delete"], objects=["java"])
        result = matcher.match(rep_a, rep_b)
        assert result["score"] < 0.5

    def test_no_intent_summary(self, matcher):
        rep_a = SemanticRepresentation()
        rep_b = SemanticRepresentation()
        result = matcher.match(rep_a, rep_b)
        assert result["score"] == 0.5

    def test_shared_actions_boost(self, matcher):
        rep_a = SemanticRepresentation(
            intent_summary="setup environment", actions=["setup", "configure"], objects=["env"]
        )
        rep_b = SemanticRepresentation(
            intent_summary="install dependencies", actions=["setup", "install"], objects=["deps"]
        )
        result = matcher.match(rep_a, rep_b)
        assert result["score"] > 0.3

    def test_shared_actions_boost_exact(self, matcher):
        rep_a = SemanticRepresentation(
            intent_summary="setup environment", actions=["setup", "configure"], objects=["env"]
        )
        rep_b = SemanticRepresentation(
            intent_summary="install dependencies", actions=["setup", "install"], objects=["deps"]
        )
        result = matcher.match(rep_a, rep_b)
        assert result["score"] == pytest.approx(0.35, rel=1e-3)
