"""SemanticAssessment — the unified output of the Semantic Intelligence Engine.

Every ARES reasoning component downstream consumes ONLY SemanticAssessment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Recommendation(Enum):
    DUPLICATE = "DUPLICATE"
    NOT_DUPLICATE = "NOT_DUPLICATE"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class ConceptOverlap:
    overlap_score: float = 0.0
    shared_concepts: list[str] = field(default_factory=list)
    missing_in_a: list[str] = field(default_factory=list)
    missing_in_b: list[str] = field(default_factory=list)
    total_a: int = 0
    total_b: int = 0
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityOverlap:
    overlap_score: float = 0.0
    shared_entities: list[str] = field(default_factory=list)
    missing_in_a: list[str] = field(default_factory=list)
    missing_in_b: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    total_a: int = 0
    total_b: int = 0
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentSimilarity:
    score: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationSimilarity:
    score: float = 0.0
    matching_relations: list[dict] = field(default_factory=list)
    missing_in_a: list[dict] = field(default_factory=list)
    missing_in_b: list[dict] = field(default_factory=list)
    total_a: int = 0
    total_b: int = 0
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextSimilarity:
    score: float = 0.0
    domain_match: bool = False
    domain_a: str | None = None
    domain_b: str | None = None
    shared_context_keys: list[str] = field(default_factory=list)
    constraints_match: bool = False
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class Conflict:
    conflict_type: str
    description: str
    severity: float = 1.0
    source: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceItem:
    category: str
    status: str
    message: str
    confidence: float = 1.0
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingMetadata:
    processing_time_ms: float = 0.0
    stages: dict[str, float] = field(default_factory=dict)
    components_used: list[str] = field(default_factory=list)


@dataclass
class SemanticAssessment:
    semantic_similarity: float = 0.0
    concept_overlap: ConceptOverlap = field(default_factory=ConceptOverlap)
    entity_overlap: EntityOverlap = field(default_factory=EntityOverlap)
    intent_similarity: IntentSimilarity = field(default_factory=IntentSimilarity)
    relation_similarity: RelationSimilarity = field(default_factory=RelationSimilarity)
    context_similarity: ContextSimilarity = field(default_factory=ContextSimilarity)
    conflicts: list[Conflict] = field(default_factory=list)
    supporting_evidence: list[EvidenceItem] = field(default_factory=list)
    confidence: float = 0.0
    confidence_detail: dict[str, float] = field(default_factory=dict)
    recommendation: Recommendation = Recommendation.UNCERTAIN
    recommendation_reason: str = ""
    processing_metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_similarity": self.semantic_similarity,
            "concept_overlap": {
                "overlap_score": self.concept_overlap.overlap_score,
                "shared_concepts": self.concept_overlap.shared_concepts,
                "missing_in_a": self.concept_overlap.missing_in_a,
                "missing_in_b": self.concept_overlap.missing_in_b,
                "total_a": self.concept_overlap.total_a,
                "total_b": self.concept_overlap.total_b,
            },
            "entity_overlap": {
                "overlap_score": self.entity_overlap.overlap_score,
                "shared_entities": self.entity_overlap.shared_entities,
                "missing_in_a": self.entity_overlap.missing_in_a,
                "missing_in_b": self.entity_overlap.missing_in_b,
                "conflicts": self.entity_overlap.conflicts,
                "total_a": self.entity_overlap.total_a,
                "total_b": self.entity_overlap.total_b,
            },
            "intent_similarity": {
                "score": self.intent_similarity.score,
                "confidence": self.intent_similarity.confidence,
                "reason": self.intent_similarity.reason,
            },
            "relation_similarity": {
                "score": self.relation_similarity.score,
                "matching_relations": self.relation_similarity.matching_relations,
                "total_a": self.relation_similarity.total_a,
                "total_b": self.relation_similarity.total_b,
            },
            "context_similarity": {
                "score": self.context_similarity.score,
                "domain_match": self.context_similarity.domain_match,
                "constraints_match": self.context_similarity.constraints_match,
            },
            "conflicts": [
                {"type": c.conflict_type, "description": c.description, "severity": c.severity} for c in self.conflicts
            ],
            "supporting_evidence": [
                {"category": e.category, "status": e.status, "message": e.message, "confidence": e.confidence}
                for e in self.supporting_evidence
            ],
            "confidence": self.confidence,
            "confidence_detail": self.confidence_detail,
            "recommendation": self.recommendation.value,
            "recommendation_reason": self.recommendation_reason,
            "processing_metadata": {
                "processing_time_ms": self.processing_metadata.processing_time_ms,
                "stages": self.processing_metadata.stages,
                "components_used": self.processing_metadata.components_used,
            },
        }
