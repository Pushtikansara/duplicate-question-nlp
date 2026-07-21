from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from duplicate_question_app._reflection.interfaces import (
    AuditorResult,
    ConsistencyWarning,
    RecommendationType,
    RiskLevel,
    TrustLevel,
)


@dataclass
class ReflectionResult:
    prediction: dict[str, Any]
    confidence: float
    trust_score: float
    trust_level: TrustLevel
    risk_level: RiskLevel
    routing_assessment: AuditorResult | None = None
    reasoning_assessment: AuditorResult | None = None
    debate_assessment: AuditorResult | None = None
    memory_assessment: AuditorResult | None = None
    confidence_assessment: AuditorResult | None = None
    explainability_score: float = 0.0
    evidence_completeness: float = 0.0
    calibration_assessment: dict[str, Any] = field(default_factory=dict)
    consistency_warnings: list[ConsistencyWarning] = field(default_factory=list)
    recommendations: list[RecommendationType] = field(default_factory=list)
    human_review_required: bool = False
    human_review_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction": {
                "predicted_label": self.prediction.get("predicted_label"),
                "prediction": self.prediction.get("prediction"),
                "confidence": self.confidence,
                "prob_duplicate": self.prediction.get("prob_duplicate"),
            },
            "trust_score": self.trust_score,
            "trust_level": self.trust_level.value,
            "risk_level": self.risk_level.value,
            "routing_assessment": self.routing_assessment.to_dict() if self.routing_assessment else None,
            "reasoning_assessment": self.reasoning_assessment.to_dict() if self.reasoning_assessment else None,
            "debate_assessment": self.debate_assessment.to_dict() if self.debate_assessment else None,
            "memory_assessment": self.memory_assessment.to_dict() if self.memory_assessment else None,
            "confidence_assessment": self.confidence_assessment.to_dict() if self.confidence_assessment else None,
            "explainability_score": self.explainability_score,
            "evidence_completeness": self.evidence_completeness,
            "consistency_warnings": [w.to_dict() for w in self.consistency_warnings],
            "recommendations": [r.value for r in self.recommendations],
            "human_review_required": self.human_review_required,
            "human_review_reason": self.human_review_reason,
            "timestamp": self.timestamp,
        }
