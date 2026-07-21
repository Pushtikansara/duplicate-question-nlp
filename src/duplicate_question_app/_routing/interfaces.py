from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._perception.cognitive_representation import Metadata as PerceptionMetadata
from duplicate_question_app._reasoning.reasoning_result import ReasoningResult
from duplicate_question_app._routing.configuration import RoutingConfig
from duplicate_question_app._routing.routing_result import ComplexityResult, PipelineSelection, UncertaintyResult
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class ComplexityEstimator(ABC):
    @abstractmethod
    def estimate(
        self,
        question_a: str,
        question_b: str,
        metadata: PerceptionMetadata | None = None,
    ) -> ComplexityResult: ...


class UncertaintyRouter(ABC):
    @abstractmethod
    def should_escalate(
        self,
        cross_encoder_score: float | None,
        semantic_assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> UncertaintyResult: ...


class PipelineSelector(ABC):
    @abstractmethod
    def select(
        self,
        complexity: ComplexityResult,
        uncertainty: UncertaintyResult,
        config: RoutingConfig,
    ) -> PipelineSelection: ...


class CostEstimator(ABC):
    @abstractmethod
    def estimate_cost(
        self,
        pipeline: str,
        complexity: ComplexityResult,
    ) -> float: ...


class LatencyEstimator(ABC):
    @abstractmethod
    def estimate_latency(
        self,
        pipeline: str,
        complexity: ComplexityResult,
    ) -> float: ...
