from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._agents.agent_result import AgentResult, ConflictReport, ConsensusResult, Vote
from duplicate_question_app._reasoning.reasoning_result import ReasoningResult
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class CognitiveAgent(ABC):
    @abstractmethod
    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def weight(self) -> float:
        return 1.0


class VotingStrategy(ABC):
    @abstractmethod
    def compute(self, votes: list[Vote]) -> ConsensusResult: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


class ConsensusStrategy(ABC):
    @abstractmethod
    def build(
        self,
        results: list[AgentResult],
        votes: list[Vote],
        conflict_reports: list[ConflictReport],
    ) -> ConsensusResult: ...


class ConflictDetectionStrategy(ABC):
    @abstractmethod
    def detect(
        self,
        results: list[AgentResult],
        votes: list[Vote],
    ) -> list[ConflictReport]: ...


class AgentPlugin(ABC):
    @abstractmethod
    def process(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
        agent_results: list[AgentResult],
    ) -> list[AgentResult]: ...


class ConfidenceAggregationStrategy(ABC):
    @abstractmethod
    def aggregate(self, confidences: list[float], weights: list[float] | None = None) -> float: ...
