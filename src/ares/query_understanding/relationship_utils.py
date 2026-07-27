from __future__ import annotations

import math
import re
import unicodedata

from ares.query_understanding.relationship_patterns import (
    ABBREVIATION_MAP,
    ANTONYM_MAP,
    DATE_PATTERN,
    NUMBER_PATTERN,
    SPELLING_VARIANTS,
    SYNONYM_MAP,
    TIME_PATTERN,
    UNIT_NORMALIZATION,
    UNIT_PATTERN,
)

_WHITESPACE = re.compile(r"\s+")
_PUNCTUATION = re.compile(r"[^\w\s]")
_MULTI_SPACE = re.compile(r"\s+")


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    return _WHITESPACE.split(text.strip())


_CONTRACTIONS = {
    "what's": "what is",
    "it's": "it is",
    "that's": "that is",
    "there's": "there is",
    "here's": "here is",
    "who's": "who is",
    "how's": "how is",
    "where's": "where is",
    "when's": "when is",
    "why's": "why is",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "won't": "will not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "can't": "cannot",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "haven't": "have not",
    "hasn't": "has not",
    "hadn't": "had not",
    "i'm": "i am",
    "you're": "you are",
    "he's": "he is",
    "she's": "she is",
    "we're": "we are",
    "they're": "they are",
    "i've": "i have",
    "you've": "you have",
    "we've": "we have",
    "they've": "they have",
    "i'll": "i will",
    "you'll": "you will",
    "he'll": "he will",
    "she'll": "she will",
    "we'll": "we will",
    "they'll": "they will",
    "i'd": "i would",
    "you'd": "you would",
    "he'd": "he would",
    "she'd": "she would",
    "we'd": "we would",
    "they'd": "they would",
}


def normalize_text(text: str) -> str:
    result = unicodedata.normalize("NFKC", text)
    result = _MULTI_SPACE.sub(" ", result).strip().lower()
    for contraction, expansion in _CONTRACTIONS.items():
        result = result.replace(contraction, expansion)
    return result


def strip_punctuation(text: str) -> str:
    return _PUNCTUATION.sub("", text)


def remove_stopwords(tokens: list[str], stopwords: frozenset) -> list[str]:
    return [t for t in tokens if t not in stopwords]


def tokens_to_set(tokens: list[str]) -> set[str]:
    return {strip_punctuation(t).lower() for t in tokens if strip_punctuation(t)}


def compute_jaccard(tokens1: list[str], tokens2: list[str]) -> float:
    set1 = tokens_to_set(tokens1)
    set2 = tokens_to_set(tokens2)
    if not set1 and not set2:
        return 0.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union) if union else 0.0


def compute_token_overlap(tokens1: list[str], tokens2: list[str]) -> int:
    set1 = tokens_to_set(tokens1)
    set2 = tokens_to_set(tokens2)
    return len(set1 & set2)


def edit_distance(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]


def normalized_edit_distance(s1: str, s2: str) -> float:
    if not s1 and not s2:
        return 0.0
    dist = edit_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return dist / max_len if max_len > 0 else 0.0


def find_numbers(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(), m.start(), m.end()) for m in NUMBER_PATTERN.finditer(text)]


def find_dates(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(), m.start(), m.end()) for m in DATE_PATTERN.finditer(text)]


def find_times(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(), m.start(), m.end()) for m in TIME_PATTERN.finditer(text)]


def find_units(text: str) -> list[tuple[str, str, float, int, int]]:
    results: list[tuple[str, str, float, int, int]] = []
    for m in UNIT_PATTERN.finditer(text):
        val_str = m.group(1)
        unit = m.group(2).lower()
        try:
            val = float(val_str.replace(",", ""))
        except ValueError:
            continue
        normalized_unit = UNIT_NORMALIZATION.get(unit, unit)
        results.append((m.group(), normalized_unit, val, m.start(), m.end()))
    return results


def compare_units(
    units1: list[tuple[str, str, float, int, int]],
    units2: list[tuple[str, str, float, int, int]],
) -> list[dict]:
    results: list[dict] = []
    for u1 in units1:
        for u2 in units2:
            if u1[1] == u2[1]:
                if abs(u1[2] - u2[2]) > 0.001:
                    results.append(
                        {
                            "type": "unit_difference",
                            "q1_value": u1[2],
                            "q2_value": u2[2],
                            "unit": u1[1],
                            "difference": abs(u1[2] - u2[2]),
                        }
                    )
            else:
                results.append(
                    {
                        "type": "unit_change",
                        "q1_unit": u1[1],
                        "q2_unit": u2[1],
                        "q1_value": u1[2],
                        "q2_value": u2[2],
                    }
                )
    return results


def _clean(word: str) -> str:
    return strip_punctuation(word).lower().strip(".")


def check_abbreviation(word1: str, word2: str) -> bool:
    w1 = _clean(word1)
    w2 = _clean(word2)
    if w1 in ABBREVIATION_MAP:
        return w2 in ABBREVIATION_MAP[w1]
    if w2 in ABBREVIATION_MAP:
        return w1 in ABBREVIATION_MAP[w2]
    # Also check multi-word expansions
    if w1 in ABBREVIATION_MAP:
        for expand in ABBREVIATION_MAP[w1]:
            if w2 in expand.split():
                return True
    if w2 in ABBREVIATION_MAP:
        for expand in ABBREVIATION_MAP[w2]:
            if w1 in expand.split():
                return True
    return False


def check_synonym(word1: str, word2: str) -> bool:
    w1 = _clean(word1)
    w2 = _clean(word2)
    if w1 in SYNONYM_MAP and w2 in SYNONYM_MAP[w1]:
        return True
    return bool(w2 in SYNONYM_MAP and w1 in SYNONYM_MAP[w2])


def check_antonym(word1: str, word2: str) -> bool:
    w1 = _clean(word1)
    w2 = _clean(word2)
    if w1 in ANTONYM_MAP and ANTONYM_MAP[w1] == w2:
        return True
    return bool(w2 in ANTONYM_MAP and ANTONYM_MAP[w2] == w1)


def check_spelling_variant(word1: str, word2: str) -> bool:
    w1 = _clean(word1)
    w2 = _clean(word2)
    if w1 in SPELLING_VARIANTS and w2 in SPELLING_VARIANTS[w1]:
        return True
    return bool(w2 in SPELLING_VARIANTS and w1 in SPELLING_VARIANTS[w2])


def compute_shared_token_ratio(tokens1: list[str], tokens2: list[str]) -> float:
    if not tokens1 or not tokens2:
        return 0.0
    set1 = {t.lower() for t in tokens1}
    set2 = {t.lower() for t in tokens2}
    shared = set1 & set2
    return len(shared) / min(len(set1), len(set2)) if min(len(set1), len(set2)) > 0 else 0.0


def cosine_similarity_binary(tokens1: list[str], tokens2: list[str]) -> float:
    set1 = tokens_to_set(tokens1)
    set2 = tokens_to_set(tokens2)
    if not set1 or not set2:
        return 0.0
    intersection = set1 & set2
    return len(intersection) / (math.sqrt(len(set1)) * math.sqrt(len(set2))) if set1 and set2 else 0.0
