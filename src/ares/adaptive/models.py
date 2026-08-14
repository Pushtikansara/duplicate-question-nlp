from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Phase 14 shared data models for the ARES Adaptive Routing / Intelligence
# layer.  These types are deliberately domain-agnostic (a "request" is a pair
# of strings, a "model" is a named runtime) so future applications can reuse
# the router without modification.
# ---------------------------------------------------------------------------


@dataclass
class DifficultyAssessment:
    """Deterministic assessment of how hard a request is to answer.

    Produced entirely by the difficulty analyzer: no external LLM, no
    randomness, so identical requests always yield identical assessments.
    """

    difficulty_score: float = 0.0
    difficulty_level: str = "easy"
    uncertainty_score: float = 0.0
    risk_level: str = "low"
    signals: dict[str, float] = field(default_factory=dict)
    signal_details: dict[str, list[str]] = field(default_factory=dict)
    recommended_budget: str = "low"
    recommended_strategy: str = "fast_lexical"
    explanation: str = ""
    processing_time_ms: float = 0.0
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "difficulty_score": self.difficulty_score,
            "difficulty_level": self.difficulty_level,
            "uncertainty_score": self.uncertainty_score,
            "risk_level": self.risk_level,
            "signals": dict(self.signals),
            "signal_details": {k: list(v) for k, v in self.signal_details.items()},
            "recommended_budget": self.recommended_budget,
            "recommended_strategy": self.recommended_strategy,
            "explanation": self.explanation,
            "processing_time_ms": self.processing_time_ms,
            "version": self.version,
        }


@dataclass(frozen=True)
class ModelProfile:
    """Static capability / cost metadata for one model.

    Created from the existing model registry and merged with configuration
    driven values.  The router never hard-codes per-model logic: everything
    it needs is read from these profiles.
    """

    model_name: str
    internal_id: str
    model_type: str
    capability_tier: str
    expected_accuracy: float
    expected_latency_ms: float
    computational_cost: float
    memory_cost_mb: float
    confidence_quality: float
    reliability: float
    fallback_priority: int
    supported_tasks: tuple[str, ...] = ("duplicate_detection",)
    available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "internal_id": self.internal_id,
            "model_type": self.model_type,
            "capability_tier": self.capability_tier,
            "expected_accuracy": self.expected_accuracy,
            "expected_latency_ms": self.expected_latency_ms,
            "computational_cost": self.computational_cost,
            "memory_cost_mb": self.memory_cost_mb,
            "confidence_quality": self.confidence_quality,
            "reliability": self.reliability,
            "fallback_priority": self.fallback_priority,
            "supported_tasks": list(self.supported_tasks),
            "available": self.available,
        }


@dataclass(frozen=True)
class ComputeBudget:
    """Computation budget allocated to one request.

    ``max_model_calls`` limits total model invocations (single most important
    cost lever), ``max_escalation_level`` bounds the escalation ladder depth
    and ``max_latency_ms`` bounds wall-clock model time.
    """

    name: str
    max_model_calls: int
    max_escalation_level: int
    max_latency_ms: float
    reflection_allowed: bool
    fusion_min_models: int
    max_stages: int = 8

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_model_calls": self.max_model_calls,
            "max_escalation_level": self.max_escalation_level,
            "max_latency_ms": self.max_latency_ms,
            "reflection_allowed": self.reflection_allowed,
            "fusion_min_models": self.fusion_min_models,
            "max_stages": self.max_stages,
        }


@dataclass
class ModelEvidence:
    """One model's prediction captured during adaptive execution."""

    model_name: str
    strategy: str
    predicted_label: int
    prediction: str
    confidence: float
    prob_duplicate: float
    latency_ms: float
    error: str | None = None
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "strategy": self.strategy,
            "predicted_label": self.predicted_label,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "prob_duplicate": self.prob_duplicate,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "rank": self.rank,
        }


@dataclass
class DisagreementAssessment:
    """Detected disagreement across collected model evidence."""

    disagreement_score: float = 0.0
    disagreement_level: str = "none"
    labels: list[int] = field(default_factory=list)
    probabilities: list[float] = field(default_factory=list)
    resolution_strategy: str = "majority_vote"
    resolution_label: int = 0
    resolution_probability: float = 0.0
    explanation: str = ""
    evidence_count: int = 0
    difficulty_level: str | None = None
    risk_level: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "disagreement_score": self.disagreement_score,
            "disagreement_level": self.disagreement_level,
            "labels": list(self.labels),
            "probabilities": list(self.probabilities),
            "resolution_strategy": self.resolution_strategy,
            "resolution_label": self.resolution_label,
            "resolution_probability": self.resolution_probability,
            "explanation": self.explanation,
            "evidence_count": self.evidence_count,
            "difficulty_level": self.difficulty_level,
            "risk_level": self.risk_level,
        }


@dataclass
class RoutingPlan:
    """Deterministic plan describing how one request should be computed."""

    initial_strategy: str = "fast_lexical"
    initial_model: str = ""
    escalation_ladder: list[str] = field(default_factory=list)
    reflection_requested: bool = False
    reflection_reason: str | None = None
    reflection_skipped_reason: str | None = None
    early_exit_eligible: bool = False
    fusion_requested: bool = False
    fusion_reason: str | None = None
    fusion_method: str = "majority_vote"
    human_review_recommended: bool = False
    explanation: str = ""
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "initial_strategy": self.initial_strategy,
            "initial_model": self.initial_model,
            "escalation_ladder": list(self.escalation_ladder),
            "reflection_requested": self.reflection_requested,
            "reflection_reason": self.reflection_reason,
            "reflection_skipped_reason": self.reflection_skipped_reason,
            "early_exit_eligible": self.early_exit_eligible,
            "fusion_requested": self.fusion_requested,
            "fusion_reason": self.fusion_reason,
            "fusion_method": self.fusion_method,
            "human_review_recommended": self.human_review_recommended,
            "explanation": self.explanation,
            "version": self.version,
        }


@dataclass
class ReflectionRecord:
    """Conditional reflection outcome for one request."""

    requested: bool = False
    executed: bool = False
    reason: str | None = None
    skipped_reason: str | None = None
    trust_score: float | None = None
    risk_level: str | None = None
    human_review_required: bool = False
    recommendations: list[str] = field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "executed": self.executed,
            "reason": self.reason,
            "skipped_reason": self.skipped_reason,
            "trust_score": self.trust_score,
            "risk_level": self.risk_level,
            "human_review_required": self.human_review_required,
            "recommendations": list(self.recommendations),
            "latency_ms": self.latency_ms,
        }
