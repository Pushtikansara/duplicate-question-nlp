"""Tests for DefaultSemanticSimilarity."""

import pytest

from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRelation, SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_similarity import DefaultSemanticSimilarity


@pytest.fixture
def sim():
    return DefaultSemanticSimilarity()


class TestDefaultSemanticSimilarity:
    def test_identical_representations(self, sim):
        rep = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL"),
                SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
            ],
            entities=[{"name": "Python", "type": "language"}],
            actions=["install"],
            objects=["python"],
            relationships=[SemanticRelation(source_id="INSTALL", target_id="PYTHON", relation_type="acts_on")],
            domain="technology",
            intent_summary="install python",
        )
        result = sim.compute_all(rep, rep)
        assert result["overall"] > 0.5

    def test_completely_different(self, sim):
        rep_a = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL"),
                SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
            ],
            actions=["install"],
            domain="technology",
            intent_summary="install python",
        )
        rep_b = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="DELETE", label="delete", normalized_form="DELETE"),
                SemanticConcept(id="JAVA", label="Java", normalized_form="JAVA"),
            ],
            actions=["delete"],
            domain="science",
            intent_summary="delete java",
        )
        result = sim.compute_all(rep_a, rep_b)
        assert result["overall"] < 0.5

    def test_single_value_output(self, sim):
        rep_a = SemanticRepresentation(intent_summary="test")
        rep_b = SemanticRepresentation(intent_summary="test")
        score = sim.compute(rep_a, rep_b)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_empty_representations(self, sim):
        empty = SemanticRepresentation()
        result = sim.compute_all(empty, empty)
        assert 0.0 <= result["overall"] <= 1.0

    def test_all_intermediate_scores_returned(self, sim):
        rep_a = SemanticRepresentation(intent_summary="install python")
        rep_b = SemanticRepresentation(intent_summary="install python")
        result = sim.compute_all(rep_a, rep_b)
        assert "concept_similarity" in result
        assert "entity_similarity" in result
        assert "relation_similarity" in result
        assert "intent_similarity" in result
        assert "context_similarity" in result
        assert "overall" in result
