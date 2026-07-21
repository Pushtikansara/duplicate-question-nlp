from __future__ import annotations

from typing import Any


class QualityEstimator:
    def estimate(self, reflection_result: Any) -> dict[str, Any]:
        trust_score = getattr(reflection_result, "trust_score", 0.0)
        warnings = getattr(reflection_result, "consistency_warnings", []) or []
        assessments = [
            getattr(reflection_result, "routing_assessment", None),
            getattr(reflection_result, "reasoning_assessment", None),
            getattr(reflection_result, "debate_assessment", None),
            getattr(reflection_result, "memory_assessment", None),
            getattr(reflection_result, "confidence_assessment", None),
        ]

        avg_assessment_score = 0.0
        count = 0
        for a in assessments:
            if a is not None:
                avg_assessment_score += getattr(a, "score", 0.0)
                count += 1
        avg_assessment_score = avg_assessment_score / count if count > 0 else 0.0

        quality = trust_score / 100.0 * 0.7 + avg_assessment_score * 0.3
        quality = max(0.0, min(1.0, quality))

        warning_penalty = len(warnings) * 0.05
        quality = max(0.0, quality - warning_penalty)

        if quality >= 0.8:
            level = "high"
        elif quality >= 0.6:
            level = "medium"
        elif quality >= 0.4:
            level = "low"
        else:
            level = "critical"

        return {
            "quality_score": round(quality, 4),
            "quality_level": level,
            "avg_assessment_score": round(avg_assessment_score, 4),
            "warning_penalty": round(warning_penalty, 4),
            "warning_count": len(warnings),
        }
