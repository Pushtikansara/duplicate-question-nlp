"""Standardized exception hierarchy for duplicate question detection.

Every exception includes:
- context: What operation was being performed
- cause: Why the error occurred (technical detail)
- resolution: Suggested next step to resolve the issue
"""

from __future__ import annotations

from typing import Any


class BaseAppError(Exception):
    """Base exception with structured context, cause, and resolution."""

    def __init__(
        self,
        message: str = "",
        *,
        context: str = "",
        cause: str = "",
        resolution: str = "",
    ):
        self.context = context
        self.cause = cause
        self.resolution = resolution
        parts = [message]
        if context:
            parts.append(f"Context: {context}")
        if cause:
            parts.append(f"Cause: {cause}")
        if resolution:
            parts.append(f"Resolution: {resolution}")
        super().__init__(" | ".join(parts))

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": type(self).__name__,
            "message": str(self.args[0]) if self.args else "",
            "context": self.context,
            "cause": self.cause,
            "resolution": self.resolution,
        }


class DuplicateQuestionAppError(BaseAppError):
    """Base exception for all duplicate question detection errors."""


class ConfigurationError(DuplicateQuestionAppError):
    """Raised when configuration loading or resolution fails.

    Common causes:
    - Missing configs/ directory
    - Invalid YAML syntax in config files
    - Missing required keys

    Resolution: Check that configs/{name}.yaml exists and is valid YAML.
    Override paths with DQD_CONFIG_DIR or individual DQD_* env vars.
    """


class ModelNotFoundError(DuplicateQuestionAppError):
    """Raised when a requested model is not found on disk or in registry.

    Common causes:
    - Models have not been trained or downloaded yet
    - Model directory path is misconfigured in configs/paths.yaml

    Resolution: Run training pipeline or download pre-trained weights.
    Check paths in configs/paths.yaml or via DQD_MODELS_DIR env var.
    """


class ModelNotReadyError(DuplicateQuestionAppError):
    """Raised when a model exists but its artifacts are incomplete.

    Common causes:
    - config.json missing
    - model weights (pytorch_model.bin / model.safetensors) missing
    - tokenizer files missing

    Resolution: Re-run training or verify model directory contents.
    Run `dqd doctor` for detailed diagnostics.
    """


class InferenceError(DuplicateQuestionAppError):
    """Raised when model inference fails.

    Common causes:
    - Model not loaded or out of memory
    - Input text is empty or malformed
    - Device mismatch (CPU vs GPU)

    Resolution: Verify model is loaded, check device configuration,
    and ensure input text is non-empty.
    """


class DataError(DuplicateQuestionAppError):
    """Raised when data loading or processing fails.

    Common causes:
    - CSV file missing required columns (question1, question2)
    - File format is invalid or corrupted
    - Dataset path is misconfigured

    Resolution: Verify dataset path and format.
    Check configs/paths.yaml or DQD_DATA_DIR env var.
    """


class DatasetNotFoundError(DataError):
    """Raised when a dataset file is not found.

    Resolution: Verify the dataset exists at the configured path.
    Run `dqd doctor` to check data directory status.
    """


class TrainingError(DuplicateQuestionAppError):
    """Raised when training fails.

    Common causes:
    - Insufficient data or memory
    - Configuration error in configs/training.yaml
    - GPU/CPU device incompatibility

    Resolution: Check training configuration and available resources.
    Review configs/training.yaml.
    """


class CalibrationError(DuplicateQuestionAppError):
    """Raised when probability calibration fails.

    Common causes:
    - Insufficient calibration data
    - sklearn not installed for Platt/Isotonic methods

    Resolution: Ensure sufficient validation data is available.
    Install optional dependencies: pip install .[all]
    """


class EnsembleError(DuplicateQuestionAppError):
    """Raised when ensemble inference fails.

    Resolution: Ensure at least one sub-model is available.
    Run `dqd doctor` for model availability diagnostics.
    """


class RegistryError(DuplicateQuestionAppError):
    """Raised when model registry operations fail.

    Resolution: Verify model directories and HuggingFace cache.
    Run `dqd doctor --models` for detailed model status.
    """


class EvaluationError(DuplicateQuestionAppError):
    """Raised when evaluation metrics computation fails.

    Resolution: Verify that prediction data and ground truth labels
    are available and correctly formatted.
    """


class PreprocessingError(DuplicateQuestionAppError):
    """Raised when text preprocessing fails.

    Resolution: Ensure input text is non-empty and valid UTF-8.
    """


class ArtifactError(DuplicateQuestionAppError):
    """Raised when loading or saving artifacts fails.

    Common causes:
    - Artifact file missing or corrupted
    - Permission denied on output directory

    Resolution: Verify artifact paths and permissions.
    Run `dqd doctor` for filesystem diagnostics.
    """


class LinguistError(DuplicateQuestionAppError):
    """Raised when linguistic analysis fails.

    Resolution: This is typically a recoverable error.
    Linguistic features will be degraded but inference continues.
    """


class ValidationError(DuplicateQuestionAppError):
    """Raised when validation checks fail.

    Provides a list of individual validation failures.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        errors: list[str] | None = None,
        context: str = "",
        cause: str = "",
        resolution: str = "",
    ):
        self.errors = errors or []
        super().__init__(message, context=context, cause=cause, resolution=resolution)

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "errors": self.errors,
        }


class CacheError(DuplicateQuestionAppError):
    """Raised when cache operations fail.

    Resolution: Clear caches via clear_all_caches() or restart.
    This is typically a recoverable error.
    """


class RuntimeDiagnosticsError(DuplicateQuestionAppError):
    """Raised when runtime diagnostics collection fails.

    Resolution: Report issue. This is internal infrastructure.
    """
