from __future__ import annotations

from typing import Any

from duplicate_question_app._reflection.interfaces import AuditorResult, RoutingAuditorABC


class RoutingAuditor(RoutingAuditorABC):
    def audit(self, routing_result: Any) -> AuditorResult:
        if routing_result is None:
            return AuditorResult(
                module="routing",
                score=0.5,
                details={"available": False},
                warnings=["No routing result available"],
                passed=False,
            )
        details: dict[str, Any] = {}
        warnings: list[str] = []
        score = 1.0

        pipeline = getattr(routing_result, "selected_pipeline", "unknown")
        details["selected_pipeline"] = pipeline

        complexity = getattr(routing_result, "complexity", "unknown")
        details["complexity"] = complexity

        required = getattr(routing_result, "required_modules", []) or []
        skipped = getattr(routing_result, "skipped_modules", []) or []
        details["required_modules"] = required
        details["skipped_modules"] = skipped

        confidence = getattr(routing_result, "confidence", 1.0)
        details["routing_confidence"] = confidence

        if confidence < 0.5:
            score -= 0.3
            warnings.append(f"Routing confidence low: {confidence:.2f}")
        if not required:
            score -= 0.2
            warnings.append("No required modules specified by routing")

        details["pipeline_appropriate"] = len(required) >= 2 or len(skipped) <= 2
        score = max(0.0, min(1.0, score))
        return AuditorResult(
            module="routing",
            score=score,
            details=details,
            warnings=warnings,
            passed=score >= 0.5,
        )
