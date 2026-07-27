from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RELATIONSHIP_TYPES = frozenset(
    {
        "exact_match",
        "near_match",
        "lexical_reformulation",
        "word_order_change",
        "sentence_structure_change",
        "passive_to_active_voice",
        "active_to_passive_voice",
        "negation_introduced",
        "negation_removed",
        "double_negation",
        "question_polarity_change",
        "entity_replacement",
        "entity_addition",
        "entity_removal",
        "entity_reordering",
        "version_difference",
        "numeric_difference",
        "date_difference",
        "time_difference",
        "currency_difference",
        "unit_difference",
        "percentage_difference",
        "abbreviation_expansion",
        "abbreviation_compression",
        "acronym_match",
        "synonym_replacement",
        "antonym_detection",
        "pronoun_replacement",
        "reference_shift",
        "punctuation_only",
        "formatting_only",
        "capitalization_only",
        "whitespace_only",
        "typographical_difference",
        "spelling_variant",
        "duplicate_tokens",
        "repeated_words",
        "inserted_clause",
        "removed_clause",
        "unknown_relationship",
    }
)

RISK_FLAGS = frozenset(
    {
        "meaning_changed",
        "possible_false_positive",
        "possible_false_negative",
        "entity_conflict",
        "numeric_conflict",
        "temporal_conflict",
        "version_conflict",
        "negation_conflict",
        "ambiguous_difference",
        "high_semantic_drift",
        "low_semantic_drift",
    }
)

SEMANTIC_FLAGS = frozenset(
    {
        "equivalent_intent",
        "same_entity",
        "different_entity",
        "more_specific",
        "less_specific",
        "broader_query",
        "narrower_query",
        "temporal_shift",
        "numeric_shift",
        "negation_shift",
        "polarity_change",
        "scope_change",
        "perspective_change",
        "certainty_change",
        "formality_change",
        "technical_level_change",
        "ambiguity_change",
    }
)


@dataclass
class TransformationStep:
    step_type: str = ""
    description: str = ""
    tokens_q1: list[str] = field(default_factory=list)
    tokens_q2: list[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_type": self.step_type,
            "description": self.description,
            "tokens_q1": self.tokens_q1,
            "tokens_q2": self.tokens_q2,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransformationStep:
        return cls(
            step_type=data.get("step_type", ""),
            description=data.get("description", ""),
            tokens_q1=data.get("tokens_q1", []),
            tokens_q2=data.get("tokens_q2", []),
            confidence=data.get("confidence", 1.0),
        )


@dataclass
class TransformationChain:
    steps: list[TransformationStep] = field(default_factory=list)
    final_intent: str = "unknown"
    is_equivalent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "final_intent": self.final_intent,
            "is_equivalent": self.is_equivalent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransformationChain:
        return cls(
            steps=[TransformationStep.from_dict(s) for s in data.get("steps", [])],
            final_intent=data.get("final_intent", "unknown"),
            is_equivalent=data.get("is_equivalent", False),
        )


@dataclass
class Evidence:
    rule_name: str = ""
    rule_layer: int = 0
    matched_pattern: str = ""
    tokens_q1: list[str] = field(default_factory=list)
    tokens_q2: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "rule_layer": self.rule_layer,
            "matched_pattern": self.matched_pattern,
            "tokens_q1": self.tokens_q1,
            "tokens_q2": self.tokens_q2,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Evidence:
        return cls(
            rule_name=data.get("rule_name", ""),
            rule_layer=data.get("rule_layer", 0),
            matched_pattern=data.get("matched_pattern", ""),
            tokens_q1=data.get("tokens_q1", []),
            tokens_q2=data.get("tokens_q2", []),
            confidence=data.get("confidence", 0.0),
        )


@dataclass
class RelationshipInfo:
    relationship_type: str = ""
    confidence: float = 0.0
    evidence: list[Evidence] = field(default_factory=list)
    human_explanation: str = ""
    developer_explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "human_explanation": self.human_explanation,
            "developer_explanation": self.developer_explanation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RelationshipInfo:
        return cls(
            relationship_type=data.get("relationship_type", ""),
            confidence=data.get("confidence", 0.0),
            evidence=[Evidence.from_dict(e) for e in data.get("evidence", [])],
            human_explanation=data.get("human_explanation", ""),
            developer_explanation=data.get("developer_explanation", ""),
        )


@dataclass
class ComparisonStatistics:
    token_count_q1: int = 0
    token_count_q2: int = 0
    char_count_q1: int = 0
    char_count_q2: int = 0
    word_count_q1: int = 0
    word_count_q2: int = 0
    token_overlap: int = 0
    token_overlap_ratio: float = 0.0
    edit_distance: int = 0
    normalized_edit_distance: float = 0.0
    jaccard_similarity: float = 0.0
    length_difference: int = 0
    shared_token_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_count_q1": self.token_count_q1,
            "token_count_q2": self.token_count_q2,
            "char_count_q1": self.char_count_q1,
            "char_count_q2": self.char_count_q2,
            "word_count_q1": self.word_count_q1,
            "word_count_q2": self.word_count_q2,
            "token_overlap": self.token_overlap,
            "token_overlap_ratio": self.token_overlap_ratio,
            "edit_distance": self.edit_distance,
            "normalized_edit_distance": self.normalized_edit_distance,
            "jaccard_similarity": self.jaccard_similarity,
            "length_difference": self.length_difference,
            "shared_token_ratio": self.shared_token_ratio,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComparisonStatistics:
        return cls(**{k: data.get(k, 0) for k in cls.__dataclass_fields__})


@dataclass
class RelationshipAnalysis:
    relationship_types: list[RelationshipInfo] = field(default_factory=list)
    relationship_score: float = 0.0
    relationship_confidence: float = 0.0
    relationship_summary: str = ""
    semantic_flags: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    transformation_chain: TransformationChain = field(default_factory=TransformationChain)
    comparison_statistics: ComparisonStatistics = field(default_factory=ComparisonStatistics)
    processing_time: float = 0.0
    version: str = "1.0.0"

    def primary_relationship(self) -> str:
        if not self.relationship_types:
            return "unknown_relationship"
        return max(self.relationship_types, key=lambda r: r.confidence).relationship_type

    def risk_score(self) -> float:
        high_risk = {
            "meaning_changed",
            "negation_conflict",
            "entity_conflict",
            "numeric_conflict",
            "temporal_conflict",
            "version_conflict",
        }
        medium_risk = {
            "possible_false_positive",
            "possible_false_negative",
            "high_semantic_drift",
            "ambiguous_difference",
        }
        score = 0.0
        for flag in self.risk_flags:
            if flag in high_risk:
                score += 25.0
            elif flag in medium_risk:
                score += 15.0
            else:
                score += 5.0
        return min(100.0, score)

    def semantic_distance(self) -> float:
        opposite = {"exact_match", "punctuation_only", "formatting_only", "capitalization_only", "whitespace_only"}
        for r in self.relationship_types:
            if r.relationship_type in opposite:
                return 0.0
        base = 1.0 - self.relationship_score / 100.0
        for r in self.relationship_types:
            if r.relationship_type in {
                "negation_introduced",
                "negation_removed",
                "antonym_detection",
                "question_polarity_change",
            }:
                base = min(1.0, base + 0.3)
        return round(base * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_types": [r.to_dict() for r in self.relationship_types],
            "relationship_score": self.relationship_score,
            "relationship_confidence": self.relationship_confidence,
            "relationship_summary": self.relationship_summary,
            "semantic_flags": self.semantic_flags,
            "risk_flags": self.risk_flags,
            "transformation_chain": self.transformation_chain.to_dict(),
            "comparison_statistics": self.comparison_statistics.to_dict(),
            "processing_time": self.processing_time,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RelationshipAnalysis:
        return cls(
            relationship_types=[RelationshipInfo.from_dict(r) for r in data.get("relationship_types", [])],
            relationship_score=data.get("relationship_score", 0.0),
            relationship_confidence=data.get("relationship_confidence", 0.0),
            relationship_summary=data.get("relationship_summary", ""),
            semantic_flags=data.get("semantic_flags", []),
            risk_flags=data.get("risk_flags", []),
            transformation_chain=TransformationChain.from_dict(data.get("transformation_chain", {})),
            comparison_statistics=ComparisonStatistics.from_dict(data.get("comparison_statistics", {})),
            processing_time=data.get("processing_time", 0.0),
            version=data.get("version", "1.0.0"),
        )


@dataclass
class RelationshipRule:
    name: str
    layer: int
    description: str
    priority: int = 100
    enabled: bool = True
