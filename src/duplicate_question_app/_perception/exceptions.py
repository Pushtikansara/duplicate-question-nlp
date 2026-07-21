"""Perception engine exception hierarchy."""

from __future__ import annotations

from duplicate_question_app._config.exceptions import BaseAppError


class PerceptionError(BaseAppError):
    """Base for all perception engine errors."""


class NormalizationError(PerceptionError):
    """Raised when text normalization fails."""


class LanguageDetectionError(PerceptionError):
    """Raised when language detection fails."""


class TokenizationError(PerceptionError):
    """Raised when tokenization fails."""


class StructuralAnalysisError(PerceptionError):
    """Raised when structural analysis fails."""


class LinguisticAnalysisError(PerceptionError):
    """Raised when linguistic analysis fails."""


class MetadataExtractionError(PerceptionError):
    """Raised when metadata extraction fails."""


class ValidationError(PerceptionError):
    """Raised when validation checks fail."""


class PluginLoadError(PerceptionError):
    """Raised when a plugin cannot be loaded."""


class PipelineError(PerceptionError):
    """Raised when the perception pipeline encounters an error."""
