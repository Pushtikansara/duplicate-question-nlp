from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReflectionConfig:
    enable_routing_audit: bool = True
    enable_reasoning_audit: bool = True
    enable_debate_audit: bool = True
    enable_memory_audit: bool = True
    enable_confidence_audit: bool = True
    enable_explainability: bool = True
    enable_consistency_check: bool = True
    enable_recommendations: bool = True
    enable_human_review: bool = True

    trust_weights: dict[str, float] = field(
        default_factory=lambda: {
            "routing_quality": 0.10,
            "reasoning_quality": 0.20,
            "debate_agreement": 0.15,
            "evidence_completeness": 0.15,
            "confidence_calibration": 0.15,
            "memory_quality": 0.10,
            "explainability_completeness": 0.10,
            "benchmark_consistency": 0.05,
        }
    )

    human_review_threshold: float = 40.0
    low_confidence_threshold: float = 0.6
    calibration_error_threshold: float = 0.15
    routing_confidence_threshold: float = 0.5
    evidence_completeness_threshold: float = 0.3
    max_warnings_before_review: int = 3
