"""Tests for DefaultConfidenceFusion."""

import pytest

from duplicate_question_app._semantic_intelligence.confidence_fusion import DEFAULT_WEIGHTS, DefaultConfidenceFusion


@pytest.fixture
def fusion():
    return DefaultConfidenceFusion()


class TestDefaultConfidenceFusion:
    def test_all_perfect_scores(self, fusion):
        scores = {
            "concept_similarity": 1.0,
            "relation_similarity": 1.0,
            "intent_similarity": 1.0,
            "entity_similarity": 1.0,
            "context_similarity": 1.0,
        }
        result = fusion.compute(scores)
        assert result["overall"] == pytest.approx(1.0, rel=1e-6)

    def test_all_zero_scores(self, fusion):
        scores = {
            "concept_similarity": 0.0,
            "relation_similarity": 0.0,
            "intent_similarity": 0.0,
            "entity_similarity": 0.0,
            "context_similarity": 0.0,
        }
        result = fusion.compute(scores)
        assert result["overall"] == 0.0

    def test_weights_sum_to_one(self, fusion):
        assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-6

    def test_missing_scores_default_to_zero(self, fusion):
        scores = {"concept_similarity": 0.5}
        result = fusion.compute(scores)
        assert result["overall"] < 0.5

    def test_custom_weights(self):
        custom = DefaultConfidenceFusion(weights={"concept_similarity": 1.0})
        result = custom.compute({"concept_similarity": 0.5})
        assert result["overall"] == 0.5

    def test_weight_normalization(self):
        fusion = DefaultConfidenceFusion(weights={"a": 1.0, "b": 1.0})
        total = sum(fusion._weights.values())
        assert abs(total - 1.0) < 1e-6

    def test_intermediate_scores_stored(self, fusion):
        scores = {
            "concept_similarity": 0.8,
            "relation_similarity": 0.6,
            "intent_similarity": 0.9,
            "entity_similarity": 0.7,
            "context_similarity": 0.5,
        }
        result = fusion.compute(scores)
        assert "raw_scores" in result
        assert "weighted_scores" in result
        assert "weights" in result
        assert result["raw_scores"] == scores
