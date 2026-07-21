from __future__ import annotations

import logging
from typing import Any

from duplicate_question_app._perception.cognitive_representation import Metadata as PerceptionMetadata
from duplicate_question_app._reasoning.reasoning_result import ReasoningResult
from duplicate_question_app._routing.complexity_estimator import DefaultComplexityEstimator
from duplicate_question_app._routing.configuration import RoutingConfig
from duplicate_question_app._routing.cost_estimator import DefaultCostEstimator
from duplicate_question_app._routing.interfaces import (
    ComplexityEstimator,
    CostEstimator,
    LatencyEstimator,
    PipelineSelector,
    UncertaintyRouter,
)
from duplicate_question_app._routing.latency_estimator import DefaultLatencyEstimator
from duplicate_question_app._routing.pipeline_selector import DefaultPipelineSelector
from duplicate_question_app._routing.routing_result import (
    ComplexityResult,
    PipelineSelection,
    RoutingResult,
    UncertaintyResult,
)
from duplicate_question_app._routing.uncertainty_router import DefaultUncertaintyRouter
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment

log = logging.getLogger(__name__)


class AdaptiveRoutingEngine:
    def __init__(
        self,
        complexity_estimator: ComplexityEstimator | None = None,
        uncertainty_router: UncertaintyRouter | None = None,
        pipeline_selector: PipelineSelector | None = None,
        cost_estimator: CostEstimator | None = None,
        latency_estimator: LatencyEstimator | None = None,
        config: RoutingConfig | None = None,
    ):
        self._complexity_estimator = complexity_estimator or DefaultComplexityEstimator()
        self._uncertainty_router = uncertainty_router or DefaultUncertaintyRouter()
        self._pipeline_selector = pipeline_selector or DefaultPipelineSelector()
        self._cost_estimator = cost_estimator or DefaultCostEstimator()
        self._latency_estimator = latency_estimator or DefaultLatencyEstimator()
        self._config = config or RoutingConfig()

    def route(
        self,
        question_a: str,
        question_b: str,
        cross_encoder_score: float | None = None,
        perception_metadata: PerceptionMetadata | None = None,
        semantic_assessment: SemanticAssessment | None = None,
        reasoning_result: ReasoningResult | None = None,
    ) -> RoutingResult:
        metadata: dict[str, Any] = {}
        errors: list[str] = []

        complexity_result = self._estimate_complexity(question_a, question_b, perception_metadata, errors, metadata)
        uncertainty_result = self._check_uncertainty(
            cross_encoder_score, semantic_assessment, reasoning_result, errors, metadata
        )
        pipeline_selection = self._select_pipeline(complexity_result, uncertainty_result, errors, metadata)

        cost = 0.0
        if self._config.enable_cost_estimation:
            cost = self._estimate_cost(pipeline_selection.pipeline, complexity_result, errors, metadata)

        latency = 0.0
        if self._config.enable_latency_estimation:
            latency = self._estimate_latency(pipeline_selection.pipeline, complexity_result, errors, metadata)

        metadata["errors"] = errors

        confidence = 1.0
        if errors:
            confidence -= len(errors) * 0.1
            confidence = max(0.0, confidence)

        return RoutingResult(
            selected_pipeline=pipeline_selection.pipeline,
            reason=pipeline_selection.reason,
            complexity=complexity_result.complexity,
            estimated_latency_ms=latency,
            estimated_cost=cost,
            required_modules=list(pipeline_selection.required_modules),
            skipped_modules=list(pipeline_selection.skipped_modules),
            confidence=confidence,
            metadata=metadata,
            pipeline_selection=pipeline_selection,
            complexity_result=complexity_result,
            uncertainty_result=uncertainty_result,
        )

    def _estimate_complexity(
        self,
        question_a: str,
        question_b: str,
        perception_metadata: PerceptionMetadata | None,
        errors: list[str],
        metadata: dict[str, Any],
    ) -> ComplexityResult:
        try:
            result = self._complexity_estimator.estimate(question_a, question_b, perception_metadata)
            metadata["complexity_estimated"] = True
            return result
        except Exception as exc:
            log.exception("Complexity estimation failed")
            errors.append(f"Complexity estimation failed: {exc}")
            metadata["complexity_estimated"] = False
            return ComplexityResult(
                complexity="uncertain",
                score=1.0,
                features={},
                explanation=f"Estimation failed: {exc}",
            )

    def _check_uncertainty(
        self,
        cross_encoder_score: float | None,
        semantic_assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
        errors: list[str],
        metadata: dict[str, Any],
    ) -> UncertaintyResult:
        try:
            result = self._uncertainty_router.should_escalate(
                cross_encoder_score,
                semantic_assessment,
                reasoning_result,
            )
            metadata["uncertainty_checked"] = True
            return result
        except Exception as exc:
            log.exception("Uncertainty check failed")
            errors.append(f"Uncertainty check failed: {exc}")
            metadata["uncertainty_checked"] = False
            return UncertaintyResult(
                should_escalate=True,
                reason=f"Uncertainty check failed: {exc}",
                uncertainty_score=1.0,
                contributing_factors=["Router failure"],
            )

    def _select_pipeline(
        self,
        complexity: ComplexityResult,
        uncertainty: UncertaintyResult,
        errors: list[str],
        metadata: dict[str, Any],
    ) -> PipelineSelection:
        try:
            result = self._pipeline_selector.select(complexity, uncertainty, self._config)
            metadata["pipeline_selected"] = True
            return result
        except Exception as exc:
            log.exception("Pipeline selection failed")
            errors.append(f"Pipeline selection failed: {exc}")
            metadata["pipeline_selected"] = False
            return PipelineSelection(
                pipeline="uncertain_full",
                required_modules=["cross_encoder", "semantic_intelligence", "reasoning", "made", "debate"],
                skipped_modules=[],
                reason=f"Pipeline selection failed: {exc}",
            )

    def _estimate_cost(
        self,
        pipeline: str,
        complexity: ComplexityResult,
        errors: list[str],
        metadata: dict[str, Any],
    ) -> float:
        try:
            cost = self._cost_estimator.estimate_cost(pipeline, complexity)
            metadata["cost_estimated"] = True
            return cost
        except Exception as exc:
            log.exception("Cost estimation failed")
            errors.append(f"Cost estimation failed: {exc}")
            metadata["cost_estimated"] = False
            return 1.0

    def _estimate_latency(
        self,
        pipeline: str,
        complexity: ComplexityResult,
        errors: list[str],
        metadata: dict[str, Any],
    ) -> float:
        try:
            latency = self._latency_estimator.estimate_latency(pipeline, complexity)
            metadata["latency_estimated"] = True
            return latency
        except Exception as exc:
            log.exception("Latency estimation failed")
            errors.append(f"Latency estimation failed: {exc}")
            metadata["latency_estimated"] = False
            return 5000.0
