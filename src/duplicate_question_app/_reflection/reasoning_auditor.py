from __future__ import annotations

from typing import Any

from duplicate_question_app._reflection.interfaces import AuditorResult, ReasoningAuditorABC


class ReasoningAuditor(ReasoningAuditorABC):
    def audit(self, reasoning_result: Any) -> AuditorResult:
        if reasoning_result is None:
            return AuditorResult(
                module="reasoning",
                score=0.5,
                details={"available": False},
                warnings=["No reasoning result available"],
                passed=False,
            )
        details: dict[str, Any] = {}
        warnings: list[str] = []
        score = 1.0

        premises = getattr(reasoning_result, "premises", []) or []
        hypotheses = getattr(reasoning_result, "hypotheses", []) or []
        supporting = getattr(reasoning_result, "supporting_evidence", []) or []
        contradicting = getattr(reasoning_result, "contradicting_evidence", []) or []

        details["premise_count"] = len(premises)
        details["hypothesis_count"] = len(hypotheses)
        details["supporting_evidence_count"] = len(supporting)
        details["contradicting_evidence_count"] = len(contradicting)

        if len(premises) < 2:
            score -= 0.15
            warnings.append(f"Low premise count: {len(premises)}")
        if len(hypotheses) < 1:
            score -= 0.15
            warnings.append("No hypotheses generated")
        if len(supporting) == 0 and len(contradicting) == 0:
            score -= 0.2
            warnings.append("No evidence chains found")

        trace = getattr(reasoning_result, "reasoning_trace", None)
        details["reasoning_trace_available"] = trace is not None
        if trace is None:
            score -= 0.1
            warnings.append("No reasoning trace available")

        confidence = float(getattr(reasoning_result, "confidence", 0.0))
        uncertainty = float(getattr(reasoning_result, "uncertainty", 1.0))
        details["reasoning_confidence"] = confidence
        details["reasoning_uncertainty"] = uncertainty

        if uncertainty > 0.8:
            score -= 0.2
            warnings.append(f"High uncertainty: {uncertainty:.2f}")

        score = max(0.0, min(1.0, score))
        return AuditorResult(
            module="reasoning",
            score=score,
            details=details,
            warnings=warnings,
            passed=score >= 0.5,
        )
