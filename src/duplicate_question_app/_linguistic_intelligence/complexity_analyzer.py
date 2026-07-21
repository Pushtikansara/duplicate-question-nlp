"""ComplexityAnalyzer — measures linguistic complexity and readability.

Computes:
  - Vocabulary complexity (type-token ratio, long word ratio, polysyllable count)
  - Syntactic complexity (sentence length, clause density)
  - Readability (Flesch Reading Ease, Flesch-Kincaid Grade, Coleman-Liau Index)
  - Overall complexity score
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import (
    ComplexityScore,
    ReadabilityScore,
    SentenceStatistics,
    TokenStatistics,
)

log = get_logger(__name__)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD_FIND = re.compile(r"\b\w+(?:[-']\w+)*\b")
_POLYSYLLABLE = re.compile(r"[aeiouy]{2,}", re.IGNORECASE)
_LONG_WORD = re.compile(r"\b\w{7,}\b")
_STOPWORDS: set[str] = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "by",
    "with",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "can",
    "could",
    "shall",
    "should",
    "may",
    "might",
    "must",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "his",
    "its",
    "our",
    "their",
    "this",
    "that",
    "these",
    "those",
    "not",
    "no",
    "nor",
    "so",
    "very",
    "just",
    "if",
    "then",
    "else",
    "when",
    "where",
    "why",
    "how",
    "what",
    "which",
    "who",
    "whom",
    "whose",
    "about",
    "into",
    "over",
    "after",
    "before",
    "between",
    "under",
    "above",
    "below",
    "out",
    "off",
    "up",
    "down",
}


class ComplexityAnalyzer(ABC):
    @abstractmethod
    def analyze(self, text: str) -> tuple[TokenStatistics, SentenceStatistics, ComplexityScore, ReadabilityScore]: ...


class DefaultComplexityAnalyzer(ComplexityAnalyzer):
    def __init__(self) -> None:
        self._logger = get_logger(f"{__name__}.DefaultComplexityAnalyzer")

    def analyze(self, text: str) -> tuple[TokenStatistics, SentenceStatistics, ComplexityScore, ReadabilityScore]:
        if not text or not text.strip():
            return TokenStatistics(), SentenceStatistics(), ComplexityScore(), ReadabilityScore()
        words = _WORD_FIND.findall(text.lower())
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text.strip()) if s.strip()]
        if not sentences:
            sentences = [text.strip()]
        token_stats = self._compute_token_stats(words)
        sent_stats = self._compute_sentence_stats(sentences)
        complexity = self._compute_complexity(words, sentences)
        readability = self._compute_readability(words, sentences)
        return token_stats, sent_stats, complexity, readability

    def _compute_token_stats(self, words: list[str]) -> TokenStatistics:
        total = len(words)
        unique = len(set(words))
        stopword_count = sum(1 for w in words if w in _STOPWORDS)
        punct = sum(1 for w in words if not w.isalnum())
        numeric = sum(1 for w in words if w.isdigit())
        avg_len = sum(len(w) for w in words) / total if total > 0 else 0.0
        ttr = unique / total if total > 0 else 0.0
        return TokenStatistics(
            total=total,
            unique=unique,
            stopword_count=stopword_count,
            punctuation_count=punct,
            numeric_count=numeric,
            avg_token_length=avg_len,
            type_token_ratio=ttr,
        )

    def _compute_sentence_stats(self, sentences: list[str]) -> SentenceStatistics:
        sent_lens = [len(s.split()) for s in sentences]
        total = len(sentences)
        avg = sum(sent_lens) / total if total > 0 else 0.0
        questions = sum(1 for s in sentences if "?" in s)
        exclamations = sum(1 for s in sentences if "!" in s and "?" not in s)
        return SentenceStatistics(
            total=total,
            avg_sentence_length=avg,
            min_sentence_length=min(sent_lens) if sent_lens else 0,
            max_sentence_length=max(sent_lens) if sent_lens else 0,
            question_sentences=questions,
            exclamatory_sentences=exclamations,
        )

    def _compute_complexity(self, words: list[str], sentences: list[str]) -> ComplexityScore:
        total_words = len(words)
        if total_words == 0 or len(sentences) == 0:
            return ComplexityScore()
        long_words = sum(1 for w in words if len(w) >= 7)
        polysyllables = sum(1 for w in words if _count_syllables(w) >= 3)
        avg_sent_words = total_words / len(sentences)
        vocab_complexity = long_words / total_words if total_words > 0 else 0.0
        sent_complexity = min(1.0, avg_sent_words / 40.0)
        readability = 1.0 - min(1.0, vocab_complexity * 2.0)
        overall = vocab_complexity * 0.4 + sent_complexity * 0.4 + readability * 0.2
        flesch = _flesch_reading_ease(total_words, len(sentences), polysyllables)
        syntax = min(1.0, avg_sent_words / 30.0)
        return ComplexityScore(
            overall=overall,
            vocabulary_complexity=vocab_complexity,
            syntactic_complexity=syntax,
            sentence_complexity=sent_complexity,
            readability=readability,
            flesch_reading_ease=max(0.0, min(100.0, flesch)),
            avg_sentence_words=avg_sent_words,
            long_word_ratio=vocab_complexity,
            polysyllable_count=polysyllables,
        )

    def _compute_readability(self, words: list[str], sentences: list[str]) -> ReadabilityScore:
        total_words = len(words)
        total_sentences = len(sentences)
        if total_words == 0 or total_sentences == 0:
            return ReadabilityScore()
        total_chars = sum(len(w) for w in words)
        polysyllables = sum(1 for w in words if _count_syllables(w) >= 3)
        flesch = _flesch_reading_ease(total_words, total_sentences, polysyllables)
        kincaid = _flesch_kincaid_grade(total_words, total_sentences, polysyllables)
        coleman = _coleman_liau(total_chars, total_words, total_sentences)
        avg_score = (flesch + (100.0 - kincaid * 10.0) + (100.0 - coleman * 5.0)) / 3.0
        avg_score = max(0.0, min(100.0, avg_score))
        return ReadabilityScore(
            flesch_reading_ease=max(0.0, min(100.0, flesch)),
            flesch_kincaid_grade=max(0.0, kincaid),
            coleman_liau_index=max(0.0, coleman),
            avg=avg_score,
        )


def _count_syllables(word: str) -> int:
    word = word.lower().strip(".,!?;:")
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _flesch_reading_ease(words: int, sentences: int, polysyllables: int) -> float:
    if words == 0 or sentences == 0:
        return 0.0
    return 206.835 - 1.015 * (words / sentences) - 84.6 * (polysyllables / words)


def _flesch_kincaid_grade(words: int, sentences: int, polysyllables: int) -> float:
    if words == 0 or sentences == 0:
        return 0.0
    return 0.39 * (words / sentences) + 11.8 * (polysyllables / words) - 15.59


def _coleman_liau(chars: int, words: int, sentences: int) -> float:
    if words == 0 or sentences == 0:
        return 0.0
    letter_count = chars / words * 100.0
    s = sentences / words * 100.0
    return 0.0588 * letter_count - 0.296 * s - 15.8
