from __future__ import annotations

import re
import unicodedata

import emoji as emoji_lib

_URL_PATTERN = re.compile(
    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?"
    r"(?:/[\w\-./?%&+=~!#]*)?",
    re.IGNORECASE,
)
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_DATE_PATTERN = re.compile(
    r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b",
    re.IGNORECASE,
)
_CODE_PATTERN = re.compile(
    r"(?:def |class |import |from |return |if __name__|function |var |let |const |"
    r"print\(|console\.log|<[!?]|```|`\w+`|&\w+;)"
)
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "\U0001f900-\U0001f9ff"
    "\U0000200d"
    "\U0000fe0f"
    "]+",
    flags=re.UNICODE,
)
_REPEATED_CHAR = re.compile(r"(.)\1{3,}")
_SPECIAL_CHARS = re.compile(r"[^a-zA-Z0-9\s]")
_NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_SENTENCE_SPLIT = re.compile(r"[.!?]+")
_WHITESPACE = re.compile(r"\s+")
_SYLLABLE_PATTERN = re.compile(r"[aeiouyAEIOUY]+")
_STOPWORDS = frozenset(
    {
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
        "up",
        "about",
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
        "is",
        "am",
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
        "i",
        "me",
        "my",
        "myself",
        "we",
        "us",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
    }
)
_QUESTION_WORDS = frozenset(
    {
        "what",
        "when",
        "where",
        "why",
        "how",
        "who",
        "whom",
        "whose",
        "which",
    }
)
_LANGUAGE_PATTERNS: dict[str, list[tuple[str, float]]] = {
    "en": [
        (r"\bthe\b", 1.0),
        (r"\band\b", 0.8),
        (r"\bto\b", 0.7),
        (r"\bof\b", 0.7),
        (r"\bis\b", 0.6),
        (r"\bin\b", 0.6),
        (r"\bthat\b", 0.5),
        (r"\bit\b", 0.5),
        (r"\bfor\b", 0.4),
        (r"\bwith\b", 0.4),
    ],
    "es": [
        (r"\bel\b", 1.0),
        (r"\bla\b", 1.0),
        (r"\blos\b", 0.8),
        (r"\blas\b", 0.8),
        (r"\by\b", 0.7),
        (r"\bde\b", 0.7),
        (r"\bque\b", 0.6),
        (r"\ben\b", 0.5),
        (r"\bpor\b", 0.4),
    ],
    "fr": [
        (r"\ble\b", 1.0),
        (r"\bla\b", 1.0),
        (r"\bles\b", 0.8),
        (r"\bde\b", 0.8),
        (r"\bdu\b", 0.7),
        (r"\bdes\b", 0.7),
        (r"\bet\b", 0.7),
        (r"\bque\b", 0.6),
        (r"\bdans\b", 0.4),
    ],
    "de": [
        (r"\bder\b", 1.0),
        (r"\bdie\b", 1.0),
        (r"\bdas\b", 0.9),
        (r"\bund\b", 0.8),
        (r"\bmit\b", 0.5),
        (r"\bauf\b", 0.4),
    ],
}


def validate_input(text_a: str, text_b: str) -> None:
    if not isinstance(text_a, str) or not isinstance(text_b, str):
        raise TypeError("Both inputs must be strings")
    if not text_a.strip() and not text_b.strip():
        raise ValueError("At least one question must be non-empty")


def normalize_text(text: str, lower: bool = True, strip_whitespace: bool = True) -> str:
    result = text
    if strip_whitespace:
        result = _WHITESPACE.sub(" ", result).strip()
    if lower:
        result = result.lower()
    return result


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "unknown"
    lower = text.strip().lower()
    tokens = _WHITESPACE.split(lower)
    if not tokens:
        return "unknown"

    if text.startswith("¿"):
        return "es"

    scores: dict[str, float] = {}
    for lang, patterns in _LANGUAGE_PATTERNS.items():
        score = 0.0
        for pattern_str, weight in patterns:
            if re.search(pattern_str, lower):
                score += weight
        scores[lang] = score

    has_latin = any(ord(c) < 0x02B0 for c in text if c.isalpha())
    if not has_latin:
        cjk = sum(1 for c in text if unicodedata.category(c) in ("Lo",) or 0x4E00 <= ord(c) <= 0x9FFF)
        if cjk > len(text) * 0.3:
            return "zh"
        arabic = sum(1 for c in text if 0x0600 <= ord(c) <= 0x06FF)
        if arabic > len(text) * 0.3:
            return "ar"
        cyrillic = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF)
        if cyrillic > len(text) * 0.3:
            return "ru"

    if not scores:
        return "en"
    return max(scores, key=scores.get) if any(s > 0 for s in scores.values()) else "en"


def count_syllables(word: str) -> int:
    if not word or len(word) <= 2:
        return 1
    word = word.lower()
    matches = _SYLLABLE_PATTERN.findall(word)
    count = len(matches)
    if word.endswith("e") and count > 1:
        count -= 1
    if word.endswith("le") and len(word) > 2 and word[-3] not in "aeiouy":
        count += 1
    return max(count, 1)


def flesch_reading_ease(total_syllables: int, total_words: int, total_sentences: int) -> float:
    if total_words == 0 or total_sentences == 0:
        return 0.0
    return max(
        0.0, min(100.0, 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words))
    )


def tokenize(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    return _WHITESPACE.split(stripped)


def sentencize(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]


def is_question(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    if text.rstrip().endswith("?"):
        return True
    first_word = text.split()[0].lower().strip("""'""") if text.split() else ""
    return first_word in _QUESTION_WORDS


def contains_url(text: str) -> bool:
    return bool(_URL_PATTERN.search(text))


def contains_email(text: str) -> bool:
    return bool(_EMAIL_PATTERN.search(text))


def contains_date(text: str) -> bool:
    return bool(_DATE_PATTERN.search(text))


def contains_code(text: str) -> bool:
    return bool(_CODE_PATTERN.search(text))


def contains_emoji(text: str) -> bool:
    return bool(emoji_lib.emoji_count(text)) or bool(_EMOJI_PATTERN.search(text))


def contains_number(text: str) -> bool:
    return bool(_NUMBER_PATTERN.search(text))


def find_numbers(text: str) -> list[str]:
    return _NUMBER_PATTERN.findall(text)


def find_urls(text: str) -> list[str]:
    return _URL_PATTERN.findall(text)


def find_emails(text: str) -> list[str]:
    return _EMAIL_PATTERN.findall(text)


def find_dates(text: str) -> list[str]:
    return _DATE_PATTERN.findall(text)


def find_code_snippets(text: str) -> list[str]:
    return _CODE_PATTERN.findall(text)


def is_stopword(word: str) -> bool:
    return word.lower() in _STOPWORDS


def repeated_char_ratio(text: str) -> float:
    if not text:
        return 0.0
    repeated_count = sum(max(0, len(m.group()) - 3) for m in _REPEATED_CHAR.finditer(text))
    return repeated_count / len(text) if text else 0.0


def capitalization_ratio(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    alpha_chars = sum(1 for c in text if c.isalpha())
    upper_chars = sum(1 for c in text if c.isupper())
    return upper_chars / alpha_chars if alpha_chars > 0 else 0.0


def uppercase_word_ratio(text: str) -> float:
    words = tokenize(text)
    if not words:
        return 0.0
    upper = sum(1 for w in words if w.isupper() and len(w) > 1)
    return upper / len(words)


def lowercase_word_ratio(text: str) -> float:
    words = tokenize(text)
    if not words:
        return 0.0
    lower = sum(1 for w in words if w.islower())
    return lower / len(words)


def whitespace_count(text: str) -> int:
    return len(_WHITESPACE.findall(text))


def symbol_count(text: str) -> int:
    return len(_SPECIAL_CHARS.findall(text))


def punctuation_count(text: str) -> int:
    punct_chars = set(".,!?;:-'\"()[]{}<>/\\@#$%^&*_~`+=|")
    return sum(1 for c in text if c in punct_chars)


def numeric_count(text: str) -> int:
    return len(_NUMBER_PATTERN.findall(text))


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


def jaccard_similarity(tokens1: set[str], tokens2: set[str]) -> float:
    if not tokens1 and not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union) if union else 0.0


def character_overlap(t1: str, t2: str) -> float:
    if not t1 or not t2:
        return 0.0
    set1 = set(t1.replace(" ", ""))
    set2 = set(t2.replace(" ", ""))
    return jaccard_similarity(set1, set2)


def complex_word_count(words: list[str]) -> int:
    return sum(1 for w in words if len(w) > 6 and count_syllables(w) >= 3)
