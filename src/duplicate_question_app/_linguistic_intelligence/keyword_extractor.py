"""KeywordExtractor — extracts and scores important keywords from text.

Uses TF-style frequency scoring with length and position bonuses.
Wraps the existing lexical engine for noun/verb/entity detection.
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from collections import Counter

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import Keyword, LexicalFeatures
from duplicate_question_app._linguistics.lexical import extract_tokens as _extract_tokens

log = get_logger(__name__)

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

_WORD_FIND = re.compile(r"\b\w+(?:[-']\w+)*\b")


class KeywordExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> tuple[list[Keyword], dict[str, float], LexicalFeatures]: ...


class DefaultKeywordExtractor(KeywordExtractor):
    def __init__(self, top_n: int = 20) -> None:
        self._top_n = top_n
        self._logger = get_logger(f"{__name__}.DefaultKeywordExtractor")

    def extract(self, text: str) -> tuple[list[Keyword], dict[str, float], LexicalFeatures]:
        if not text or not text.strip():
            return [], {}, LexicalFeatures()
        words = _WORD_FIND.findall(text.lower())
        if not words:
            return [], {}, LexicalFeatures()
        freq = Counter(words)
        total = len(words)
        lexical = self._compute_lexical(text)
        keywords = self._score_keywords(freq, total, text, lexical)
        keyword_scores = {k.word: k.score for k in keywords}
        return keywords, keyword_scores, lexical

    def _compute_lexical(self, text: str) -> LexicalFeatures:
        try:
            analysis = _extract_tokens(text)
        except Exception:
            return LexicalFeatures()
        total = len(analysis.all_tokens)
        content = len(analysis.nouns | analysis.verbs | analysis.entities)
        function_names = {w for w in analysis.all_tokens if w in _STOPWORDS}
        density = content / total if total > 0 else 0.0
        diversity = len(analysis.all_tokens) / total if total > 0 else 0.0
        return LexicalFeatures(
            lexical_density=density,
            lexical_diversity=diversity,
            noun_count=len(analysis.nouns),
            verb_count=len(analysis.verbs),
            content_word_count=content,
            function_word_count=len(function_names),
            unique_nouns=sorted(analysis.nouns),
            unique_verbs=sorted(analysis.verbs),
        )

    def _score_keywords(self, freq: Counter, total: int, text: str, lexical: LexicalFeatures) -> list[Keyword]:
        noun_set = set(lexical.unique_nouns)
        verb_set = set(lexical.unique_verbs)
        entity_set: set[str] = set()
        scored: list[Keyword] = []
        for word, count in freq.most_common(self._top_n * 2):
            if word in _STOPWORDS and len(word) <= 3:
                continue
            tf = count / total
            length_bonus = min(0.3, math.log(len(word) + 1) * 0.1)
            position_bonus = 0.0
            idx = text.lower().find(word)
            if idx < 20:
                position_bonus = 0.2
            elif idx < 50:
                position_bonus = 0.1
            is_noun = word in noun_set
            is_verb = word in verb_set
            is_entity = word in entity_set
            pos_bonus = 0.3 if is_noun else (0.2 if is_verb else 0.0)
            score = tf + length_bonus + position_bonus + pos_bonus
            kw = Keyword(
                word=word,
                score=score,
                frequency=count,
                tfidf_score=tf,
                is_noun=is_noun,
                is_verb=is_verb,
                is_entity=is_entity,
            )
            scored.append(kw)
        scored.sort(key=lambda k: k.score, reverse=True)
        scored = scored[: self._top_n]
        self._normalize_scores(scored)
        return scored

    @staticmethod
    def _normalize_scores(keywords: list[Keyword]) -> None:
        if not keywords:
            return
        max_score = max(k.score for k in keywords)
        if max_score > 0:
            for kw in keywords:
                kw.score = kw.score / max_score
