"""Structural Analyzer — fourth stage of the Cognitive Perception Pipeline.

Detects sentence boundaries, paragraph structure, and section breaks.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._perception.cognitive_representation import Sentence, Token
from duplicate_question_app._perception.config import StructuralAnalyzerConfig
from duplicate_question_app._perception.exceptions import StructuralAnalysisError

log = get_logger(__name__)

_SENTENCE_SPLITTER = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
_SECTION_PATTERN = re.compile(r"^#{1,6}\s+.*$", re.MULTILINE)
_PARAGRAPH_SPLITTER = re.compile(r"\n\s*\n")


class StructuralAnalyzer(ABC):
    @abstractmethod
    def analyze(self, text: str, tokens: list[Token]) -> list[Sentence]: ...


class DefaultStructuralAnalyzer(StructuralAnalyzer):
    def __init__(self, config: StructuralAnalyzerConfig | None = None):
        self._config = config or StructuralAnalyzerConfig()
        self._logger = get_logger(f"{__name__}.DefaultStructuralAnalyzer")

    def analyze(self, text: str, tokens: list[Token]) -> list[Sentence]:
        if not text:
            return []
        try:
            sentences = self._split_sentences(text, tokens)
            if self._config.max_sentences and len(sentences) > self._config.max_sentences:
                sentences = sentences[: self._config.max_sentences]
            self._logger.debug("Detected %d sentences", len(sentences))
            return sentences
        except Exception as exc:
            raise StructuralAnalysisError(
                str(exc),
                context="structural_analysis",
                cause="Sentence splitting failed",
                resolution="Ensure text is valid UTF-8 and non-empty",
            ) from exc

    def _split_sentences(self, text: str, tokens: list[Token]) -> list[Sentence]:
        raw_sentences = _SENTENCE_SPLITTER.split(text.strip())
        if not raw_sentences or (len(raw_sentences) == 1 and not raw_sentences[0]):
            raw_sentences = [text.strip()]
        sentences: list[Sentence] = []
        char_offset = 0
        for raw in raw_sentences:
            if not raw.strip():
                continue
            start = text.find(raw.strip(), char_offset)
            if start == -1:
                start = char_offset
            end = start + len(raw.strip())
            char_offset = end
            sent_tokens = [t for t in tokens if t.start >= start and t.end <= end]
            sentence = Sentence(text=raw.strip(), start=start, end=end, tokens=sent_tokens)
            sentences.append(sentence)
        return sentences
