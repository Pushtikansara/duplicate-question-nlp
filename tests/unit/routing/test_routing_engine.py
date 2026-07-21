from __future__ import annotations

from duplicate_question_app._perception.cognitive_representation import Metadata as PerceptionMetadata
from duplicate_question_app._reasoning.reasoning_result import ReasoningResult
from duplicate_question_app._routing.configuration import RoutingConfig
from duplicate_question_app._routing.routing_engine import AdaptiveRoutingEngine
from duplicate_question_app._routing.routing_result import ComplexityResult, PipelineSelection
from duplicate_question_app._routing.routing_strategy import RoutingStrategy
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class TestAdaptiveRoutingEngine:
    def test_full_routing_simple(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        qa, qb = "What is Python?", "What is Python language?"
        result = engine.route(qa, qb)
        assert result.selected_pipeline == "cross_encoder_only"
        assert result.complexity == "simple"
        assert result.confidence > 0

    def test_full_routing_with_cross_encoder_score(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("Q1", "Q2", cross_encoder_score=0.85)
        assert result.selected_pipeline is not None

    def test_full_routing_with_perception_metadata(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        metadata = PerceptionMetadata(
            length=50,
            char_count=50,
            word_count=8,
            sentence_count=1,
            question_type="wh-what",
        )
        result = engine.route("What is Python?", "What is AI?", perception_metadata=metadata)
        assert result.selected_pipeline is not None

    def test_full_routing_with_semantic_assessment(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        assessment = SemanticAssessment(semantic_similarity=0.9, confidence=0.9)
        result = engine.route("Q1", "Q2", semantic_assessment=assessment)
        assert result.selected_pipeline is not None

    def test_full_routing_with_reasoning_result(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        reasoning = ReasoningResult(decision="duplicate", confidence=0.9, uncertainty=0.1)
        result = engine.route("Q1", "Q2", reasoning_result=reasoning)
        assert result.selected_pipeline is not None

    def test_routing_result_fields_populated(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("What is Python?", "What is AI?")
        assert result.selected_pipeline is not None
        assert result.reason != ""
        assert result.complexity != ""
        assert result.estimated_latency_ms >= 0
        assert 0.0 <= result.estimated_cost <= 1.0
        assert isinstance(result.required_modules, list)
        assert isinstance(result.skipped_modules, list)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.metadata, dict)

    def test_routing_result_nested_objects(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("What is Python?", "What is AI?")
        assert result.pipeline_selection is not None
        assert result.complexity_result is not None
        assert result.uncertainty_result is not None

    def test_routing_result_to_dict(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("What is Python?", "What is AI?")
        d = result.to_dict()
        assert d["selected_pipeline"] is not None
        assert d["pipeline_selection"] is not None
        assert d["complexity_result"] is not None
        assert d["uncertainty_result"] is not None

    def test_error_in_complexity_estimator(
        self,
        mock_complexity_estimator,
        mock_uncertainty_router,
        mock_pipeline_selector,
        mock_cost_estimator,
        mock_latency_estimator,
    ):
        mock_complexity_estimator.estimate.side_effect = ValueError("Estimator failed")
        engine = AdaptiveRoutingEngine(
            complexity_estimator=mock_complexity_estimator,
            uncertainty_router=mock_uncertainty_router,
            pipeline_selector=mock_pipeline_selector,
            cost_estimator=mock_cost_estimator,
            latency_estimator=mock_latency_estimator,
        )
        result = engine.route("Q1", "Q2")
        assert result.complexity == "uncertain"
        assert len(result.metadata.get("errors", [])) > 0

    def test_error_in_uncertainty_router(
        self,
        mock_complexity_estimator,
        mock_uncertainty_router,
        mock_pipeline_selector,
        mock_cost_estimator,
        mock_latency_estimator,
    ):
        mock_uncertainty_router.should_escalate.side_effect = ValueError("Router failed")
        engine = AdaptiveRoutingEngine(
            complexity_estimator=mock_complexity_estimator,
            uncertainty_router=mock_uncertainty_router,
            pipeline_selector=mock_pipeline_selector,
            cost_estimator=mock_cost_estimator,
            latency_estimator=mock_latency_estimator,
        )
        result = engine.route("Q1", "Q2")
        assert result.uncertainty_result is not None
        assert result.uncertainty_result.should_escalate

    def test_error_in_pipeline_selector(
        self,
        mock_complexity_estimator,
        mock_uncertainty_router,
        mock_pipeline_selector,
        mock_cost_estimator,
        mock_latency_estimator,
    ):
        mock_pipeline_selector.select.side_effect = ValueError("Selector failed")
        engine = AdaptiveRoutingEngine(
            complexity_estimator=mock_complexity_estimator,
            uncertainty_router=mock_uncertainty_router,
            pipeline_selector=mock_pipeline_selector,
            cost_estimator=mock_cost_estimator,
            latency_estimator=mock_latency_estimator,
        )
        result = engine.route("Q1", "Q2")
        assert result.selected_pipeline == "uncertain_full"

    def test_error_in_cost_estimator(
        self,
        mock_complexity_estimator,
        mock_uncertainty_router,
        mock_pipeline_selector,
        mock_cost_estimator,
        mock_latency_estimator,
    ):
        mock_cost_estimator.estimate_cost.side_effect = ValueError("Cost failed")
        engine = AdaptiveRoutingEngine(
            complexity_estimator=mock_complexity_estimator,
            uncertainty_router=mock_uncertainty_router,
            pipeline_selector=mock_pipeline_selector,
            cost_estimator=mock_cost_estimator,
            latency_estimator=mock_latency_estimator,
        )
        result = engine.route("Q1", "Q2")
        assert result.estimated_cost == 1.0

    def test_error_in_latency_estimator(
        self,
        mock_complexity_estimator,
        mock_uncertainty_router,
        mock_pipeline_selector,
        mock_cost_estimator,
        mock_latency_estimator,
    ):
        mock_latency_estimator.estimate_latency.side_effect = ValueError("Latency failed")
        engine = AdaptiveRoutingEngine(
            complexity_estimator=mock_complexity_estimator,
            uncertainty_router=mock_uncertainty_router,
            pipeline_selector=mock_pipeline_selector,
            cost_estimator=mock_cost_estimator,
            latency_estimator=mock_latency_estimator,
        )
        result = engine.route("Q1", "Q2")
        assert result.estimated_latency_ms == 5000.0

    def test_cost_estimation_disabled(self, mock_estimators):
        config = RoutingConfig(enable_cost_estimation=False)
        engine = AdaptiveRoutingEngine(**mock_estimators, config=config)
        result = engine.route("Q1", "Q2")
        assert result.estimated_cost == 0.0

    def test_latency_estimation_disabled(self, mock_estimators):
        config = RoutingConfig(enable_latency_estimation=False)
        engine = AdaptiveRoutingEngine(**mock_estimators, config=config)
        result = engine.route("Q1", "Q2")
        assert result.estimated_latency_ms == 0.0

    def test_different_complexity_levels(self, mock_estimators):
        mock_estimators["complexity_estimator"].estimate.return_value = ComplexityResult(
            complexity="complex",
            score=0.8,
            features={},
            explanation="complex test",
        )
        mock_estimators["pipeline_selector"].select.return_value = PipelineSelection(
            pipeline="full_cognitive",
            required_modules=["cross_encoder", "semantic_intelligence", "reasoning", "made"],
            skipped_modules=[],
            reason="Complex question",
        )
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("Complex Q1", "Complex Q2")
        assert result.complexity == "complex"
        assert result.selected_pipeline == "full_cognitive"

    def test_default_estimators(self):
        engine = AdaptiveRoutingEngine()
        result = engine.route("What is Python?", "What is AI?")
        assert result.selected_pipeline is not None
        assert result.complexity == "simple"

    def test_empty_questions_default(self):
        engine = AdaptiveRoutingEngine()
        result = engine.route("", "")
        assert result.selected_pipeline is not None

    def test_confidence_reduced_on_errors(self, mock_estimators):
        mock_estimators["complexity_estimator"].estimate.side_effect = RuntimeError("fail")
        mock_estimators["uncertainty_router"].should_escalate.side_effect = RuntimeError("fail")
        mock_estimators["pipeline_selector"].select.side_effect = RuntimeError("fail")
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("Q1", "Q2")
        assert result.confidence < 1.0

    def test_required_modules_for_pipeline(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("Q1", "Q2")
        assert "cross_encoder" in result.required_modules

    def test_skipped_modules_for_simple(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("Q1", "Q2")
        assert "semantic_intelligence" in result.skipped_modules

    def test_with_fastest_strategy(self, mock_estimators):
        config = RoutingConfig(default_strategy=RoutingStrategy.FASTEST)
        mock_estimators["pipeline_selector"].select.return_value = PipelineSelection(
            pipeline="cross_encoder_only",
            required_modules=["cross_encoder"],
            skipped_modules=["semantic_intelligence", "reasoning", "made"],
            reason="Fastest strategy",
        )
        engine = AdaptiveRoutingEngine(**mock_estimators, config=config)
        result = engine.route("Q1", "Q2")
        assert result.selected_pipeline == "cross_encoder_only"

    def test_to_dict_full(self, mock_estimators):
        engine = AdaptiveRoutingEngine(**mock_estimators)
        result = engine.route("Q1", "Q2")
        d = result.to_dict()
        assert set(d.keys()) == {
            "selected_pipeline",
            "reason",
            "complexity",
            "estimated_latency_ms",
            "estimated_cost",
            "required_modules",
            "skipped_modules",
            "confidence",
            "metadata",
            "pipeline_selection",
            "complexity_result",
            "uncertainty_result",
        }
