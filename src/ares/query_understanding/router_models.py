from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

STRATEGY_FAST_LEXICAL = "fast_lexical"
STRATEGY_BASELINE = "baseline_classifier"
STRATEGY_CROSS_ENCODER = "cross_encoder"
STRATEGY_ENSEMBLE = "ensemble"
STRATEGY_FALLBACK = "fallback"

ROUTING_STRATEGIES = [
    STRATEGY_FAST_LEXICAL,
    STRATEGY_BASELINE,
    STRATEGY_CROSS_ENCODER,
    STRATEGY_ENSEMBLE,
    STRATEGY_FALLBACK,
]

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"

PRIORITY_LOW = "low"
PRIORITY_NORMAL = "normal"
PRIORITY_HIGH = "high"

_REASON_CODES = frozenset(
    {
        "exact_match",
        "very_low_complexity",
        "low_overlap",
        "high_overlap",
        "entity_dense",
        "negation_detected",
        "high_ambiguity",
        "numeric_conflict",
        "version_conflict",
        "date_conflict",
        "antonym_detected",
        "entity_conflict",
        "low_confidence",
        "high_risk",
        "complex_question",
        "very_long_question",
        "cross_lingual",
        "technical_domain",
        "code_snippet",
        "unknown_type",
        "evidence_conflict",
        "semantic_drift_detected",
        "length_mismatch",
        "empty_input",
        "fallback_default",
    }
)


@dataclass
class RoutingDecision:
    selected_strategy: str = STRATEGY_FALLBACK
    confidence: float = 0.0
    priority: str = PRIORITY_NORMAL
    reason_codes: list[str] = field(default_factory=list)
    triggered_rules: list[dict[str, Any]] = field(default_factory=list)
    risk_level: str = RISK_LOW
    estimated_cost: float = 0.0
    estimated_latency: float = 0.0
    explanation: str = ""
    processing_time: float = 0.0
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_strategy": self.selected_strategy,
            "confidence": self.confidence,
            "priority": self.priority,
            "reason_codes": self.reason_codes,
            "triggered_rules": self.triggered_rules,
            "risk_level": self.risk_level,
            "estimated_cost": self.estimated_cost,
            "estimated_latency": self.estimated_latency,
            "explanation": self.explanation,
            "processing_time": self.processing_time,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoutingDecision:
        return cls(
            selected_strategy=data.get("selected_strategy", STRATEGY_FALLBACK),
            confidence=data.get("confidence", 0.0),
            priority=data.get("priority", PRIORITY_NORMAL),
            reason_codes=data.get("reason_codes", []),
            triggered_rules=data.get("triggered_rules", []),
            risk_level=data.get("risk_level", RISK_LOW),
            estimated_cost=data.get("estimated_cost", 0.0),
            estimated_latency=data.get("estimated_latency", 0.0),
            explanation=data.get("explanation", ""),
            processing_time=data.get("processing_time", 0.0),
            version=data.get("version", "1.0.0"),
        )
