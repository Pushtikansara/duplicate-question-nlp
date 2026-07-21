"""Tests for DefaultConceptMatcher."""

import pytest

from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRepresentation
from duplicate_question_app._semantic_intelligence.concept_matcher import DefaultConceptMatcher


@pytest.fixture
def matcher():
    return DefaultConceptMatcher()


@pytest.fixture
def rep_python_install():
    return SemanticRepresentation(
        concepts=[
            SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL"),
            SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
        ],
    )


@pytest.fixture
def rep_python_setup():
    return SemanticRepresentation(
        concepts=[
            SemanticConcept(id="SETUP", label="setup", normalized_form="SETUP"),
            SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
        ],
    )


@pytest.fixture
def rep_unrelated():
    return SemanticRepresentation(
        concepts=[
            SemanticConcept(id="DELETE", label="delete", normalized_form="DELETE"),
            SemanticConcept(id="JAVA", label="Java", normalized_form="JAVA"),
        ],
    )


class TestDefaultConceptMatcher:
    def test_matching_identical(self, matcher, rep_python_install):
        result = matcher.match(rep_python_install, rep_python_install)
        assert result["overlap_score"] == 1.0
        assert len(result["shared_concepts"]) == 2
        assert len(result["missing_in_a"]) == 0
        assert len(result["missing_in_b"]) == 0

    def test_matching_partial_overlap(self, matcher, rep_python_install, rep_python_setup):
        result = matcher.match(rep_python_install, rep_python_setup)
        assert result["overlap_score"] == pytest.approx(1 / 3, rel=1e-6)
        assert result["shared_concepts"] == ["PYTHON"]
        assert "INSTALL" in result["missing_in_b"]
        assert "SETUP" in result["missing_in_a"]

    def test_matching_no_overlap(self, matcher, rep_python_install, rep_unrelated):
        result = matcher.match(rep_python_install, rep_unrelated)
        assert result["overlap_score"] == 0.0
        assert len(result["shared_concepts"]) == 0

    def test_matching_empty_concepts(self, matcher):
        empty = SemanticRepresentation()
        result = matcher.match(empty, empty)
        assert result["overlap_score"] == 0.0
        assert result["total_a"] == 0
        assert result["total_b"] == 0

    def test_matching_through_normalization(self, matcher):
        rep_a = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL"),
            ],
        )
        rep_b = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="INSTALL_ALT", label="installing", normalized_form="INSTALL"),
            ],
        )
        result = matcher.match(rep_a, rep_b)
        assert result["overlap_score"] == 1.0
        assert "INSTALL" in result["shared_concepts"]

    def test_matching_returns_correct_totals(self, matcher, rep_python_install, rep_python_setup):
        result = matcher.match(rep_python_install, rep_python_setup)
        assert result["total_a"] == 2
        assert result["total_b"] == 2
