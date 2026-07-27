from __future__ import annotations

import re
import statistics

_RE_ABBREVIATION = re.compile(r"\b[A-Z]{2,}(?:\d*)\b")
_RE_NUMBER = re.compile(r"\b\d+(?:[.,]\d+)*\b")
_RE_SPECIAL = re.compile(r"[^a-zA-Z0-9\s]")
_RE_MIXED_CASE = re.compile(r"\b[A-Z][a-z]+[A-Z][a-z]+\b")
_RE_PRONOUN = re.compile(r"\b(it|they|them|this|that|these|those|something|someone|somebody)\b", re.IGNORECASE)
_RE_MULTI_SPACE = re.compile(r"\s+")

_COMMON_WORDS: frozenset = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
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
        "need",
        "dare",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "because",
        "also",
        "if",
        "else",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "i",
        "me",
        "my",
        "we",
        "us",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "it",
        "its",
        "they",
        "them",
        "their",
        "or",
        "and",
        "but",
        "about",
        "up",
        "down",
    }
)

_AMBIGUOUS_WORDS: frozenset = frozenset(
    {
        "it",
        "this",
        "that",
        "thing",
        "stuff",
        "something",
        "anything",
        "someone",
        "somebody",
        "somewhere",
        "somehow",
        "do",
        "does",
        "make",
        "get",
        "put",
        "set",
        "take",
        "give",
        "go",
        "come",
        "work",
        "run",
        "turn",
        "use",
        "handle",
        "deal",
        "fix",
    }
)


def count_syllables(word: str) -> int:
    word = word.lower().strip()
    if not word:
        return 0
    vowel_run = 0
    count = 0
    for ch in word:
        if ch in "aeiouy":
            if not vowel_run:
                count += 1
            vowel_run = 1
        else:
            vowel_run = 0
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def flesch_reading_ease(text: str) -> float:
    if not text or not text.strip():
        return 100.0
    words = _RE_MULTI_SPACE.split(text.strip())
    sentences = len(re.findall(r"[.!?]+", text)) or 1
    syllables = sum(count_syllables(w) for w in words)
    return max(0.0, min(100.0, 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / len(words))))


def lexical_complexity(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    avg_len = statistics.mean(len(t) for t in tokens) if len(tokens) > 1 else (len(tokens[0]) if tokens else 0)
    num_long = sum(1 for t in tokens if len(t) > 8)
    return min(1.0, (avg_len / 15) * 0.5 + (num_long / max(len(tokens), 1)) * 0.5)


def syntactic_complexity(tokens: list[str], sentences: int) -> float:
    if not tokens or sentences == 0:
        return 0.0
    avg_sentence_len = len(tokens) / max(sentences, 1)
    if avg_sentence_len <= 5:
        return 0.0
    if avg_sentence_len <= 10:
        return 0.2
    if avg_sentence_len <= 15:
        return 0.4
    if avg_sentence_len <= 20:
        return 0.6
    if avg_sentence_len <= 30:
        return 0.8
    return 1.0


def semantic_complexity(tokens: list[str], language: str = "en") -> float:
    if not tokens:
        return 0.0
    uncommon = sum(1 for t in tokens if t.lower() not in _COMMON_WORDS)
    ratio = uncommon / max(len(tokens), 1)
    return min(1.0, ratio)


def entity_complexity(entity_count: int, total_words: int) -> float:
    if total_words == 0:
        return 0.0
    density = entity_count / max(total_words, 1)
    if density <= 0.1:
        return 0.0
    if density <= 0.2:
        return 0.2
    if density <= 0.35:
        return 0.5
    if density <= 0.5:
        return 0.7
    return 1.0


def ambiguity_score(tokens: list[str], text: str, language: str = "en") -> float:
    if not tokens or not text:
        return 0.0
    score = 0.0
    pronoun_matches = list(_RE_PRONOUN.finditer(text.lower()))
    if pronoun_matches:
        score += min(0.3, len(pronoun_matches) * 0.1)
    ambiguous_words = sum(1 for t in tokens if t.lower() in _AMBIGUOUS_WORDS)
    if ambiguous_words:
        score += min(0.2, ambiguous_words * 0.05)
    if len(tokens) <= 2:
        score += 0.15
    if len(tokens) >= 20:
        score += 0.1
    mixed_case = _RE_MIXED_CASE.findall(text)
    if mixed_case:
        score += min(0.1, len(mixed_case) * 0.05)
    return min(1.0, score)


def readability_complexity(fre: float) -> float:
    if fre >= 90:
        return 0.0
    if fre >= 70:
        return 0.2
    if fre >= 50:
        return 0.4
    if fre >= 30:
        return 0.6
    if fre >= 10:
        return 0.8
    return 1.0


def rare_token_density(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    rare = sum(1 for t in tokens if t.lower() not in _COMMON_WORDS and len(t) > 6)
    return min(1.0, rare / max(len(tokens), 1))


def entity_density(entity_count: int, total_words: int) -> float:
    if total_words == 0:
        return 0.0
    return min(1.0, entity_count / max(total_words, 1))


def abbreviation_density(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    abbrevs = sum(1 for t in tokens if _RE_ABBREVIATION.fullmatch(t))
    return min(1.0, abbrevs / max(len(tokens), 1))


def numeric_density(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    nums = sum(1 for t in tokens if _RE_NUMBER.fullmatch(t))
    return min(1.0, nums / max(len(tokens), 1))


def sentence_complexity(tokens: list[str], sentences: int) -> float:
    if sentences <= 1:
        return 0.0
    if sentences <= 2:
        return 0.2
    if sentences <= 3:
        return 0.4
    if sentences <= 5:
        return 0.6
    return 0.8


def question_length_score(text: str) -> float:
    if not text:
        return 0.0
    length = len(text)
    if length <= 10:
        return 0.1
    if length <= 30:
        return 0.2
    if length <= 60:
        return 0.4
    if length <= 100:
        return 0.6
    if length <= 150:
        return 0.8
    return 1.0


def token_diversity(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    unique = len({t.lower() for t in tokens})
    return unique / max(len(tokens), 1)


def comparison_difficulty(
    overlap_ratio: float,
    entity_delta: int,
    type_mismatch: bool,
    relationship_count: int,
) -> float:
    score = 0.0
    if overlap_ratio < 0.2:
        score += 0.3
    elif overlap_ratio < 0.4:
        score += 0.2
    elif overlap_ratio > 0.9:
        score += 0.0
    else:
        score += 0.1
    if entity_delta > 3:
        score += 0.2
    elif entity_delta > 0:
        score += 0.1
    if type_mismatch:
        score += 0.15
    if relationship_count > 5:
        score += 0.2
    elif relationship_count > 2:
        score += 0.1
    return min(1.0, score)


def confidence_estimate(
    ambiguity: float,
    rare_tokens: float,
    entity_complex: float,
) -> float:
    return max(0.0, 1.0 - (ambiguity * 0.4 + rare_tokens * 0.3 + entity_complex * 0.3))


def risk_score(comparison_diff: float, ambiguity: float, entity_complex: float) -> float:
    return min(1.0, comparison_diff * 0.4 + ambiguity * 0.35 + entity_complex * 0.25)
