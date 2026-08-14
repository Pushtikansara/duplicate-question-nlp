from __future__ import annotations

import time
from typing import Any

from ares._result import PredictionResult
from ares.adaptive.models import ReflectionRecord
from ares.confidence import (
    compute_final_confidence,
    compute_risk_level,
    compute_trust_level,
    compute_trust_score,
)
from ares.semantic_validator import validate_semantic


class AdaptiveReflection:
    """Conditional reflection built on the existing semantic validation and
    confidence/trust routines.

    Reflection only executes when the routing plan requested it and the budget
    permits it; otherwise the reason is recorded instead of the computation.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}

    def reflect(
        self,
        result: PredictionResult,
        question1: str,
        question2: str,
        *,
        requested: bool,
        skipped_reason: str | None,
        agreement: float | None = None,
        uncertainty: float | None = None,
        model_count: int = 1,
        mode: str = "selected",
    ) -> ReflectionRecord:
        if not requested:
            return ReflectionRecord(requested=False, executed=False, skipped_reason=skipped_reason)

        start = time.perf_counter()
        try:
            semantic = validate_semantic(question1, question2, result)
        except Exception:
            semantic = None

        adjusted = semantic.get("adjusted_confidence", result.confidence) if semantic else result.confidence
        contradiction_count = semantic.get("semantic_detail", {}).get("contradiction_count", 0) if semantic else 0

        confidence_result = compute_final_confidence(
            raw_confidence=result.confidence,
            adjusted_confidence=adjusted,
            agreement_score=agreement,
            trust_score=result.trust_score,
            uncertainty=uncertainty,
            mode=mode,
            model_count=model_count,
        )
        final_confidence = confidence_result["final_confidence"]
        result.confidence = final_confidence

        trust_score = compute_trust_score(
            confidence=final_confidence,
            agreement=agreement,
            contradiction_count=contradiction_count,
            uncertainty=uncertainty,
        )
        result.trust_score = trust_score
        result.trust_level = compute_trust_level(trust_score)
        result.risk_level = compute_risk_level(
            trust_score=trust_score,
            confidence=final_confidence,
            agreement=agreement,
            uncertainty=uncertainty,
            contradiction_count=contradiction_count,
        )
        result.human_review_required = trust_score < 0.4
        result.recommendations = self._recommendations(trust_score)

        elapsed = (time.perf_counter() - start) * 1000
        return ReflectionRecord(
            requested=True,
            executed=True,
            reason=None,
            trust_score=trust_score,
            risk_level=result.risk_level,
            human_review_required=result.human_review_required,
            recommendations=list(result.recommendations),
            latency_ms=round(elapsed, 4),
        )

    @staticmethod
    def _recommendations(trust_score: float) -> list[str]:
        recs: list[str] = []
        if trust_score < 0.7:
            recs.append("review_manually")
        if trust_score < 0.5:
            recs.append("recheck_similarity")
        if trust_score < 0.3:
            recs.append("flag_for_expert_review")
        return recs
