"""Text Normalizer — first stage of the Cognitive Perception Pipeline.

Wraps the existing `normalize_question` from `_preprocessing.text`
to maintain backward compatibility while providing an injectable interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._perception.cognitive_representation import ValidationReport
from duplicate_question_app._perception.config import NormalizerConfig
from duplicate_question_app._perception.exceptions import NormalizationError
from duplicate_question_app._preprocessing.text import normalize_question

log = get_logger(__name__)


class TextNormalizer(ABC):
    @abstractmethod
    def normalize(self, text: str) -> tuple[str, ValidationReport]: ...


class DefaultTextNormalizer(TextNormalizer):
    def __init__(self, config: NormalizerConfig | None = None):
        self._config = config or NormalizerConfig()
        self._logger = get_logger(f"{__name__}.DefaultTextNormalizer")

    def normalize(self, text: str) -> tuple[str, ValidationReport]:
        report = ValidationReport()
        if not isinstance(text, str):
            report.errors.append("Input must be a string")
            raise NormalizationError("Input must be a string", context="normalize")
        raw = text.strip()
        if not raw:
            report.errors.append("Empty text after stripping")
            report.valid = False
            return "", report
        try:
            normalized = normalize_question(
                text,
                expand_abbrevs=self._config.expand_abbreviations,
                fix_typos=self._config.fix_typos,
            )
            self._logger.debug("Normalized text (%d chars -> %d chars)", len(raw), len(normalized))
            return normalized, report
        except Exception as exc:
            report.errors.append(str(exc))
            raise NormalizationError(
                str(exc),
                context="normalize",
                cause="normalize_question raised an exception",
                resolution="Check input text encoding and content",
            ) from exc


class NoOpTextNormalizer(TextNormalizer):
    def normalize(self, text: str) -> tuple[str, ValidationReport]:
        return text.strip(), ValidationReport()
