from __future__ import annotations

import re

from ares.query_understanding.type_patterns import (
    FIRST_WORD_RULES,
    MUTUALLY_EXCLUSIVE,
    TYPE_PATTERNS,
)
from ares.query_understanding.utils import (
    contains_code,
    contains_date,
    contains_number,
    tokenize,
)


def classify_question(text: str, normalized: str = "") -> tuple[str, float, str]:
    if not text or not text.strip():
        return "other", 0.0, "empty input"

    raw = text
    txt = normalized if normalized else text.strip().lower()
    tokens = tokenize(txt)
    first_word = tokens[0].lower().strip("""'""") if tokens else ""
    clean_tokens = [t.strip(".,!?;:'\"()[]{}") for t in tokens]
    clean_token_count = len([t for t in clean_tokens if t])

    candidates: list[tuple[str, float, str]] = []

    code_match = _check_code(text, txt, tokens)
    if code_match:
        candidates.append(code_match)

    numeric_match = _check_numeric(text, txt, tokens)
    if numeric_match:
        candidates.append(numeric_match)

    temporal_match = _check_temporal(text, txt, tokens)
    if temporal_match:
        candidates.append(temporal_match)

    for qtype, patterns in TYPE_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(txt)
            if match:
                score = _score_for_type(qtype, match, tokens, first_word, txt)
                candidates.append((qtype, score, match.group()))
                break

    first_word_match = _check_first_word(first_word, tokens, clean_token_count)
    if first_word_match:
        candidates.append(first_word_match)

    if not candidates:
        return "other", 0.0, "no matching patterns"

    candidates.sort(key=lambda x: x[1], reverse=True)

    best_type, best_score, best_reason = candidates[0]

    tied = [c for c in candidates if abs(c[1] - best_score) < 0.05]
    if len(tied) > 1:
        best_type, best_score, best_reason = _resolve_ties(tied, first_word, txt, tokens)

    if best_score < 0.2:
        return "other", best_score, f"low_confidence:{best_reason}"

    return best_type, round(best_score, 4), best_reason


def _check_code(raw: str, txt: str, tokens: list[str]) -> tuple[str, float, str] | None:
    if contains_code(raw):
        if any(w in txt for w in ("how to", "fix", "debug", "error", "bug", "issue")):
            return "troubleshooting", 0.85, "code_with_troubleshooting_keywords"
        if any(w in txt for w in ("how to", "write", "create", "implement", "build", "code")):
            return "how_to", 0.75, "code_with_how_to_keywords"
        return "code", 0.90, "contains_code"

    code_keywords = {
        "function",
        "class",
        "method",
        "variable",
        "syntax",
        "compile",
        "library",
        "framework",
        "api",
        "module",
        "package",
        "dependency",
    }
    if code_keywords & set(tokens):
        return "code", 0.60, "code_related_keywords"

    return None


def _check_numeric(raw: str, txt: str, tokens: list[str]) -> tuple[str, float, str] | None:
    how_words = {
        "how many",
        "how much",
        "how long",
        "how far",
        "how old",
        "how often",
        "how tall",
        "how wide",
        "how deep",
    }
    if any(hw in txt for hw in how_words):
        return "numeric", 0.85, f"how_quantity:{txt[:30]}"

    if contains_number(raw) and (
        any(
            w in txt
            for w in {
                "price",
                "cost",
                "number",
                "count",
                "amount",
                "total",
                "percentage",
                "percent",
                "rate",
                "statistics",
                "figure",
            }
        )
    ):
        return "numeric", 0.75, "number_with_numeric_keywords"

    price_pattern = re.compile(r"\bwhat\s+is\s+the\s+(?:price|cost|number|count|total|amount)\b", re.IGNORECASE)
    if price_pattern.search(txt):
        return "numeric", 0.80, "what_is_the_price"

    return None


def _check_temporal(raw: str, txt: str, tokens: list[str]) -> tuple[str, float, str] | None:
    if contains_date(raw):
        if txt.startswith("when"):
            return "temporal", 0.90, "when_with_date"
        return "temporal", 0.70, "contains_date"

    time_pattern = re.compile(r"\bwhat\s+time\b", re.IGNORECASE)
    if time_pattern.search(txt):
        return "temporal", 0.75, "what_time"

    return None


def _check_first_word(first_word: str, tokens: list[str], clean_token_count: int) -> tuple[str, float, str] | None:
    for qtype, words in FIRST_WORD_RULES.items():
        if first_word in words:
            if qtype == "yes_no":
                return (qtype, 0.60, f"first_word:{first_word}")
            elif qtype == "organization":
                extra = {"company", "organization", "team", "group", "brand", "startup"}
                if extra & set(tokens):
                    return (qtype, 0.75, f"first_word:{first_word}")
                return (qtype, 0.45, f"first_word:{first_word}_ambiguous")
            elif qtype == "definition":
                if first_word == "what":
                    if clean_token_count <= 8:
                        return (qtype, 0.65, f"first_word:{first_word}_short")
                    return ("explanation", 0.50, f"first_word:{first_word}_long")
                return (qtype, 0.70, f"first_word:{first_word}")
            elif qtype == "reason_why":
                return (qtype, 0.85, f"first_word:{first_word}")
            elif qtype == "how_to":
                return (qtype, 0.75, f"first_word:{first_word}")
            elif qtype in ("temporal", "location", "person"):
                return (qtype, 0.80, f"first_word:{first_word}")
            return (qtype, 0.60, f"first_word:{first_word}")
    return None


def _score_for_type(qtype: str, match: re.Match, tokens: list[str], first_word: str, txt: str) -> float:
    base_scores = {
        "definition": 0.75,
        "how_to": 0.80,
        "comparison": 0.85,
        "explanation": 0.70,
        "reason_why": 0.85,
        "opinion": 0.80,
        "factoid": 0.75,
        "yes_no": 0.60,
        "numeric": 0.80,
        "temporal": 0.80,
        "location": 0.80,
        "person": 0.80,
        "organization": 0.70,
        "procedure": 0.75,
        "recommendation": 0.80,
        "troubleshooting": 0.85,
        "list": 0.75,
    }

    score = base_scores.get(qtype, 0.60)

    matched_text = match.group().lower()
    match_len_ratio = len(matched_text) / max(len(tokens) * 5, 1)
    if match_len_ratio > 0.3:
        score = min(1.0, score + 0.10)
    elif match_len_ratio < 0.05:
        score = max(0.3, score - 0.15)

    if qtype == "yes_no" and not _text_ends_with_question_mark(tokens):
        score = max(0.2, score - 0.20)

    if qtype == "recommendation" and _has_comparison_signal(txt):
        score = max(0.5, score - 0.25)

    if qtype == "comparison" and _has_comparison_signal(txt):
        score = min(1.0, score + 0.10)

    if qtype in MUTUALLY_EXCLUSIVE:
        for excl in MUTUALLY_EXCLUSIVE[qtype]:
            excl_patterns = TYPE_PATTERNS.get(excl, [])
            for p in excl_patterns:
                if p.search(" ".join(tokens)):
                    score = max(0.1, score - 0.30)
                    break

    return round(score, 4)


def _has_comparison_signal(txt: str) -> bool:
    signals = {"vs", "versus", "difference between", "compare", "contrast"}
    return any(s in txt for s in signals)


def _resolve_ties(
    tied: list[tuple[str, float, str]], first_word: str, txt: str, tokens: list[str]
) -> tuple[str, float, str]:
    if _has_comparison_signal(txt):
        for t in tied:
            if t[0] == "comparison":
                return t

    preferred_order = [
        "code",
        "troubleshooting",
        "comparison",
        "reason_why",
        "yes_no",
        "how_to",
        "temporal",
        "location",
        "person",
        "numeric",
        "recommendation",
        "opinion",
        "factoid",
        "definition",
        "procedure",
        "explanation",
        "list",
        "organization",
        "other",
    ]
    for preferred in preferred_order:
        for t in tied:
            if t[0] == preferred:
                return t

    return tied[0]


def _text_ends_with_question_mark(tokens: list[str]) -> bool:
    if not tokens:
        return False
    return tokens[-1].endswith("?")
