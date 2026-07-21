from __future__ import annotations

from duplicate_question_app._routing.configuration import RoutingConfig
from duplicate_question_app._routing.pipeline_selector import DefaultPipelineSelector
from duplicate_question_app._routing.routing_result import ComplexityResult, UncertaintyResult
from duplicate_question_app._routing.routing_strategy import RoutingStrategy


class TestDefaultPipelineSelector:
    def setup_method(self):
        self.selector = DefaultPipelineSelector()
        self.config = RoutingConfig()

    def _make_complexity(self, label: str, score: float = 0.5) -> ComplexityResult:
        return ComplexityResult(
            complexity=label,
            score=score,
            features={},
            explanation="test",
        )

    def _make_uncertainty(self, escalate: bool) -> UncertaintyResult:
        return UncertaintyResult(
            should_escalate=escalate,
            reason="test",
            uncertainty_score=0.8 if escalate else 0.0,
            contributing_factors=["test"] if escalate else [],
        )

    def test_simple_no_escalation_balanced(self):
        complexity = self._make_complexity("simple", 0.2)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert result.pipeline == "cross_encoder_only"

    def test_medium_no_escalation_balanced(self):
        complexity = self._make_complexity("medium", 0.5)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert result.pipeline == "semantic_reasoning"

    def test_complex_no_escalation_balanced(self):
        complexity = self._make_complexity("complex", 0.8)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert result.pipeline == "full_cognitive"

    def test_uncertain_no_escalation_balanced(self):
        complexity = self._make_complexity("uncertain", 0.9)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert result.pipeline == "uncertain_full"

    def test_simple_with_escalation(self):
        complexity = self._make_complexity("simple", 0.2)
        uncertainty = self._make_uncertainty(True)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert result.pipeline == "uncertain_full"

    def test_medium_with_escalation(self):
        complexity = self._make_complexity("medium", 0.5)
        uncertainty = self._make_uncertainty(True)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert result.pipeline == "uncertain_full"

    def test_complex_with_escalation(self):
        complexity = self._make_complexity("complex", 0.8)
        uncertainty = self._make_uncertainty(True)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert result.pipeline == "uncertain_full"

    def test_simple_with_fastest_strategy(self):
        config = RoutingConfig(default_strategy=RoutingStrategy.FASTEST)
        complexity = self._make_complexity("simple", 0.2)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, config)
        assert result.pipeline == "cross_encoder_only"

    def test_medium_with_fastest_strategy(self):
        config = RoutingConfig(default_strategy=RoutingStrategy.FASTEST)
        complexity = self._make_complexity("medium", 0.5)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, config)
        assert result.pipeline == "semantic_reasoning"

    def test_simple_with_accuracy_strategy(self):
        config = RoutingConfig(default_strategy=RoutingStrategy.HIGHEST_ACCURACY)
        complexity = self._make_complexity("simple", 0.2)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, config)
        assert result.pipeline == "semantic_reasoning"

    def test_medium_with_accuracy_strategy(self):
        config = RoutingConfig(default_strategy=RoutingStrategy.HIGHEST_ACCURACY)
        complexity = self._make_complexity("medium", 0.5)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, config)
        assert result.pipeline == "full_cognitive"

    def test_complex_with_accuracy_strategy(self):
        config = RoutingConfig(default_strategy=RoutingStrategy.HIGHEST_ACCURACY)
        complexity = self._make_complexity("complex", 0.8)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, config)
        assert result.pipeline == "uncertain_full"

    def test_research_strategy(self):
        config = RoutingConfig(default_strategy=RoutingStrategy.RESEARCH)
        complexity = self._make_complexity("simple", 0.2)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, config)
        assert result.pipeline == "uncertain_full"

    def test_required_modules_for_cross_encoder(self):
        complexity = self._make_complexity("simple", 0.2)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert "cross_encoder" in result.required_modules
        assert "semantic_intelligence" in result.skipped_modules

    def test_required_modules_for_full_cognitive(self):
        complexity = self._make_complexity("complex", 0.8)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert "made" in result.required_modules
        assert len(result.skipped_modules) == 0

    def test_required_modules_for_uncertain_full(self):
        complexity = self._make_complexity("simple", 0.2)
        uncertainty = self._make_uncertainty(True)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert "debate" in result.required_modules

    def test_reason_not_empty(self):
        complexity = self._make_complexity("simple", 0.2)
        uncertainty = self._make_uncertainty(False)
        result = self.selector.select(complexity, uncertainty, self.config)
        assert len(result.reason) > 0
