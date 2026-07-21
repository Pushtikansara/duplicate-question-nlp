"""Abstract interfaces for all Semantic Intelligence Engine components.

Every component exposes an ABC for testability and plugin injection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class ConceptMatcher(ABC):
    @abstractmethod
    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict: ...


class EntityMatcher(ABC):
    @abstractmethod
    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict: ...


class RelationMatcher(ABC):
    @abstractmethod
    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict: ...


class IntentMatcher(ABC):
    @abstractmethod
    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict: ...


class ContextMatcher(ABC):
    @abstractmethod
    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict: ...


class ConflictDetector(ABC):
    @abstractmethod
    def detect(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> list[dict]: ...


class EvidenceBuilder(ABC):
    @abstractmethod
    def build(self, assessment: SemanticAssessment) -> list[dict]: ...


class ConfidenceFusion(ABC):
    @abstractmethod
    def compute(self, scores: dict[str, float]) -> dict: ...


class SemanticSimilarity(ABC):
    @abstractmethod
    def compute(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> float: ...


class DecisionSupport(ABC):
    @abstractmethod
    def evaluate(self, assessment: SemanticAssessment) -> dict: ...


class SemanticIntelligenceEngine(ABC):
    @abstractmethod
    def assess(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> SemanticAssessment: ...
