"""Validator — validates input text and the assembled CognitiveRepresentation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._perception.cognitive_representation import CognitiveRepresentation, ValidationReport
from duplicate_question_app._perception.config import ValidatorConfig
from duplicate_question_app._perception.exceptions import ValidationError

log = get_logger(__name__)


class TextValidator(ABC):
    @abstractmethod
    def validate_text(self, text: str) -> ValidationReport: ...

    @abstractmethod
    def validate_representation(self, representation: CognitiveRepresentation) -> ValidationReport: ...


class DefaultValidator(TextValidator):
    def __init__(self, config: ValidatorConfig | None = None):
        self._config = config or ValidatorConfig()
        self._logger = get_logger(f"{__name__}.DefaultValidator")

    def validate_text(self, text: str) -> ValidationReport:
        report = ValidationReport()
        if not isinstance(text, str):
            report.valid = False
            report.errors.append("Input must be a string")
            return report
        stripped = text.strip()
        if self._config.require_non_empty and not stripped:
            report.valid = False
            report.errors.append("Text must not be empty")
        if len(stripped) < self._config.min_text_length:
            report.valid = False
            report.errors.append(f"Text length ({len(stripped)}) is below minimum ({self._config.min_text_length})")
        if len(stripped) > self._config.max_text_length:
            report.valid = False
            report.errors.append(f"Text length ({len(stripped)}) exceeds maximum ({self._config.max_text_length})")
        if not report.valid:
            raise ValidationError(
                "Text validation failed",
                context="validate_text",
                cause="; ".join(report.errors),
                resolution="Ensure text is non-empty and within length limits",
            )
        return report

    def validate_representation(self, representation: CognitiveRepresentation) -> ValidationReport:
        report = ValidationReport()
        if not representation.raw_text:
            report.valid = False
            report.errors.append("Raw text must not be empty")
        if not representation.normalized_text:
            report.warnings.append("Normalized text is empty")
        if not representation.language:
            report.warnings.append("Language is not set")
        report.valid = len(report.errors) == 0
        return report
