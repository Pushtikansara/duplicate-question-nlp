"""Validation framework for configurations, datasets, paths, artifacts, and user inputs.

Provides early-failure validation with clear diagnostic messages.
All validation functions return a ValidationResult with errors list.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from duplicate_question_app._config.exceptions import ValidationError


class ValidationResult:
    """Result of a validation check.

    Attributes:
        passed: True if all checks passed.
        errors: List of human-readable error messages.
        warnings: List of non-blocking warnings.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def merge(self, other: ValidationResult) -> ValidationResult:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self

    def raise_if_failed(self, context: str = "") -> None:
        if not self.passed:
            raise ValidationError(
                f"Validation failed ({len(self.errors)} error(s))",
                errors=self.errors,
                context=context,
                resolution="Review the errors above and fix the reported issues.",
            )

    def summary(self) -> str:
        parts: list[str] = []
        if self.passed:
            parts.append("Validation passed.")
        else:
            parts.append(f"Validation failed: {len(self.errors)} error(s)")
            for i, err in enumerate(self.errors, 1):
                parts.append(f"  {i}. {err}")
        if self.warnings:
            parts.append(f"Warnings: {len(self.warnings)}")
            for w in self.warnings:
                parts.append(f"  - {w}")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------


def validate_config(config: dict[str, Any], required_keys: list[str], section: str) -> ValidationResult:
    """Validate that a config section has required keys."""
    result = ValidationResult()
    for key in required_keys:
        if key not in config:
            result.errors.append(f"Config '{section}' missing required key: '{key}'")
    return result


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------


def validate_path_exists(path: Path, label: str) -> ValidationResult:
    """Validate that a filesystem path exists."""
    result = ValidationResult()
    if not path.exists():
        result.errors.append(f"{label}: path does not exist: {path}")
    return result


def validate_path_is_dir(path: Path, label: str) -> ValidationResult:
    """Validate that a path exists and is a directory."""
    result = validate_path_exists(path, label)
    if path.exists() and not path.is_dir():
        result.errors.append(f"{label}: path is not a directory: {path}")
    return result


def validate_path_is_file(path: Path, label: str) -> ValidationResult:
    """Validate that a path exists and is a file."""
    result = validate_path_exists(path, label)
    if path.exists() and not path.is_file():
        result.errors.append(f"{label}: path is not a file: {path}")
    return result


# ---------------------------------------------------------------------------
# AppPaths validation
# ---------------------------------------------------------------------------


def validate_app_paths(paths: Any) -> ValidationResult:
    """Validate that all required application paths exist."""
    result = ValidationResult()

    if hasattr(paths, "models_dir"):
        result.merge(validate_path_is_dir(paths.models_dir, "Models directory"))
    if hasattr(paths, "data_dir"):
        result.merge(validate_path_is_dir(paths.data_dir, "Data directory"))
    if hasattr(paths, "results_dir"):
        result.merge(validate_path_is_dir(paths.results_dir, "Results directory"))
    if hasattr(paths, "project_root"):
        result.merge(validate_path_is_dir(paths.project_root, "Project root"))

    return result


# ---------------------------------------------------------------------------
# Model directory validation
# ---------------------------------------------------------------------------


def validate_model_directory(model_dir: Path, label: str) -> ValidationResult:
    """Validate a model directory has the required artifacts.

    Checks for:
    - Directory existence
    - config.json
    - model weights (pytorch_model.bin or model.safetensors)
    - tokenizer files
    """
    result = ValidationResult()

    if not model_dir.exists():
        result.errors.append(f"{label}: model directory does not exist: {model_dir}")
        return result

    if not (model_dir / "config.json").exists():
        result.errors.append(f"{label}: config.json is missing")

    has_weights = (model_dir / "pytorch_model.bin").exists() or (model_dir / "model.safetensors").exists()
    if not has_weights:
        result.errors.append(f"{label}: model weights (pytorch_model.bin / model.safetensors) are missing")

    has_tokenizer = (model_dir / "tokenizer.json").exists() or (model_dir / "tokenizer_config.json").exists()
    if not has_tokenizer:
        result.warnings.append(f"{label}: no tokenizer files found (inference may fail)")

    return result


# ---------------------------------------------------------------------------
# Dataset validation
# ---------------------------------------------------------------------------


def validate_dataset_columns(columns: set[str], required: set[str], source: str) -> ValidationResult:
    """Validate that a dataset has required columns."""
    result = ValidationResult()
    missing = required - columns
    if missing:
        result.errors.append(f"{source}: missing required columns: {', '.join(sorted(missing))}")
    return result


# ---------------------------------------------------------------------------
# User input validation
# ---------------------------------------------------------------------------


def validate_non_empty_text(text: str | None, field_name: str) -> ValidationResult:
    """Validate that a text input is non-empty."""
    result = ValidationResult()
    if not text or not text.strip():
        result.errors.append(f"{field_name}: text input is empty")
    return result


def validate_threshold(threshold: float) -> ValidationResult:
    """Validate a decision threshold is in range [0.0, 1.0]."""
    result = ValidationResult()
    if not 0.0 <= threshold <= 1.0:
        result.errors.append(f"Threshold must be between 0.0 and 1.0, got {threshold}")
    return result


def validate_model_name(model_name: str, available: list[str]) -> ValidationResult:
    """Validate that a model name is in the available model list."""
    result = ValidationResult()
    if model_name not in available:
        result.errors.append(f"Unknown model '{model_name}'. Available: {', '.join(available)}")
    return result


__all__ = [
    "ValidationResult",
    "validate_config",
    "validate_path_exists",
    "validate_path_is_dir",
    "validate_path_is_file",
    "validate_app_paths",
    "validate_model_directory",
    "validate_dataset_columns",
    "validate_non_empty_text",
    "validate_threshold",
    "validate_model_name",
]
