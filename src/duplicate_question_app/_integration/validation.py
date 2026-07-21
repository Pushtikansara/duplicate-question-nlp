from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_pipeline_context(context: Any) -> ValidationResult:
    errors = []
    warnings = []
    if context is None:
        errors.append("Pipeline context is None")
        return ValidationResult(valid=False, errors=errors)
    if not hasattr(context, "question_a") or not context.question_a:
        errors.append("question_a is required")
    if not hasattr(context, "question_b") or not context.question_b:
        errors.append("question_b is required")
    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_prediction_unchanged(before: dict[str, Any], after: dict[str, Any]) -> ValidationResult:
    errors = []
    warnings = []
    for key in ("predicted_label", "prediction", "prob_duplicate", "prob_non_duplicate"):
        if key in before and key in after and before[key] != after[key]:
            errors.append(f"Prediction changed for key {key}: {before[key]} -> {after[key]}")
    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
