from __future__ import annotations

from typing import Any

from ares.adaptive.models import (
    ComputeBudget,
    DifficultyAssessment,
    DisagreementAssessment,
    ModelEvidence,
    ReflectionRecord,
    RoutingPlan,
)
from ares.adaptive.trust import TrustAssessment


def build_adaptive_trace(
    *,
    assessment: DifficultyAssessment,
    plan: RoutingPlan,
    budget: ComputeBudget,
    evidences: list[ModelEvidence],
    disagreement: DisagreementAssessment | None,
    escalation_count: int,
    escalation_reasons: list[str],
    early_exit: bool,
    early_exit_reason: str | None,
    stopping_reason: str | None = None,
    reflection: ReflectionRecord | None,
    stages_executed: list[str],
    stages_skipped: list[str],
    consumed_latency_ms: float,
    final_strategy: str,
    final_model: str,
    final_confidence: float,
    review_required: bool,
    routing_explanation: str,
    error: str | None = None,
    error_code: str | None = None,
    fallback_used: bool = False,
    trust: TrustAssessment | None = None,
) -> dict[str, Any]:
    """Assemble the additive Phase 14 adaptive trace sections.

    The returned mapping is merged into the existing orchestration trace by the
    pipeline enrichment / finalisation steps — existing consumers keep seeing
    every Phase 13 key unchanged.
    """
    executed_models = [e.model_name for e in evidences]
    trace: dict[str, Any] = {
        "routing": {
            "initial_strategy": plan.initial_strategy,
            "selected_model": plan.initial_model,
            "routing_reason": routing_explanation,
            "difficulty": assessment.difficulty_level,
            "difficulty_score": assessment.difficulty_score,
            "uncertainty_score": assessment.uncertainty_score,
            "risk": assessment.risk_level,
        },
        "execution": {
            "models_executed": list(dict.fromkeys(executed_models)),
            "model_calls": len(evidences),
            "stages_executed": list(stages_executed),
            "stages_skipped": list(stages_skipped),
        },
        "adaptive": {
            "escalation_count": escalation_count,
            "escalation_reasons": list(escalation_reasons),
            "early_exit": early_exit,
            "early_exit_reason": early_exit_reason,
            "stopping_reason": stopping_reason,
            "reflection_requested": bool(reflection and reflection.requested),
            "reflection_executed": bool(reflection and reflection.executed),
            "reflection_reason": (reflection.reason if reflection else None),
            "reflection_skipped_reason": (reflection.skipped_reason if reflection else None),
            "fusion_requested": plan.fusion_requested,
            "fusion_method": plan.fusion_method if disagreement else None,
            "human_review_recommended": plan.human_review_recommended,
        },
        "trust": trust.to_dict() if trust is not None else None,
        "evidence": {
            "model_predictions": [e.to_dict() for e in evidences],
            "confidence": final_confidence,
            "disagreement": disagreement.to_dict() if disagreement else None,
        },
        "budget": {
            "configured_budget": budget.to_dict(),
            "consumed_budget": {
                "model_calls": len(evidences),
                "latency_ms": round(consumed_latency_ms, 3),
                "escalation_level": escalation_count,
            },
        },
        "final": {
            "final_strategy": final_strategy,
            "final_model": final_model,
            "final_confidence": final_confidence,
            "review_required": review_required,
        },
    }
    if error is not None:
        trace["error"] = error
        trace["error_code"] = error_code
        trace["fallback_used"] = fallback_used
    return trace
