"""Abstract interfaces for all Semantic Knowledge Representation components.

Every semantic component exposes an ABC for testability and plugin injection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic.semantic_graph import SemanticNode, SemanticRelation


class ConceptExtractor(ABC):
    @abstractmethod
    def extract(self, profile: LinguisticProfile) -> list[SemanticNode]: ...


class RelationExtractor(ABC):
    @abstractmethod
    def extract(self, profile: LinguisticProfile, concepts: list[SemanticNode]) -> list[SemanticRelation]: ...


class SemanticRoleAnalyzer(ABC):
    @abstractmethod
    def analyze(self, profile: LinguisticProfile, concepts: list[SemanticNode]) -> dict[str, list[SemanticNode]]: ...


class ContextBuilder(ABC):
    @abstractmethod
    def build(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> dict: ...


class AmbiguityDetector(ABC):
    @abstractmethod
    def detect(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> list[dict]: ...


class SemanticConfidence(ABC):
    @abstractmethod
    def compute(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> dict: ...


class RepresentationBuilder(ABC):
    @abstractmethod
    def build(self, profile: LinguisticProfile) -> tuple[SemanticRepresentation, bool, float, str | None]: ...
