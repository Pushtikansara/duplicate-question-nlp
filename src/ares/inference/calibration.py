from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CALIBRATION_THRESHOLDS: dict[str, float] = {
    "low_confidence": 0.5,
    "high_confidence": 0.95,
    "overconfidence_margin": 0.15,
}


@dataclass
class CalibrationReport:
    model_name: str
    raw_score: float
    calibrated_score: float
    threshold: float
    decision: str
    is_overconfident: bool
    is_underconfident: bool
    confidence_gap: float
    calibration_quality: str
    details: dict[str, Any] = field(default_factory=dict)


def calibrate_score(
    raw_score: float,
    model_name: str,
    threshold: float = 0.5,
    calibration_thresholds: dict[str, float] | None = None,
) -> CalibrationReport:
    ct = dict(DEFAULT_CALIBRATION_THRESHOLDS)
    if calibration_thresholds:
        ct.update(calibration_thresholds)
    calibrated_score = _apply_isotonic_scaling(raw_score, model_name)
    decision = "duplicate" if calibrated_score >= threshold else "non_duplicate"
    overconfidence_margin = ct["overconfidence_margin"]
    is_overconfident = (raw_score - calibrated_score) > overconfidence_margin
    is_underconfident = (calibrated_score - raw_score) > overconfidence_margin
    confidence_gap = round(abs(raw_score - calibrated_score), 4)
    if confidence_gap <= 0.05:
        quality = "well_calibrated"
    elif confidence_gap <= 0.10:
        quality = "acceptable"
    else:
        quality = "needs_calibration"
    return CalibrationReport(
        model_name=model_name,
        raw_score=round(raw_score, 4),
        calibrated_score=round(calibrated_score, 4),
        threshold=threshold,
        decision=decision,
        is_overconfident=is_overconfident,
        is_underconfident=is_underconfident,
        confidence_gap=confidence_gap,
        calibration_quality=quality,
        details={
            "overconfidence_margin": overconfidence_margin,
            "raw_decision": "duplicate" if raw_score >= threshold else "non_duplicate",
            "decision_changed": (raw_score >= threshold) != (calibrated_score >= threshold),
        },
    )


def _apply_isotonic_scaling(raw_score: float, model_name: str) -> float:
    model_lower = model_name.lower()
    if "classical" in model_lower or "lr" in model_lower or "svm" in model_lower:
        return max(0.0, min(1.0, raw_score * 0.92 + 0.04))
    if "transformer" in model_lower or "bert" in model_lower:
        return max(0.0, min(1.0, raw_score * 0.95 + 0.02))
    if "ensemble" in model_lower:
        return max(0.0, min(1.0, raw_score * 0.97 + 0.01))
    return raw_score
