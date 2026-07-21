from __future__ import annotations

from duplicate_question_app._routing.cost_estimator import DefaultCostEstimator
from duplicate_question_app._routing.routing_result import ComplexityResult


class TestDefaultCostEstimator:
    def setup_method(self):
        self.estimator = DefaultCostEstimator()

    def _make_complexity(self, complexity: str, score: float, avg_words: float = 10) -> ComplexityResult:
        return ComplexityResult(
            complexity=complexity,
            score=score,
            features={"avg_word_count": avg_words},
            explanation="test",
        )

    def test_cross_encoder_only_cost(self):
        complexity = self._make_complexity("simple", 0.2)
        cost = self.estimator.estimate_cost("cross_encoder_only", complexity)
        assert 0.05 <= cost <= 0.2

    def test_semantic_reasoning_cost(self):
        complexity = self._make_complexity("medium", 0.5)
        cost = self.estimator.estimate_cost("semantic_reasoning", complexity)
        assert 0.2 <= cost <= 0.6

    def test_full_cognitive_cost(self):
        complexity = self._make_complexity("complex", 0.8)
        cost = self.estimator.estimate_cost("full_cognitive", complexity)
        assert 0.3 <= cost <= 1.0

    def test_uncertain_full_cost(self):
        complexity = self._make_complexity("uncertain", 0.9)
        cost = self.estimator.estimate_cost("uncertain_full", complexity)
        assert 0.5 <= cost <= 1.0

    def test_unknown_pipeline_returns_max(self):
        complexity = self._make_complexity("simple", 0.2)
        cost = self.estimator.estimate_cost("unknown_pipeline", complexity)
        assert cost == 1.0

    def test_complexity_increases_cost(self):
        simple = self._make_complexity("simple", 0.2, avg_words=5)
        complex_r = self._make_complexity("complex", 0.9, avg_words=50)
        cost_simple = self.estimator.estimate_cost("full_cognitive", simple)
        cost_complex = self.estimator.estimate_cost("full_cognitive", complex_r)
        assert cost_simple <= cost_complex

    def test_cost_bounds(self):
        for pipeline in ("cross_encoder_only", "semantic_reasoning", "full_cognitive", "uncertain_full"):
            for score in (0.0, 0.25, 0.5, 0.75, 1.0):
                complexity = self._make_complexity("test", score)
                cost = self.estimator.estimate_cost(pipeline, complexity)
                assert 0.0 <= cost <= 1.0, f"Pipeline {pipeline}, score {score}: cost={cost}"

    def test_empty_complexity_features(self):
        complexity = ComplexityResult(
            complexity="simple",
            score=0.2,
            features={},
            explanation="test",
        )
        cost = self.estimator.estimate_cost("cross_encoder_only", complexity)
        assert 0.0 <= cost <= 1.0

    def test_zero_word_count(self):
        complexity = self._make_complexity("simple", 0.2, avg_words=0)
        cost = self.estimator.estimate_cost("cross_encoder_only", complexity)
        assert 0.0 <= cost <= 1.0

    def test_large_word_count(self):
        complexity = self._make_complexity("complex", 0.9, avg_words=500)
        cost = self.estimator.estimate_cost("uncertain_full", complexity)
        assert cost <= 1.0
