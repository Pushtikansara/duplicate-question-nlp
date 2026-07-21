"""Metadata Extractor — sixth stage of the Cognitive Perception Pipeline.

Extracts surface-level metadata from normalized text.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._perception.cognitive_representation import Metadata
from duplicate_question_app._perception.config import MetadataExtractorConfig
from duplicate_question_app._perception.exceptions import MetadataExtractionError

log = get_logger(__name__)

_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_CODE_PATTERN = re.compile(r"(```|`[^`]+`)")


class MetadataExtractor(ABC):
    @abstractmethod
    def extract(self, text: str, normalized: str) -> Metadata: ...


class DefaultMetadataExtractor(MetadataExtractor):
    _QUESTION_WORDS: set[str] = {"what", "why", "how", "when", "where", "who", "which", "whose", "whom"}

    def __init__(self, config: MetadataExtractorConfig | None = None):
        self._config = config or MetadataExtractorConfig()
        self._logger = get_logger(f"{__name__}.DefaultMetadataExtractor")

    def extract(self, text: str, normalized: str) -> Metadata:
        if not normalized:
            return Metadata()
        try:
            words = normalized.split()
            word_count = len(words)
            char_count = len(normalized)
            sentence_count = max(1, len(re.findall(r"[.!?]+", normalized)))
            has_qmark = "?" in normalized
            has_excl = "!" in normalized
            has_code = bool(_CODE_PATTERN.search(text))
            has_url = bool(_URL_PATTERN.search(text))
            has_email = bool(_EMAIL_PATTERN.search(text))
            question_type = self._detect_question_type(words) if self._config.detect_question_type else None

            return Metadata(
                length=char_count,
                char_count=char_count,
                word_count=word_count,
                sentence_count=sentence_count,
                question_type=question_type,
                has_question_mark=has_qmark,
                has_exclamation=has_excl,
                has_code=has_code,
                has_url=has_url,
                has_email=has_email,
            )
        except Exception as exc:
            raise MetadataExtractionError(
                str(exc),
                context="metadata_extraction",
                cause="Failed to extract metadata from text",
                resolution="Ensure text is valid and non-empty",
            ) from exc

    def _detect_question_type(self, words: list[str]) -> str | None:
        if not words:
            return None
        first_word = words[0].lower().strip("?")
        if first_word in self._QUESTION_WORDS:
            return f"wh-{first_word}"
        if first_word in {
            "is",
            "are",
            "was",
            "were",
            "do",
            "does",
            "did",
            "has",
            "have",
            "had",
            "can",
            "could",
            "will",
            "would",
            "should",
            "may",
            "might",
        }:
            return "yes-no"
        return "declarative"
