"""SemanticRepresentation — the unified semantic knowledge object.

This is the ONLY object that future ARES reasoning engines receive as input.
It is embedded within CognitiveRepresentation and constructed from LinguisticProfile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SemanticConcept:
    id: str
    label: str
    normalized_form: str
    original_forms: list[str] = field(default_factory=list)
    confidence: float = 1.0
    source: str = "keyword"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticRelation:
    source_id: str
    target_id: str
    relation_type: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticRoleAssignment:
    role: str
    concept_ids: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class AmbiguityEntry:
    type: str
    description: str
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class ProcessingMetadata:
    total_concepts: int = 0
    total_relations: int = 0
    total_roles: int = 0
    ambiguity_count: int = 0
    processing_time_ms: float = 0.0
    stages: dict[str, float] = field(default_factory=dict)


@dataclass
class SemanticRepresentation:
    concepts: list[SemanticConcept] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    relationships: list[SemanticRelation] = field(default_factory=list)
    semantic_roles: list[SemanticRoleAssignment] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    domain: str | None = None
    intent_summary: str | None = None
    constraints: list[str] = field(default_factory=list)
    ambiguities: list[AmbiguityEntry] = field(default_factory=list)
    semantic_graph: Any = None
    semantic_confidence: float = 0.0
    confidence_detail: dict[str, float] = field(default_factory=dict)
    reasoning_metadata: dict[str, Any] = field(default_factory=dict)
    processing_metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "concepts": [
                {"id": c.id, "label": c.label, "normalized_form": c.normalized_form, "confidence": c.confidence}
                for c in self.concepts
            ],
            "entities": self.entities,
            "actions": self.actions,
            "objects": self.objects,
            "attributes": self.attributes,
            "relationships": [
                {"source": r.source_id, "target": r.target_id, "type": r.relation_type, "confidence": r.confidence}
                for r in self.relationships
            ],
            "semantic_roles": [
                {"role": sr.role, "concept_ids": sr.concept_ids, "confidence": sr.confidence}
                for sr in self.semantic_roles
            ],
            "context": self.context,
            "domain": self.domain,
            "intent_summary": self.intent_summary,
            "constraints": self.constraints,
            "ambiguities": [
                {"type": a.type, "description": a.description, "confidence": a.confidence} for a in self.ambiguities
            ],
            "semantic_graph": self.semantic_graph.to_dict() if self.semantic_graph is not None else None,
            "semantic_confidence": self.semantic_confidence,
            "confidence_detail": self.confidence_detail,
            "processing_metadata": {
                "total_concepts": self.processing_metadata.total_concepts,
                "total_relations": self.processing_metadata.total_relations,
                "total_roles": self.processing_metadata.total_roles,
                "ambiguity_count": self.processing_metadata.ambiguity_count,
                "processing_time_ms": self.processing_metadata.processing_time_ms,
            },
        }
