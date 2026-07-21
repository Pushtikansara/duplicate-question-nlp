from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ComplexityResult:
    complexity: str
    score: float
    features: dict[str, Any]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "complexity": self.complexity,
            "score": self.score,
            "features": self.features,
            "explanation": self.explanation,
        }


@dataclass
class UncertaintyResult:
    should_escalate: bool
    reason: str
    uncertainty_score: float
    contributing_factors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "should_escalate": self.should_escalate,
            "reason": self.reason,
            "uncertainty_score": self.uncertainty_score,
            "contributing_factors": self.contributing_factors,
        }


@dataclass
class PipelineSelection:
    pipeline: str
    required_modules: list[str]
    skipped_modules: list[str]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline": self.pipeline,
            "required_modules": self.required_modules,
            "skipped_modules": self.skipped_modules,
            "reason": self.reason,
        }


@dataclass
class RoutingResult:
    selected_pipeline: str
    reason: str
    complexity: str
    estimated_latency_ms: float
    estimated_cost: float
    required_modules: list[str]
    skipped_modules: list[str]
    confidence: float
    metadata: dict[str, Any]
    pipeline_selection: PipelineSelection | None = None
    complexity_result: ComplexityResult | None = None
    uncertainty_result: UncertaintyResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_pipeline": self.selected_pipeline,
            "reason": self.reason,
            "complexity": self.complexity,
            "estimated_latency_ms": self.estimated_latency_ms,
            "estimated_cost": self.estimated_cost,
            "required_modules": self.required_modules,
            "skipped_modules": self.skipped_modules,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "pipeline_selection": self.pipeline_selection.to_dict() if self.pipeline_selection else None,
            "complexity_result": self.complexity_result.to_dict() if self.complexity_result else None,
            "uncertainty_result": self.uncertainty_result.to_dict() if self.uncertainty_result else None,
        }
