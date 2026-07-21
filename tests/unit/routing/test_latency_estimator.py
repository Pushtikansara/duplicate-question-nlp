from __future__ import annotations

from duplicate_question_app._routing.latency_estimator import DefaultLatencyEstimator
from duplicate_question_app._routing.routing_result import ComplexityResult


class TestDefaultLatencyEstimator:
    def setup_method(self):
        self.estimator = DefaultLatencyEstimator()

    def _make_complexity(self, complexity: str, score: float, avg_words: float = 10) -> ComplexityResult:
        return ComplexityResult(
            complexity=complexity,
            score=score,
            features={"avg_word_count": avg_words},
            explanation="test",
        )

    def test_cross_encoder_only_latency(self):
        complexity = self._make_complexity("simple", 0.2, avg_words=5)
        latency = self.estimator.estimate_latency("cross_encoder_only", complexity)
        assert 50.0 <= latency <= 200.0

    def test_semantic_reasoning_latency(self):
        complexity = self._make_complexity("medium", 0.5)
        latency = self.estimator.estimate_latency("semantic_reasoning", complexity)
        assert 200.0 <= latency <= 800.0

    def test_full_cognitive_latency(self):
        complexity = self._make_complexity("complex", 0.8)
        latency = self.estimator.estimate_latency("full_cognitive", complexity)
        assert 500.0 <= latency <= 2000.0

    def test_uncertain_full_latency(self):
        complexity = self._make_complexity("uncertain", 0.9)
        latency = self.estimator.estimate_latency("uncertain_full", complexity)
        assert 1000.0 <= latency <= 5000.0

    def test_unknown_pipeline_returns_max(self):
        complexity = self._make_complexity("simple", 0.2)
        latency = self.estimator.estimate_latency("unknown_pipeline", complexity)
        assert latency == 5000.0

    def test_complexity_increases_latency(self):
        simple = self._make_complexity("simple", 0.2, avg_words=5)
        complex_r = self._make_complexity("complex", 0.9, avg_words=50)
        lat_simple = self.estimator.estimate_latency("full_cognitive", simple)
        lat_complex = self.estimator.estimate_latency("full_cognitive", complex_r)
        assert lat_simple <= lat_complex

    def test_latency_within_bounds(self):
        for pipeline in ("cross_encoder_only", "semantic_reasoning", "full_cognitive", "uncertain_full"):
            for score in (0.0, 0.5, 1.0):
                complexity = self._make_complexity("test", score)
                latency = self.estimator.estimate_latency(pipeline, complexity)
                bounds = {
                    "cross_encoder_only": (50.0, 200.0),
                    "semantic_reasoning": (200.0, 800.0),
                    "full_cognitive": (500.0, 2000.0),
                    "uncertain_full": (1000.0, 5000.0),
                }
                lo, hi = bounds[pipeline]
                assert lo <= latency <= hi, f"{pipeline}: {latency} not in [{lo}, {hi}]"

    def test_empty_complexity_features(self):
        complexity = ComplexityResult(
            complexity="simple",
            score=0.2,
            features={},
            explanation="test",
        )
        latency = self.estimator.estimate_latency("cross_encoder_only", complexity)
        assert 50.0 <= latency <= 200.0

    def test_zero_word_count(self):
        complexity = self._make_complexity("simple", 0.2, avg_words=0)
        latency = self.estimator.estimate_latency("cross_encoder_only", complexity)
        assert 50.0 <= latency <= 200.0

    def test_large_word_count(self):
        complexity = self._make_complexity("complex", 0.9, avg_words=200)
        latency = self.estimator.estimate_latency("uncertain_full", complexity)
        assert 1000.0 <= latency <= 5000.0
