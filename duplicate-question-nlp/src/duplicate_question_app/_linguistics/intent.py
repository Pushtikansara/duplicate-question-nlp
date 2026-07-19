"""Question Intent Detection — classifies questions into intent categories.

Categories:
- Definition: "What is X?", "Define X", "Explain X"
- Comparison: "X vs Y", "Difference between X and Y", "Compare X and Y"
- Installation: "How to install X", "Install X", "Setup X"
- Tutorial: "How to X", "Tutorial X", "Guide to X"
- Troubleshooting: "Error X", "Fix X", "Why does X fail", "Debug X"
- Recommendation: "Best X", "Recommend X", "Which X should I use"
- Opinion: "Is X better than Y", "Should I use X", "Thoughts on X"
- Debugging: "How to debug X", "Traceback X", "Stack trace X"
- Translation: "Translate X", "Convert X to Y", "X in Y language"
- Math: "Calculate X", "Solve X", "Formula for X"
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class IntentCategory(Enum):
    DEFINITION = "definition"
    COMPARISON = "comparison"
    INSTALLATION = "installation"
    TUTORIAL = "tutorial"
    TROUBLESHOOTING = "troubleshooting"
    RECOMMENDATION = "recommendation"
    OPINION = "opinion"
    DEBUGGING = "debugging"
    TRANSLATION = "translation"
    MATH = "math"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    primary_intent: IntentCategory
    confidence: float
    all_scores: Dict[IntentCategory, float]
    detected_patterns: List[str]


# Pattern definitions for each intent category
_INTENT_PATTERNS: Dict[IntentCategory, List[Tuple[str, float]]] = {
    IntentCategory.DEFINITION: [
        (r"\bwhat\s+is\b", 1.0),
        (r"\bdefine\b", 0.9),
        (r"\bexplain\b", 0.8),
        (r"\bmeaning\s+of\b", 0.9),
        (r"\bdefinition\s+of\b", 0.9),
        (r"\bwhat\s+does\b.*\bmean\b", 0.9),
        (r"\bdescribe\b", 0.6),
        (r"\btell\s+me\s+about\b", 0.6),
    ],
    IntentCategory.COMPARISON: [
        (r"\bvs\b", 1.0),
        (r"\bversus\b", 0.9),
        (r"\bdifference\s+between\b", 1.0),
        (r"\bcompare\b", 0.9),
        (r"\bwhich\s+is\s+better\b", 0.8),
        (r"\bbetter\s+than\b", 0.7),
        (r"\bpros?\s+and\s+cons?\b", 0.8),
        (r"\badvantages?\s+over\b", 0.7),
        (r"\bversus\b", 0.9),
        (r"\bor\b.*\bwhich\b", 0.5),
    ],
    IntentCategory.INSTALLATION: [
        (r"\binstall\b", 1.0),
        (r"\bsetup\b", 0.8),
        (r"\bhow\s+to\s+install\b", 1.0),
        (r"\bdownload\b", 0.7),
        (r"\bgetting\s+started\b", 0.6),
        (r"\bconfigure\b", 0.6),
        (r"\benable\b", 0.5),
        (r"\badd\s+to\s+path\b", 0.7),
    ],
    IntentCategory.TUTORIAL: [
        (r"\bhow\s+to\b", 0.9),
        (r"\btutorial\b", 1.0),
        (r"\bguide\b", 0.8),
        (r"\bwalkthrough\b", 0.8),
        (r"\bstep\s+by\s+step\b", 0.8),
        (r"\blearn\b", 0.6),
        (r"\bexample\s+of\b", 0.6),
        (r"\bshow\s+me\b", 0.5),
        (r"\bgetting\s+started\s+with\b", 0.7),
    ],
    IntentCategory.TROUBLESHOOTING: [
        (r"\berror\b", 0.9),
        (r"\bfix\b", 0.8),
        (r"\bsolve\b", 0.7),
        (r"\bwhy\s+does\b.*\bfail\b", 0.9),
        (r"\bnot\s+working\b", 0.9),
        (r"\bbroken\b", 0.8),
        (r"\bissue\b", 0.6),
        (r"\bproblem\b", 0.6),
        (r"\btroubleshoot\b", 0.9),
        (r"\bcrash\b", 0.8),
        (r"\bexception\b", 0.8),
        (r"\bstack\s+trace\b", 0.8),
        (r"\btraceback\b", 0.8),
    ],
    IntentCategory.RECOMMENDATION: [
        (r"\bbest\b", 0.9),
        (r"\brecommend\b", 1.0),
        (r"\bwhich\s+should\s+i\b", 0.9),
        (r"\bwhat\s+should\s+i\b", 0.8),
        (r"\btop\b", 0.7),
        (r"\bchoose\b", 0.6),
        (r"\bpick\b", 0.6),
        (r"\bsuggest\b", 0.8),
        (r"\bprefer\b", 0.5),
    ],
    IntentCategory.OPINION: [
        (r"\bopinion\b", 1.0),
        (r"\bthink\b", 0.6),
        (r"\bfeel\b", 0.5),
        (r"\bprefer\b", 0.6),
        (r"\bis\s+it\s+worth\b", 0.8),
        (r"\bshould\s+i\b", 0.7),
        (r"\bthoughts\b", 0.7),
        (r"\bany\s+experience\b", 0.7),
    ],
    IntentCategory.DEBUGGING: [
        (r"\bdebug\b", 1.0),
        (r"\btrace\b", 0.7),
        (r"\bbreakpoint\b", 0.8),
        (r"\bprint\s+statement\b", 0.6),
        (r"\blog\b", 0.5),
        (r"\binspect\b", 0.6),
        (r"\bprofile\b", 0.6),
        (r"\bmemory\s+leak\b", 0.8),
    ],
    IntentCategory.TRANSLATION: [
        (r"\btranslate\b", 1.0),
        (r"\bconvert\s+.*\bto\b", 0.8),
        (r"\bin\s+\w+\s+language\b", 0.7),
        (r"\bport\b", 0.6),
        (r"\brewrite\s+in\b", 0.7),
        (r"\bmigrate\s+to\b", 0.7),
    ],
    IntentCategory.MATH: [
        (r"\bcalculate\b", 0.9),
        (r"\bcompute\b", 0.8),
        (r"\bsolve\b", 0.7),
        (r"\bformula\b", 0.8),
        (r"\bequation\b", 0.8),
        (r"\bderivative\b", 0.7),
        (r"\bintegral\b", 0.7),
        (r"\bmatrix\b", 0.6),
        (r"\bprobability\b", 0.6),
        (r"\bstatistics\b", 0.6),
    ],
}


# Patterns that indicate incompatibility between intents
_INTENT_CONFLICTS: Dict[IntentCategory, Set[IntentCategory]] = {
    IntentCategory.DEFINITION: {IntentCategory.INSTALLATION, IntentCategory.TROUBLESHOOTING},
    IntentCategory.COMPARISON: {IntentCategory.INSTALLATION, IntentCategory.TUTORIAL},
    IntentCategory.INSTALLATION: {IntentCategory.DEFINITION, IntentCategory.COMPARISON, IntentCategory.TUTORIAL},
    IntentCategory.TUTORIAL: {IntentCategory.COMPARISON, IntentCategory.TROUBLESHOOTING},
    IntentCategory.TROUBLESHOOTING: {IntentCategory.DEFINITION, IntentCategory.TUTORIAL, IntentCategory.INSTALLATION},
    IntentCategory.RECOMMENDATION: {IntentCategory.INSTALLATION, IntentCategory.TROUBLESHOOTING},
    IntentCategory.OPINION: {IntentCategory.INSTALLATION, IntentCategory.TROUBLESHOOTING},
    IntentCategory.DEBUGGING: {IntentCategory.INSTALLATION, IntentCategory.DEFINITION},
    IntentCategory.TRANSLATION: {IntentCategory.INSTALLATION, IntentCategory.TROUBLESHOOTING},
    IntentCategory.MATH: {IntentCategory.INSTALLATION, IntentCategory.TROUBLESHOOTING},
}


def _compile_patterns() -> Dict[IntentCategory, List[Tuple[re.Pattern, float]]]:
    compiled = {}
    for category, patterns in _INTENT_PATTERNS.items():
        compiled[category] = [(re.compile(pattern, re.IGNORECASE), weight) for pattern, weight in patterns]
    return compiled


_COMPILED_PATTERNS = _compile_patterns()


def detect_intent(question: str) -> IntentResult:
    """Detect the primary intent of a question."""
    q_lower = question.lower()
    scores: Dict[IntentCategory, float] = {}
    detected_patterns: Dict[IntentCategory, List[str]] = {}

    for category, patterns in _COMPILED_PATTERNS.items():
        category_score = 0.0
        category_patterns = []
        for pattern, weight in patterns:
            if pattern.search(q_lower):
                category_score += weight
                category_patterns.append(pattern.pattern)
        if category_score > 0:
            scores[category] = category_score
            detected_patterns[category] = category_patterns

    if not scores:
        return IntentResult(
            primary_intent=IntentCategory.UNKNOWN,
            confidence=0.0,
            all_scores={},
            detected_patterns=[],
        )

    # Normalize scores
    max_score = max(scores.values())
    normalized = {cat: score / max_score for cat, score in scores.items()}

    # Get primary intent
    primary = max(normalized, key=normalized.get)
    confidence = normalized[primary]

    return IntentResult(
        primary_intent=primary,
        confidence=confidence,
        all_scores=normalized,
        detected_patterns=detected_patterns.get(primary, []),
    )


def intents_are_compatible(intent1: IntentCategory, intent2: IntentCategory) -> bool:
    """Check if two intents are compatible (could be the same question type)."""
    if intent1 == IntentCategory.UNKNOWN or intent2 == IntentCategory.UNKNOWN:
        return True  # Unknown doesn't conflict
    if intent1 == intent2:
        return True
    return intent2 not in _INTENT_CONFLICTS.get(intent1, set())


def intent_mismatch_penalty(q1: str, q2: str) -> Tuple[float, str]:
    """Compute penalty for intent mismatch between two questions."""
    intent1 = detect_intent(q1)
    intent2 = detect_intent(q2)

    if intent1.primary_intent == IntentCategory.UNKNOWN or intent2.primary_intent == IntentCategory.UNKNOWN:
        return 0.0, "One or both intents unknown"

    if intent1.primary_intent == intent2.primary_intent:
        return 0.0, f"Same intent: {intent1.primary_intent.value}"

    if intents_are_compatible(intent1.primary_intent, intent2.primary_intent):
        return 0.1, f"Compatible intents: {intent1.primary_intent.value} vs {intent2.primary_intent.value}"

    # Conflicting intents - high penalty
    penalty = 0.5
    reason = f"Conflicting intents: {intent1.primary_intent.value} vs {intent2.primary_intent.value}"
    return penalty, reason


def get_intent_details(q1: str, q2: str) -> Dict:
    """Get detailed intent analysis for two questions."""
    i1 = detect_intent(q1)
    i2 = detect_intent(q2)
    penalty, reason = intent_mismatch_penalty(q1, q2)

    return {
        "q1_intent": i1.primary_intent.value,
        "q1_confidence": i1.confidence,
        "q1_patterns": i1.detected_patterns,
        "q1_all_scores": {k.value: v for k, v in i1.all_scores.items()},
        "q2_intent": i2.primary_intent.value,
        "q2_confidence": i2.confidence,
        "q2_patterns": i2.detected_patterns,
        "q2_all_scores": {k.value: v for k, v in i2.all_scores.items()},
        "mismatch_penalty": penalty,
        "mismatch_reason": reason,
        "compatible": intents_are_compatible(i1.primary_intent, i2.primary_intent),
    }