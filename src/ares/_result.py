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

    selected_model: str | None = None
    executed_model: str | None = None
    backend: str | None = None
    artifact_path: str | None = None
    tokenizer: str | None = None
    inference_function: str | None = None
    execution_time_ms: float = 0.0
    raw_logits: list[float] | None = None
    softmax: list[float] | None = None
    predicted_class_id: int | None = None
    label_mapping: dict[int, str] | None = None
    final_label: str | None = None
    threshold: float = 0.5
    error: str | None = None
    error_code: str | None = None
    orchestration_trace: dict[str, Any] | None = None
    adaptive_trace: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "predicted_label": self.predicted_label,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "prob_duplicate": self.prob_duplicate,
            "prob_non_duplicate": self.prob_non_duplicate,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
            "selected_model": self.selected_model,
            "executed_model": self.executed_model,
            "backend": self.backend,
            "artifact_path": self.artifact_path,
            "tokenizer": self.tokenizer,
            "inference_function": self.inference_function,
            "execution_time_ms": self.execution_time_ms,
            "raw_logits": self.raw_logits,
            "softmax": self.softmax,
            "predicted_class_id": self.predicted_class_id,
            "label_mapping": self.label_mapping,
            "final_label": self.final_label,
            "threshold": self.threshold,
            "trust_score": self.trust_score,
            "trust_level": self.trust_level,
            "risk_level": self.risk_level,
            "human_review_required": self.human_review_required,
            "recommendations": self.recommendations,
        }
        if self.explanations:
            d["explanations"] = self.explanations
        if self.error is not None:
            d["error"] = self.error
        if self.error_code is not None:
            d["error_code"] = self.error_code
        if self.orchestration_trace is not None:
            d["orchestration_trace"] = self.orchestration_trace
        if self.adaptive_trace is not None:
            d["adaptive_trace"] = self.adaptive_trace
        return d
