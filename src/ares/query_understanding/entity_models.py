from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    text: str = ""
    entity_type: str = "OTHER"
    normalized: str = ""
    confidence: float = 1.0
    start: int = 0
    end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "entity_type": self.entity_type,
            "normalized": self.normalized,
            "confidence": self.confidence,
            "start": self.start,
            "end": self.end,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Entity:
        return cls(
            text=data.get("text", ""),
            entity_type=data.get("entity_type", "OTHER"),
            normalized=data.get("normalized", ""),
            confidence=data.get("confidence", 1.0),
            start=data.get("start", 0),
            end=data.get("end", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class EntityPairMatch:
    entity_1: Entity = field(default_factory=Entity)
    entity_2: Entity = field(default_factory=Entity)
    match_type: str = "no_match"
    similarity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_1": self.entity_1.to_dict(),
            "entity_2": self.entity_2.to_dict(),
            "match_type": self.match_type,
            "similarity": self.similarity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntityPairMatch:
        return cls(
            entity_1=Entity.from_dict(data.get("entity_1", {})),
            entity_2=Entity.from_dict(data.get("entity_2", {})),
            match_type=data.get("match_type", "no_match"),
            similarity=data.get("similarity", 0.0),
        )


@dataclass
class EntityResult:
    entities_1: list[Entity] = field(default_factory=list)
    entities_2: list[Entity] = field(default_factory=list)
    shared_entities: list[EntityPairMatch] = field(default_factory=list)
    unique_entities_q1: list[Entity] = field(default_factory=list)
    unique_entities_q2: list[Entity] = field(default_factory=list)
    entity_overlap_score: float = 0.0
    entity_relationship: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities_1": [e.to_dict() for e in self.entities_1],
            "entities_2": [e.to_dict() for e in self.entities_2],
            "shared_entities": [m.to_dict() for m in self.shared_entities],
            "unique_entities_q1": [e.to_dict() for e in self.unique_entities_q1],
            "unique_entities_q2": [e.to_dict() for e in self.unique_entities_q2],
            "entity_overlap_score": self.entity_overlap_score,
            "entity_relationship": self.entity_relationship,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntityResult:
        return cls(
            entities_1=[Entity.from_dict(e) for e in data.get("entities_1", [])],
            entities_2=[Entity.from_dict(e) for e in data.get("entities_2", [])],
            shared_entities=[EntityPairMatch.from_dict(m) for m in data.get("shared_entities", [])],
            unique_entities_q1=[Entity.from_dict(e) for e in data.get("unique_entities_q1", [])],
            unique_entities_q2=[Entity.from_dict(e) for e in data.get("unique_entities_q2", [])],
            entity_overlap_score=data.get("entity_overlap_score", 0.0),
            entity_relationship=data.get("entity_relationship", "unknown"),
        )


ENTITY_TYPES = frozenset(
    {
        "PERSON",
        "ORGANIZATION",
        "LOCATION",
        "COUNTRY",
        "CITY",
        "PRODUCT",
        "COMPANY",
        "PROGRAMMING_LANGUAGE",
        "FRAMEWORK",
        "LIBRARY",
        "OPERATING_SYSTEM",
        "FILE",
        "URL",
        "EMAIL",
        "DATE",
        "TIME",
        "YEAR",
        "VERSION",
        "NUMBER",
        "PERCENTAGE",
        "CURRENCY",
        "EVENT",
        "ACADEMIC_SUBJECT",
        "BOOK",
        "MOVIE",
        "OTHER",
    }
)

MATCH_TYPES = frozenset(
    {
        "exact_match",
        "case_difference",
        "abbreviation",
        "partial_match",
        "version_difference",
        "numeric_difference",
        "no_match",
    }
)

RELATIONSHIP_TYPES = frozenset(
    {
        "same_entity",
        "related_entities",
        "overlapping",
        "different_entities",
        "no_entities",
        "unknown",
    }
)
