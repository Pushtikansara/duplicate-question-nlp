from __future__ import annotations

import re
import time
from typing import Any

from ares.adaptive.config_loader import AdaptiveRoutingConfig
from ares.adaptive.models import DifficultyAssessment

# ---------------------------------------------------------------------------
# Deterministic request-difficulty analysis.
#
# Analyses lexical overlap, negation, contradiction signals, ambiguity,
# abbreviations, numeric conflict, input length and (when available) the
# confidence of a cheap upfront model.  Fully reproducible: same input ->
# same assessment.  No external LLM is consulted.
# ---------------------------------------------------------------------------

_NEGATION_TOKENS = frozenset(
    {
        "not",
        "never",
        "no",
        "none",
        "nothing",
        "nobody",
        "cannot",
        "can't",
        "cant",
        "don't",
        "dont",
        "doesn't",
        "doesnt",
        "didn't",
        "didnt",
        "won't",
        "wont",
        "isn't",
        "isnt",
        "aren't",
        "arent",
        "wasn't",
        "wasnt",
        "weren't",
        "werent",
        "without",
    }
)

_AMBIGUOUS_WORDS = frozenset(
    {
        "bank",
        "check",
        "run",
        "set",
        "java",
        "python",
        "apple",
        "bat",
        "page",
        "match",
        "right",
        "left",
        "light",
        "rock",
        "spring",
        "note",
        "current",
        "banking",
        "credit",
        "sentence",
        "string",
        "model",
        "train",
    }
)

_CONTRADICTION_PAIRS: list[tuple[str, str]] = [
    ("increase", "decrease"),
    ("more", "less"),
    ("higher", "lower"),
    ("best", "worst"),
    ("start", "stop"),
    ("buy", "sell"),
    ("open", "closed"),
    ("true", "false"),
    ("yes", "no"),
    ("begin", "end"),
    ("raise", "lower"),
]

_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")
_ACRONYM_FLEX_RE = re.compile(r"\b[A-Za-z]{2,8}\b")

# Curated acronym -> expansion table used for abbreviation-relation detection
# (e.g. "ml" expands to "machine learning").  Overridable via config
# (difficulty.acronyms).  Keys are stored lower-cased; the scanner matches
# flexible forms (ML, M.L., ml) and normalises them to these keys.
_ACRONYM_DEFINITIONS: dict[str, str] = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "nl": "natural language",
    "dl": "deep learning",
    "cv": "computer vision",
    "api": "application programming interface",
    "ui": "user interface",
    "ux": "user experience",
    "os": "operating system",
    "gpu": "graphics processing unit",
    "cpu": "central processing unit",
    "ram": "random access memory",
    "db": "database",
    "cnn": "convolutional neural network",
    "svm": "support vector machine",
    "html": "hyper text markup language",
}


def _acronym_definitions(config: Any) -> dict[str, str]:
    definitions = dict(_ACRONYM_DEFINITIONS)
    configured = getattr(config, "difficulty_acronyms", None) or {}
    if isinstance(configured, dict):
        definitions.update({str(k).lower(): str(v) for k, v in configured.items()})
    return definitions


def _acronym_candidates(text: str, definitions: dict[str, str]) -> dict[str, str]:
    """Map canonical acronym key -> matched token for ML / M.L. / ml forms."""
    stripped = re.sub(r"(?<=\w)\.(?=\w)", "", text or "")
    candidates: dict[str, str] = {}
    for match in _ACRONYM_FLEX_RE.finditer(stripped):
        token = match.group(0)
        key = token.lower()
        if key.isalpha() and (token.isupper() or key in definitions):
            candidates.setdefault(key, token)
    return candidates


def _tokens(text: str) -> list[str]:
    return [t for t in re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower()).split() if t]


def _token_sets(text: str) -> set[str]:
    return set(_tokens(text))


def _jaccard(set_a: set[str], set_b: set[str]) -> float:
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "can",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "her",
        "his",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "its",
        "me",
        "my",
        "no",
        "not",
        "of",
        "on",
        "or",
        "our",
        "she",
        "so",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "they",
        "this",
        "to",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "will",
        "with",
        "would",
        "you",
        "your",
        "do",
        "does",
        "did",
        "up",
        "out",
        "over",
        "under",
        "again",
        "further",
        "once",
        "own",
        "same",
        "too",
        "very",
        "just",
        "because",
        "could",
        "into",
        "more",
        "most",
        "other",
        "some",
        "such",
        "than",
        "then",
        "only",
        "should",
        "about",
        "during",
        "before",
        "after",
        "above",
        "below",
    ]
)


def _content_tokens(text: str) -> list[str]:
    return [t for t in _tokens(text) if t not in _STOPWORDS]


def _negation_side(text: str) -> set[str]:
    tokens = _tokens(text)
    return {t for t in tokens if t in _NEGATION_TOKENS}


class DifficultyAnalyzer:
    """Deterministic assessor of request difficulty / uncertainty / risk."""

    version: str = "1.0.0"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = AdaptiveRoutingConfig(config)

    def analyze(
        self,
        question1: str,
        question2: str,
        *,
        cheap_confidence: float | None = None,
        analysis: Any = None,
    ) -> DifficultyAssessment:
        start = time.perf_counter()

        q1 = (question1 or "").strip()
        q2 = (question2 or "").strip()

        signals: dict[str, float] = {}
        details: dict[str, list[str]] = {}

        set1 = _token_sets(q1)
        set2 = _token_sets(q2)

        # Lexical overlap (normalised Jaccard over content tokens).
        overlap = _jaccard(set1, set2)
        signals["lexical_overlap"] = round(overlap, 4)

        # Content overlap excludes stopwords so that high stopword sharing does
        # not mask a genuine content gap (e.g. a synonym-substitution pair).
        content_overlap = _jaccard(set(_content_tokens(q1)), set(_content_tokens(q2)))
        signals["content_overlap"] = round(content_overlap, 4)

        # Exact-match shortcut -> trivially easy duplicate.
        exact = _normalized_exact(q1, q2)
        signals["exact_match"] = 1.0 if exact else 0.0

        # Negation asymmetry: negation present in exactly one question.
        neg1 = _negation_side(q1)
        neg2 = _negation_side(q2)
        negation_signal = 0.0
        if neg1 or neg2:
            if not (neg1 and neg2):
                negation_signal = 1.0
                details.setdefault("negation", []).extend(sorted(neg1 | neg2))
            elif neg1 != neg2:
                negation_signal = 0.5
                details.setdefault("negation", []).extend(sorted(neg1 ^ neg2))
        signals["negation"] = negation_signal

        # Contradiction: opposite-polarity tokens, or high overlap + negation.
        contradiction = 0.0
        shared = set1 & set2
        all_tokens = set1 | set2
        if negation_signal > 0 and overlap >= 0.4 and not exact:
            contradiction = 0.5
        for a, b in _CONTRADICTION_PAIRS:
            if (a in all_tokens) and (b in all_tokens) and not (a in shared and b in shared):
                contradiction = max(contradiction, 0.8)
                details.setdefault("contradiction", []).append(f"{a}/{b}")
        # Disjoint negation across both sides is a strong contradiction signal.
        if neg1 and neg2 and neg1 != neg2:
            contradiction = max(contradiction, 0.7)
        signals["contradiction"] = round(contradiction, 4)

        # Ambiguity: ambiguous vocabulary in a divergent context.  A shared
        # ambiguous token inside an otherwise overlapping pair is usually the
        # same sense (e.g. both questions about "python") and is NOT ambiguous;
        # only one-sided or divergent usage raises the signal.
        ambiguity = 0.0
        for token in _AMBIGUOUS_WORDS:
            in_q1 = token in set1
            in_q2 = token in set2
            if in_q1 and in_q2 and overlap >= 0.4:
                continue
            if in_q1 or in_q2:
                ambiguity = max(ambiguity, 1.0)
                details.setdefault("ambiguity", []).append(token)
        if overlap >= 0.5 and not exact and not shared:
            ambiguity = max(ambiguity, 0.4)
        signals["ambiguity"] = round(ambiguity, 4)

        # Abbreviation / acronym signals.
        abbreviation = 0.0
        definitions = _acronym_definitions(self._config)
        acr1 = _acronym_candidates(q1, definitions)
        acr2 = _acronym_candidates(q2, definitions)
        if acr1 or acr2:
            abbreviation = 1.0
            for token in list(acr1.values()) + list(acr2.values()):
                details.setdefault("abbreviation", []).append(token)
        signals["abbreviation"] = abbreviation

        # Abbreviation relation: an acronym in one question expands to the full
        # phrase present in the other (e.g. "ml" <-> "machine learning").
        # Cheap lexical models cannot equate the two, so this raises difficulty
        # and is a strong "route to a stronger model" signal.
        abbreviation_relation = 0.0
        content1_tokens = set(_content_tokens(q1))
        content2_tokens = set(_content_tokens(q2))

        def _expansion_present(expansion: str, other_content: set[str]) -> bool:
            exp_tokens = [t for t in _tokens(expansion) if t not in _STOPWORDS]
            return bool(exp_tokens) and all(t in other_content for t in exp_tokens)

        for key, token in acr1.items():
            exp = definitions.get(key)
            if exp and _expansion_present(exp, content2_tokens):
                abbreviation_relation = 1.0
                details.setdefault("abbreviation_relation", []).append(f"{token}={exp}")
        for key, token in acr2.items():
            if key in acr1:
                continue
            exp = definitions.get(key)
            if exp and _expansion_present(exp, content1_tokens):
                abbreviation_relation = 1.0
                details.setdefault("abbreviation_relation", []).append(f"{token}={exp}")
        signals["abbreviation_relation"] = abbreviation_relation

        # Numeric conflict: both sides contain numbers but different sets.
        numeric1 = set(_NUMBER_RE.findall(q1))
        numeric2 = set(_NUMBER_RE.findall(q2))
        numeric_conflict = 0.0
        if numeric1 and numeric2 and numeric1 != numeric2:
            numeric_conflict = 1.0
            details.setdefault("numeric_conflict", []).extend(sorted(numeric1 | numeric2))
        signals["numeric_conflict"] = numeric_conflict

        # Input length.
        total_len = len(q1) + len(q2)
        signals["long_input"] = 1.0 if total_len > 300 else 0.0
        signals["short_input"] = 1.0 if (len(q1) + len(q2)) <= 40 else 0.0
        details.setdefault("length", []).append(str(total_len))

        # Cheap upfront confidence (0..1), when provided.
        cheap_low = 0.0
        if cheap_confidence is not None:
            cheap_low = round(max(0.0, 1.0 - cheap_confidence), 4)
        signals["cheap_confidence_low"] = cheap_low

        # Semantic uncertainty reuse from the query-understanding layer if present.
        semantic_uncertainty = 0.0
        if analysis is not None:
            complexity = getattr(analysis, "complexity_analysis", None)
            if complexity is not None:
                semantic_uncertainty = round(min(1.0, float(getattr(complexity, "ambiguity_score", 0.0) or 0.0)), 4)
            sim = getattr(analysis, "similarity", None)
            if sim is not None:
                word_overlap = float(getattr(sim, "word_overlap_ratio", 0.0) or 0.0)
                if word_overlap > 0.0 and overlap == 0.0:
                    signals["lexical_overlap"] = round(min(1.0, word_overlap), 4)
        signals["semantic_uncertainty"] = semantic_uncertainty

        thresholds = self._config.difficulty_thresholds
        weights = self._config.difficulty_weights

        # Difficulty score: weighted blend of the derived signals.
        if exact:
            score = 0.0
        else:
            components = {
                "lexical": overlap,
                "negation": negation_signal,
                "contradiction": contradiction,
                "ambiguity": ambiguity,
                "abbreviation": abbreviation,
                "numeric_conflict": numeric_conflict,
                "length": signals["long_input"],
                "cheap_confidence": cheap_low,
            }
            total_weight = sum(float(weights.get(key, 0.0)) for key in components)
            if total_weight <= 0:
                total_weight = 1.0
            score = sum(float(weights.get(key, 0.0)) * value for key, value in components.items()) / total_weight
            score = max(0.0, min(1.0, score))
            # Semantic uncertainty from QU pushes borderline cases higher.
            score = max(score, semantic_uncertainty * 0.25)
            # Deterministic boosts: known hard-case signals can never be masked
            # by otherwise-high lexical overlap (e.g. antonym pairs).
            score = self._apply_boosts(
                score,
                contradiction=contradiction,
                negation_signal=negation_signal,
                ambiguity=ambiguity,
                numeric_conflict=numeric_conflict,
                abbreviation=abbreviation,
                abbreviation_relation=abbreviation_relation,
            )
            # Content-gap boost: high raw overlap driven mostly by stopwords
            # with a low content overlap signals a synonym-substitution pair
            # that cheap lexical models are known to misclassify.
            score = self._apply_content_gap_boost(
                score,
                overlap=overlap,
                content_overlap=content_overlap,
            )

        level = self._classify(score, thresholds)
        uncertainty = self._uncertainty(score, signals)
        risk = self._risk(score, signals, level)

        budget = self._recommend_budget(level, risk)
        strategy = self._recommend_strategy(level)

        explanation = (
            f"difficulty={score:.3f} ({level}), risk={risk}, overlap={overlap:.2f}, "
            f"negation={negation_signal:.1f}, contradiction={contradiction:.1f}, "
            f"ambiguity={ambiguity:.1f}, cheap_confidence_low={cheap_low:.2f}"
        )

        elapsed = (time.perf_counter() - start) * 1000
        return DifficultyAssessment(
            difficulty_score=round(score, 4),
            difficulty_level=level,
            uncertainty_score=round(uncertainty, 4),
            risk_level=risk,
            signals=signals,
            signal_details=details,
            recommended_budget=budget,
            recommended_strategy=strategy,
            explanation=explanation,
            processing_time_ms=round(elapsed, 4),
            version=self.version,
        )

    def _apply_boosts(
        self,
        score: float,
        *,
        contradiction: float,
        negation_signal: float,
        ambiguity: float,
        numeric_conflict: float,
        abbreviation: float,
        abbreviation_relation: float = 0.0,
    ) -> float:
        rules = self._config.difficulty_boosts
        signals = {
            "contradiction": contradiction,
            "negation_overlap": negation_signal,
            "ambiguity": ambiguity,
            "numeric_conflict": numeric_conflict,
            "abbreviation": abbreviation,
            "abbreviation_relation": abbreviation_relation,
        }
        for key, value in signals.items():
            rule = rules.get(key)
            if not rule:
                continue
            if float(value) >= float(rule.get("signal_min", 0.5)):
                score = max(score, float(rule.get("min_score", 0.0)))
        return score

    def _apply_content_gap_boost(self, score: float, *, overlap: float, content_overlap: float) -> float:
        rule = self._config.difficulty_boosts.get("content_gap") or {}
        overlap_min = float(rule.get("overlap_min", 0.45))
        content_max = float(rule.get("content_max", 0.35))
        gap_min = float(rule.get("gap_min", 0.15))
        min_score = float(rule.get("min_score", 0.45))
        if overlap >= overlap_min and content_overlap <= content_max and (overlap - content_overlap) >= gap_min:
            return max(score, min_score)
        return score

    @staticmethod
    def _classify(score: float, thresholds: dict[str, Any]) -> str:
        if score <= float(thresholds.get("easy_max", 0.33)):
            return "easy"
        if score <= float(thresholds.get("medium_max", 0.60)):
            return "medium"
        if score <= float(thresholds.get("hard_max", 0.80)):
            return "hard"
        return "critical"

    @staticmethod
    def _uncertainty(score: float, signals: dict[str, float]) -> float:
        uncertainty = score * 0.6
        uncertainty += signals.get("ambiguity", 0.0) * 0.2
        uncertainty += signals.get("negation", 0.0) * 0.1
        uncertainty += signals.get("cheap_confidence_low", 0.0) * 0.1
        return max(0.0, min(1.0, uncertainty))

    @staticmethod
    def _risk(score: float, signals: dict[str, float], level: str) -> str:
        risk_acc = score * 0.5
        risk_acc += signals.get("contradiction", 0.0) * 0.3
        risk_acc += signals.get("numeric_conflict", 0.0) * 0.2
        if level == "easy":
            return "low"
        if risk_acc < 0.35:
            return "low"
        if risk_acc < 0.6:
            return "medium"
        if risk_acc < 0.8:
            return "high"
        return "critical"

    @staticmethod
    def _recommend_budget(level: str, risk: str) -> str:
        if level in ("hard", "critical"):
            return "high"
        if level == "medium":
            return "medium"
        if risk in ("high", "critical"):
            return "medium"
        return "low"

    @staticmethod
    def _recommend_strategy(level: str) -> str:
        if level == "easy":
            return "fast_lexical"
        if level == "medium":
            return "baseline_classifier"
        if level in ("hard", "critical"):
            return "cross_encoder"
        return "fast_lexical"


def _normalized_exact(q1: str, q2: str) -> bool:
    norm1 = " ".join(re.sub(r"[^a-zA-Z0-9\s]", " ", q1.lower()).split())
    norm2 = " ".join(re.sub(r"[^a-zA-Z0-9\s]", " ", q2.lower()).split())
    return bool(norm1) and norm1 == norm2
