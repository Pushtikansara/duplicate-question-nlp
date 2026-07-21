from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._reasoning.reasoning_result import (
    Evidence,
    Hypothesis,
    Premise,
    ReasoningGraph,
)
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class PremiseBuilder(ABC):
    @abstractmethod
    def extract(self, rep: SemanticRepresentation, source_label: str) -> list[Premise]: ...


class HypothesisGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        premises_a: list[Premise],
        premises_b: list[Premise],
        assessment: SemanticAssessment | None = None,
    ) -> list[Hypothesis]: ...


class EvidenceChain(ABC):
    @abstractmethod
    def build(
        self,
        hypotheses: list[Hypothesis],
        premises_a: list[Premise],
        premises_b: list[Premise],
        assessment: SemanticAssessment | None = None,
    ) -> list[Evidence]: ...


class ReasoningGraphBuilder(ABC):
    @abstractmethod
    def build(
        self,
        premises: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> ReasoningGraph: ...


class ConflictResolver(ABC):
    @abstractmethod
    def resolve(
        self,
        premises_a: list[Premise],
        premises_b: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> list[Evidence]: ...


class UncertaintyEstimator(ABC):
    @abstractmethod
    def estimate(
        self,
        premises: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
        conflicts: list[Evidence],
    ) -> float: ...


class ConfidenceReasoner(ABC):
    @abstractmethod
    def propagate(
        self,
        premises: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> float: ...


class DecisionReasoner(ABC):
    @abstractmethod
    def decide(
        self,
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
        confidence: float,
        uncertainty: float,
        cross_encoder_score: float | None = None,
    ) -> str: ...


class ReasoningPlugin(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def process(
        self,
        premises_a: list[Premise],
        premises_b: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> list[Evidence]: ...
