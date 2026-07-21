"""Language Detector — second stage of the Cognitive Perception Pipeline.

Uses heuristic character-level analysis to detect language without external
dependencies. Supports English by default; extensible via plugins.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._perception.config import LanguageDetectorConfig

log = get_logger(__name__)

_ENGLISH_CHAR_RANGE = re.compile(r"^[a-zA-Z0-9\s.,!?;:'\"()\-]+$")

_LANGUAGE_HEURISTICS: dict[str, list[tuple[re.Pattern, float]]] = {
    "en": [
        (re.compile(r"\bthe\b", re.IGNORECASE), 1.0),
        (re.compile(r"\bis\b", re.IGNORECASE), 0.8),
        (re.compile(r"\bare\b", re.IGNORECASE), 0.7),
        (re.compile(r"\band\b", re.IGNORECASE), 0.6),
        (re.compile(r"\bthis\b", re.IGNORECASE), 0.6),
        (re.compile(r"\bthat\b", re.IGNORECASE), 0.5),
        (re.compile(r"\bwith\b", re.IGNORECASE), 0.5),
        (re.compile(r"\bfor\b", re.IGNORECASE), 0.5),
        (re.compile(r"\byou\b", re.IGNORECASE), 0.4),
        (re.compile(r"\bto\b", re.IGNORECASE), 0.4),
        (re.compile(r"\bhow\b", re.IGNORECASE), 0.4),
        (re.compile(r"\bwhat\b", re.IGNORECASE), 0.4),
        (re.compile(r"\bwhy\b", re.IGNORECASE), 0.4),
        (re.compile(r"\bnot\b", re.IGNORECASE), 0.3),
        (re.compile(r"\bcan\b", re.IGNORECASE), 0.3),
        (re.compile(r"\bdoes\b", re.IGNORECASE), 0.3),
        (re.compile(r"\bhave\b", re.IGNORECASE), 0.3),
        (re.compile(r"\bwas\b", re.IGNORECASE), 0.3),
        (re.compile(r"\bhas\b", re.IGNORECASE), 0.2),
        (re.compile(r"\bhad\b", re.IGNORECASE), 0.2),
    ],
}


class LanguageDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> tuple[str, float]: ...


class HeuristicLanguageDetector(LanguageDetector):
    def __init__(self, config: LanguageDetectorConfig | None = None):
        self._config = config or LanguageDetectorConfig()
        self._logger = get_logger(f"{__name__}.HeuristicLanguageDetector")

    def detect(self, text: str) -> tuple[str, float]:
        if not text or not text.strip():
            return self._config.fallback_language, 0.0
        normalized = text.lower().strip()
        scores: dict[str, float] = {}
        for lang, patterns in _LANGUAGE_HEURISTICS.items():
            score = 0.0
            for pattern, weight in patterns:
                matches = pattern.findall(normalized)
                score += len(matches) * weight
            if score > 0:
                scores[lang] = score
        if not scores:
            if _ENGLISH_CHAR_RANGE.match(normalized):
                return "en", self._config.confidence_threshold
            return self._config.fallback_language, 0.0
        best_lang = max(scores, key=scores.get)
        max_score = scores[best_lang]
        total = sum(scores.values())
        confidence = max_score / total if total > 0 else 0.0
        confidence = min(1.0, confidence)
        if confidence < self._config.confidence_threshold:
            self._logger.debug(
                "Low confidence (%f) for language %s, falling back to %s",
                confidence,
                best_lang,
                self._config.fallback_language,
            )
            return self._config.fallback_language, confidence
        self._logger.debug("Detected language: %s (confidence=%.2f)", best_lang, confidence)
        return best_lang, confidence


class NoOpLanguageDetector(LanguageDetector):
    def detect(self, text: str) -> tuple[str, float]:
        return "en", 1.0
