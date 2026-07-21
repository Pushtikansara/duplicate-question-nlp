"""QuestionClassifier — determines whether text is a question and classifies its type.

Produces:
  - question_type: wh-what, wh-why, wh-how, wh-when, wh-where, wh-who, wh-which, yes-no, declarative, imperative, exclamatory
  - question_class: definition, comparison, installation, tutorial, troubleshooting, recommendation, opinion, debugging, translation, math, unknown
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistics.intent import detect_intent as _detect_intent

log = get_logger(__name__)

_WH_PATTERNS: dict[str, re.Pattern] = {
    "wh-what": re.compile(r"^\s*what\b", re.IGNORECASE),
    "wh-why": re.compile(r"^\s*why\b", re.IGNORECASE),
    "wh-how": re.compile(r"^\s*how\b", re.IGNORECASE),
    "wh-when": re.compile(r"^\s*when\b", re.IGNORECASE),
    "wh-where": re.compile(r"^\s*where\b", re.IGNORECASE),
    "wh-who": re.compile(r"^\s*who[ms]?\b", re.IGNORECASE),
    "wh-which": re.compile(r"^\s*which\b", re.IGNORECASE),
}

_YES_NO_STARTERS: re.Pattern = re.compile(
    r"^\s*(is|are|was|were|do|does|did|has|have|had|can|could|will|would|shall|should|may|might|must|am)\b",
    re.IGNORECASE,
)

_IMPETIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\s*(please\s+)?(how\s+to|tell\s+me|show\s+me|explain|describe|list|give|find|help)\b", re.IGNORECASE),
    re.compile(r"^\s*what\s+is\s+the\s+(best|way|difference|meaning|purpose)\b", re.IGNORECASE),
]


class QuestionClassifier(ABC):
    @abstractmethod
    def classify(self, text: str) -> tuple[str | None, str | None, float]: ...


class DefaultQuestionClassifier(QuestionClassifier):
    def __init__(self) -> None:
        self._logger = get_logger(f"{__name__}.DefaultQuestionClassifier")

    def classify(self, text: str) -> tuple[str | None, str | None, float]:
        if not text or not text.strip():
            return None, None, 0.0
        normalized = text.strip()
        question_type = self._detect_question_type(normalized)
        question_class = self._detect_question_class(normalized)
        confidence = self._estimate_confidence(question_type, question_class, normalized)
        return question_type, question_class, confidence

    def _detect_question_type(self, text: str) -> str | None:
        if "?" in text:
            for qtype, pattern in _WH_PATTERNS.items():
                if pattern.search(text):
                    return qtype
            if _YES_NO_STARTERS.search(text):
                return "yes-no"
            return "question-other"
        if text.endswith("!"):
            return "exclamatory"
        for pat in _IMPETIVE_PATTERNS:
            if pat.search(text):
                return "imperative"
        return "declarative"

    def _detect_question_class(self, text: str) -> str | None:
        try:
            result = _detect_intent(text)
            if result.primary_intent.value == "unknown":
                return None
            return result.primary_intent.value
        except Exception:
            return None

    def _estimate_confidence(self, question_type: str | None, question_class: str | None, text: str) -> float:
        score = 0.0
        if question_type and question_type != "declarative":
            score += 0.4
        if "?" in text:
            score += 0.3
        if question_class:
            score += 0.3
        return min(1.0, score)
