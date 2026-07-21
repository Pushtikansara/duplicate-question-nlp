from __future__ import annotations

from typing import Any

from duplicate_question_app._reflection.interfaces import AuditorResult, ConfidenceAuditorABC


class ConfidenceAuditor(ConfidenceAuditorABC):
    def audit(self, prediction: dict[str, Any], calibration_data: dict[str, Any] | None) -> AuditorResult:
        details: dict[str, Any] = {}
        warnings: list[str] = []
        score = 1.0

        confidence = float(prediction.get("confidence", 0.5))
        prob_dup = float(prediction.get("prob_duplicate", 0.5))
        details["confidence"] = confidence
        details["prob_duplicate"] = prob_dup

        if confidence < 0.6:
            score -= 0.3
            warnings.append(f"Low confidence: {confidence:.2f}")
        if abs(prob_dup - 0.5) < 0.1:
            score -= 0.2
            warnings.append(f"Borderline prediction: prob={prob_dup:.3f}")

        if calibration_data is not None:
            ece = calibration_data.get("ece", 0.0)
            details["ece"] = ece
            if ece > 0.15:
                score -= 0.2
                warnings.append(f"High calibration error: ECE={ece:.4f}")

        score = max(0.0, min(1.0, score))
        return AuditorResult(
            module="confidence",
            score=score,
            details=details,
            warnings=warnings,
            passed=score >= 0.5,
        )
