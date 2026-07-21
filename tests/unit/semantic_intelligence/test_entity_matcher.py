"""Tests for DefaultEntityMatcher."""

import pytest

from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.entity_matcher import DefaultEntityMatcher


@pytest.fixture
def matcher():
    return DefaultEntityMatcher()


@pytest.fixture
def rep_with_entities():
    return SemanticRepresentation(
        entities=[
            {"name": "Python", "type": "language", "confidence": 0.95},
            {"name": "Linux", "type": "os", "confidence": 0.90},
        ],
    )


class TestDefaultEntityMatcher:
    def test_matching_identical(self, matcher, rep_with_entities):
        result = matcher.match(rep_with_entities, rep_with_entities)
        assert result["overlap_score"] == 1.0
        assert len(result["shared_entities"]) == 2

    def test_matching_partial(self, matcher):
        rep_a = SemanticRepresentation(
            entities=[
                {"name": "Python", "type": "language"},
                {"name": "Linux", "type": "os"},
            ],
        )
        rep_b = SemanticRepresentation(
            entities=[
                {"name": "Python", "type": "language"},
                {"name": "Windows", "type": "os"},
            ],
        )
        result = matcher.match(rep_a, rep_b)
        assert result["overlap_score"] == pytest.approx(1 / 3, rel=1e-6)
        assert result["shared_entities"] == ["python"]
        assert "linux" in result["missing_in_b"]
        assert "windows" in result["missing_in_a"]

    def test_matching_no_overlap(self, matcher):
        rep_a = SemanticRepresentation(
            entities=[{"name": "Python", "type": "language"}],
        )
        rep_b = SemanticRepresentation(
            entities=[{"name": "Java", "type": "language"}],
        )
        result = matcher.match(rep_a, rep_b)
        assert result["overlap_score"] == 0.0

    def test_matching_empty(self, matcher):
        empty = SemanticRepresentation()
        result = matcher.match(empty, empty)
        assert result["overlap_score"] == 0.0

    def test_entity_type_conflict_detected(self, matcher):
        rep_a = SemanticRepresentation(
            entities=[{"name": "Python", "type": "language"}],
        )
        rep_b = SemanticRepresentation(
            entities=[{"name": "Python", "type": "tool"}],
        )
        result = matcher.match(rep_a, rep_b)
        assert len(result["conflicts"]) == 1
        assert "python" in result["conflicts"][0]

    def test_case_insensitive_matching(self, matcher):
        rep_a = SemanticRepresentation(
            entities=[{"name": "Python", "type": "language"}],
        )
        rep_b = SemanticRepresentation(
            entities=[{"name": "python", "type": "language"}],
        )
        result = matcher.match(rep_a, rep_b)
        assert result["overlap_score"] == 1.0
