from dataclasses import dataclass, field
from typing import Any


@dataclass
class PredictionResult:
    predicted_label: int
    prediction: str
    confidence: float
    prob_duplicate: float
    prob_non_duplicate: float
    model_name: str
    latency_ms: float
    trust_score: float | None = None
    trust_level: str | None = None
    risk_level: str | None = None
    human_review_required: bool = False
    recommendations: list[str] = field(default_factory=list)
    explanations: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "predicted_label": self.predicted_label,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "prob_duplicate": self.prob_duplicate,
            "prob_non_duplicate": self.prob_non_duplicate,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
        }
        if self.trust_score is not None:
            d["trust_score"] = self.trust_score
            d["trust_level"] = self.trust_level
            d["risk_level"] = self.risk_level
            d["human_review_required"] = self.human_review_required
            d["recommendations"] = self.recommendations
        if self.explanations:
            d["explanations"] = self.explanations
        return d
