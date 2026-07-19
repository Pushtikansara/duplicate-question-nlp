"""Standardized exception hierarchy for duplicate question detection."""

from __future__ import annotations


class DuplicateQuestionAppError(Exception):
    """Base exception for all duplicate question detection errors."""


class ConfigurationError(DuplicateQuestionAppError):
    """Raised when configuration loading or resolution fails."""


class ModelNotFoundError(DuplicateQuestionAppError):
    """Raised when a requested model is not found on disk or in registry."""


class ModelNotReadyError(DuplicateQuestionAppError):
    """Raised when a model exists but its artifacts are incomplete."""


class InferenceError(DuplicateQuestionAppError):
    """Raised when model inference fails."""


class DataError(DuplicateQuestionAppError):
    """Raised when data loading or processing fails."""


class DatasetNotFoundError(DataError):
    """Raised when a dataset file is not found."""


class TrainingError(DuplicateQuestionAppError):
    """Raised when training fails."""


class CalibrationError(DuplicateQuestionAppError):
    """Raised when probability calibration fails."""


class EnsembleError(DuplicateQuestionAppError):
    """Raised when ensemble inference fails."""


class RegistryError(DuplicateQuestionAppError):
    """Raised when model registry operations fail."""


class EvaluationError(DuplicateQuestionAppError):
    """Raised when evaluation metrics computation fails."""


class PreprocessingError(DuplicateQuestionAppError):
    """Raised when text preprocessing fails."""


class ArtifactError(DuplicateQuestionAppError):
    """Raised when loading or saving artifacts fails."""


class LinguistError(DuplicateQuestionAppError):
    """Raised when linguistic analysis fails."""
