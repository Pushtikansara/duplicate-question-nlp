"""Tests for DefaultRelationMatcher."""

import pytest

from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRelation, SemanticRepresentation
from duplicate_question_app._semantic_intelligence.relation_matcher import DefaultRelationMatcher


@pytest.fixture
def matcher():
    return DefaultRelationMatcher()


@pytest.fixture
def rep_install_python():
    return SemanticRepresentation(
        concepts=[
            SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL"),
            SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
        ],
        relationships=[
            SemanticRelation(source_id="INSTALL", target_id="PYTHON", relation_type="acts_on", confidence=0.9),
        ],
    )


@pytest.fixture
def rep_setup_python():
    return SemanticRepresentation(
        concepts=[
            SemanticConcept(id="SETUP", label="setup", normalized_form="SETUP"),
            SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
        ],
        relationships=[
            SemanticRelation(source_id="SETUP", target_id="PYTHON", relation_type="acts_on", confidence=0.85),
        ],
    )


class TestDefaultRelationMatcher:
    def test_matching_identical_relations(self, matcher, rep_install_python):
        result = matcher.match(rep_install_python, rep_install_python)
        assert result["score"] == 1.0
        assert len(result["matching_relations"]) == 1

    def test_matching_via_normalized_concepts(self, matcher, rep_install_python, rep_setup_python):
        result = matcher.match(rep_install_python, rep_setup_python)
        assert result["score"] == 0.0
        assert len(result["matching_relations"]) == 0
        assert len(result["missing_in_a"]) == 1
        assert len(result["missing_in_b"]) == 1

    def test_matching_same_normalized_concept(self, matcher):
        rep_a = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL"),
                SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
            ],
            relationships=[SemanticRelation(source_id="INSTALL", target_id="PYTHON", relation_type="acts_on")],
        )
        rep_b = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="INSTALL_ALT", label="installing", normalized_form="INSTALL"),
                SemanticConcept(id="PYTHON_ALT", label="Python3", normalized_form="PYTHON"),
            ],
            relationships=[SemanticRelation(source_id="INSTALL_ALT", target_id="PYTHON_ALT", relation_type="acts_on")],
        )
        result = matcher.match(rep_a, rep_b)
        assert result["score"] == 1.0
        assert len(result["matching_relations"]) == 1

    def test_no_relations(self, matcher):
        empty = SemanticRepresentation()
        result = matcher.match(empty, empty)
        assert result["score"] == 0.0
        assert result["total_a"] == 0

    def test_different_relation_types(self, matcher):
        rep_a = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="A", label="a", normalized_form="A"),
                SemanticConcept(id="B", label="b", normalized_form="B"),
            ],
            relationships=[SemanticRelation(source_id="A", target_id="B", relation_type="acts_on")],
        )
        rep_b = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="A", label="a", normalized_form="A"),
                SemanticConcept(id="B", label="b", normalized_form="B"),
            ],
            relationships=[SemanticRelation(source_id="A", target_id="B", relation_type="depends_on")],
        )
        result = matcher.match(rep_a, rep_b)
        assert result["score"] == 0.0
