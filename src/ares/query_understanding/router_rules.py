from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ares.query_understanding.complexity_models import ComplexityAnalysis
from ares.query_understanding.entity_models import EntityResult
from ares.query_understanding.query_models import (
    QuestionMetadata,
    QuestionSimilarityFeatures,
)
from ares.query_understanding.relationship_models import RelationshipAnalysis
from ares.query_understanding.router_models import (
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    STRATEGY_BASELINE,
    STRATEGY_CROSS_ENCODER,
    STRATEGY_ENSEMBLE,
    STRATEGY_FALLBACK,
    STRATEGY_FAST_LEXICAL,
)
from ares.query_understanding.type_models import QuestionTypeResult


@dataclass
class RouterSignal:
    complexity: float = 0.0
    difficulty: str = ""
    ambiguity: float = 0.0
    entity_density: float = 0.0
    entity_count_total: int = 0
    numeric_density: float = 0.0
    has_negation: bool = False
    has_antonym: bool = False
    has_entity_conflict: bool = False
    has_numeric_conflict: bool = False
    has_version_conflict: bool = False
    has_date_conflict: bool = False
    has_exact_match: bool = False
    has_near_match: bool = False
    has_high_risk: bool = False
    has_low_confidence: bool = False
    has_semantic_drift: bool = False
    has_cross_lingual: bool = False
    has_code: bool = False
    overlap_ratio: float = 0.0
    jaccard: float = 0.0
    edit_distance: float = 0.0
    length_difference: int = 0
    question_type_pair: str = ""
    type_confidence: float = 0.0
    word_count_total: int = 0
    is_empty: bool = False


def _extract_signal(
    metadata_1: QuestionMetadata | None = None,
    metadata_2: QuestionMetadata | None = None,
    similarity: QuestionSimilarityFeatures | None = None,
    question_type: QuestionTypeResult | None = None,
    entity_analysis: EntityResult | None = None,
    relationship_analysis: RelationshipAnalysis | None = None,
    complexity_analysis: ComplexityAnalysis | None = None,
) -> RouterSignal:
    signal = RouterSignal()

    if complexity_analysis:
        signal.complexity = complexity_analysis.overall_complexity_score
        signal.difficulty = complexity_analysis.difficulty_level
        signal.ambiguity = complexity_analysis.ambiguity_score

    if entity_analysis:
        e1 = len(entity_analysis.entities_1) if entity_analysis.entities_1 else 0
        e2 = len(entity_analysis.entities_2) if entity_analysis.entities_2 else 0
        signal.entity_count_total = e1 + e2

    if complexity_analysis:
        signal.entity_density = complexity_analysis.entity_density

    total_w = 0
    if metadata_1:
        total_w += metadata_1.word_count
    if metadata_2:
        total_w += metadata_2.word_count
    signal.word_count_total = total_w

    if complexity_analysis:
        signal.numeric_density = complexity_analysis.numeric_density

    if similarity:
        signal.overlap_ratio = similarity.word_overlap_ratio

    if relationship_analysis:
        types = {r.relationship_type for r in relationship_analysis.relationship_types}
        signal.has_negation = "negation_introduced" in types or "negation_removed" in types
        signal.has_antonym = "antonym_detection" in types
        signal.has_entity_conflict = "entity_conflict" in relationship_analysis.risk_flags
        signal.has_numeric_conflict = "numeric_conflict" in relationship_analysis.risk_flags
        signal.has_version_conflict = "version_conflict" in relationship_analysis.risk_flags
        signal.has_date_conflict = "temporal_conflict" in relationship_analysis.risk_flags
        signal.has_exact_match = "exact_match" in types
        signal.has_near_match = "near_match" in types
        signal.has_high_risk = relationship_analysis.risk_score() > 40.0
        signal.has_semantic_drift = "high_semantic_drift" in relationship_analysis.risk_flags
        signal.jaccard = relationship_analysis.comparison_statistics.jaccard_similarity
        signal.edit_distance = float(relationship_analysis.comparison_statistics.edit_distance)
        signal.length_difference = relationship_analysis.comparison_statistics.length_difference

    if question_type:
        signal.question_type_pair = question_type.pair_type
        signal.type_confidence = question_type.classification_confidence

    if metadata_1:
        lang1 = metadata_1.language
        if metadata_2 and metadata_2.language != "unknown" and lang1 != "unknown" and lang1 != metadata_2.language:
            signal.has_cross_lingual = True
        signal.has_code = metadata_1.contains_code or (metadata_2 and metadata_2.contains_code)

    if complexity_analysis:
        signal.has_low_confidence = complexity_analysis.confidence_estimate < 0.3

    return signal


@dataclass
class RouterRule:
    name: str
    description: str
    weight: float
    category: str
    evaluate: Callable[[RouterSignal], float]

    def apply(self, signal: RouterSignal) -> float:
        return self.evaluate(signal)


def _register_rules() -> list[RouterRule]:
    return [
        RouterRule(
            name="exact_match_simple",
            description="Exact or near match with very low complexity (not for very short questions)",
            weight=1.0,
            category="fast_path",
            evaluate=lambda s: (
                1.0
                if s.has_exact_match and s.complexity < 0.2 and (s.word_count_total == 0 or s.word_count_total > 6)
                else 0.0
            ),
        ),
        RouterRule(
            name="very_low_complexity",
            description="Very low overall complexity",
            weight=0.9,
            category="fast_path",
            evaluate=lambda s: (
                1.0 if 0.0 < s.complexity < 0.15 and not (s.has_exact_match and 0 < s.word_count_total <= 6) else 0.0
            ),
        ),
        RouterRule(
            name="low_overlap_no_entities",
            description="Low overlap and no entities to resolve",
            weight=0.7,
            category="fast_path",
            evaluate=lambda s: (
                1.0
                if s.overlap_ratio < 0.3
                and s.entity_count_total == 0
                and not s.has_negation
                and not (s.has_exact_match and 0 < s.word_count_total <= 6)
                else 0.0
            ),
        ),
        RouterRule(
            name="high_jaccard_low_complexity",
            description="High Jaccard similarity with low complexity",
            weight=0.8,
            category="fast_path",
            evaluate=lambda s: 1.0 if s.jaccard > 0.7 and s.complexity < 0.3 else 0.0,
        ),
        RouterRule(
            name="entity_dense",
            description="High entity density requiring cross-encoder",
            weight=0.85,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.entity_density > 0.3 or s.entity_count_total >= 4 else 0.0,
        ),
        RouterRule(
            name="negation_conflict",
            description="Negation detected between questions",
            weight=0.9,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.has_negation else 0.0,
        ),
        RouterRule(
            name="antonym_conflict",
            description="Antonym detected between questions",
            weight=0.85,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.has_antonym else 0.0,
        ),
        RouterRule(
            name="numeric_conflict",
            description="Numeric or version conflicts present",
            weight=0.8,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.has_numeric_conflict or s.has_version_conflict else 0.0,
        ),
        RouterRule(
            name="entity_conflict",
            description="Entity replacement or conflict detected",
            weight=0.8,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.has_entity_conflict else 0.0,
        ),
        RouterRule(
            name="date_conflict",
            description="Date or temporal conflicts present",
            weight=0.75,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.has_date_conflict else 0.0,
        ),
        RouterRule(
            name="high_ambiguity",
            description="High ambiguity requires ensemble",
            weight=0.85,
            category="ensemble",
            evaluate=lambda s: 1.0 if s.ambiguity > 0.4 else 0.0,
        ),
        RouterRule(
            name="high_risk",
            description="High risk score requires ensemble",
            weight=0.8,
            category="ensemble",
            evaluate=lambda s: 1.0 if s.has_high_risk else 0.0,
        ),
        RouterRule(
            name="low_confidence",
            description="Low confidence estimate requires ensemble",
            weight=0.75,
            category="ensemble",
            evaluate=lambda s: 1.0 if s.has_low_confidence else 0.0,
        ),
        RouterRule(
            name="semantic_drift",
            description="High semantic drift detected",
            weight=0.8,
            category="ensemble",
            evaluate=lambda s: 1.0 if s.has_semantic_drift else 0.0,
        ),
        RouterRule(
            name="very_short_exact",
            description="Very short exact questions can use baseline",
            weight=0.7,
            category="baseline",
            evaluate=lambda s: 1.0 if s.has_exact_match and s.word_count_total <= 6 else 0.0,
        ),
        RouterRule(
            name="high_overlap_baseline",
            description="High overlap with basic types",
            weight=0.6,
            category="baseline",
            evaluate=lambda s: (
                1.0 if s.overlap_ratio > 0.6 and not s.has_negation and not s.has_entity_conflict else 0.0
            ),
        ),
        RouterRule(
            name="complex_question",
            description="Very complex questions need cross-encoder",
            weight=0.85,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.complexity > 0.6 else 0.0,
        ),
        RouterRule(
            name="cross_lingual",
            description="Cross-lingual pair needs cross-encoder",
            weight=0.9,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.has_cross_lingual else 0.0,
        ),
        RouterRule(
            name="code_snippet",
            description="Code snippets in questions",
            weight=0.75,
            category="cross_encoder",
            evaluate=lambda s: 1.0 if s.has_code else 0.0,
        ),
        RouterRule(
            name="fallback_default",
            description="Fallback for unhandled cases",
            weight=0.5,
            category="fallback",
            evaluate=lambda s: 1.0 if s.is_empty or (s.complexity == 0.0 and not s.has_exact_match) else 0.0,
        ),
    ]


_STRATEGY_COST: dict[str, float] = {
    STRATEGY_FAST_LEXICAL: 0.01,
    STRATEGY_BASELINE: 0.05,
    STRATEGY_CROSS_ENCODER: 0.5,
    STRATEGY_ENSEMBLE: 1.0,
    STRATEGY_FALLBACK: 0.0,
}

_STRATEGY_LATENCY: dict[str, float] = {
    STRATEGY_FAST_LEXICAL: 0.5,
    STRATEGY_BASELINE: 2.0,
    STRATEGY_CROSS_ENCODER: 10.0,
    STRATEGY_ENSEMBLE: 25.0,
    STRATEGY_FALLBACK: 0.0,
}

_STRATEGY_RISK: dict[str, str] = {
    STRATEGY_FAST_LEXICAL: RISK_LOW,
    STRATEGY_BASELINE: RISK_LOW,
    STRATEGY_CROSS_ENCODER: RISK_MEDIUM,
    STRATEGY_ENSEMBLE: RISK_HIGH,
    STRATEGY_FALLBACK: RISK_HIGH,
}

_STRATEGY_PRIORITY: dict[str, str] = {
    STRATEGY_FAST_LEXICAL: "low",
    STRATEGY_BASELINE: "normal",
    STRATEGY_CROSS_ENCODER: "high",
    STRATEGY_ENSEMBLE: "high",
    STRATEGY_FALLBACK: "normal",
}


def compute_strategy_scores(signal: RouterSignal, rules: list[RouterRule]) -> dict[str, dict[str, Any]]:
    category_scores: dict[str, float] = {
        STRATEGY_FAST_LEXICAL: 0.0,
        STRATEGY_BASELINE: 0.0,
        STRATEGY_CROSS_ENCODER: 0.0,
        STRATEGY_ENSEMBLE: 0.0,
        STRATEGY_FALLBACK: 0.0,
    }

    category_map: dict[str, str] = {
        "fast_path": STRATEGY_FAST_LEXICAL,
        "baseline": STRATEGY_BASELINE,
        "cross_encoder": STRATEGY_CROSS_ENCODER,
        "ensemble": STRATEGY_ENSEMBLE,
        "fallback": STRATEGY_FALLBACK,
    }

    triggered: list[dict[str, Any]] = []

    for rule in rules:
        score = rule.apply(signal)
        if score > 0:
            strategy = category_map.get(rule.category)
            if strategy:
                category_scores[strategy] = max(category_scores[strategy], score * rule.weight)
                triggered.append(
                    {
                        "rule": rule.name,
                        "description": rule.description,
                        "category": rule.category,
                        "score": round(score * rule.weight, 4),
                        "weight": rule.weight,
                    }
                )

    results: dict[str, dict[str, Any]] = {}
    for strategy, score in category_scores.items():
        results[strategy] = {
            "score": score,
            "cost": _STRATEGY_COST[strategy],
            "latency": _STRATEGY_LATENCY[strategy],
            "risk": _STRATEGY_RISK[strategy],
            "priority": _STRATEGY_PRIORITY[strategy],
        }

    return results, triggered
