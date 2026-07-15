"""Negation Detection — detects negation words and patterns that flip question meaning.

Detects: not, never, without, remove, disable, uninstall, delete, stop, prevent,
        avoid, disable, turn off, disable, lack of, missing, no, none, nothing,
        neither, nor, cannot, can't, won't, don't, doesn't, didn't, isn't,
        aren't, wasn't, weren't, hasn't, haven't, hadn't, wouldn't, shouldn't,
        couldn't, mustn't, needn't
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Set, Dict, Tuple, Optional
from enum import Enum


class NegationScope(Enum):
    LOCAL = "local"           # Negates single word/phrase
    CLAUSAL = "clausal"       # Negates entire clause
    QUESTION = "question"     # Negates the entire question intent


@dataclass
class NegationMatch:
    """A detected negation in text."""
    text: str
    start: int
    end: int
    negation_type: str
    scope: NegationScope
    confidence: float
    target: Optional[str] = None  # What is being negated


@dataclass
class NegationResult:
    """Result of negation detection for a question pair."""
    q1_negations: List[NegationMatch]
    q2_negations: List[NegationMatch]
    has_negation_mismatch: bool
    mismatch_penalty: float
    details: List[str]


# Explicit negation words
_EXPLICIT_NEGATIONS: Dict[str, float] = {
    "not": 1.0,
    "never": 1.0,
    "no": 0.9,
    "none": 0.9,
    "nothing": 0.9,
    "nobody": 0.8,
    "nowhere": 0.8,
    "neither": 0.9,
    "nor": 0.9,
    "without": 0.95,
    "lack": 0.8,
    "lacking": 0.8,
    "missing": 0.8,
    "absent": 0.8,
    "exclude": 0.85,
    "excluding": 0.85,
    "except": 0.7,
    "excepting": 0.7,
    "but": 0.3,  # Can be negation but often contrast
    "however": 0.2,  # Weak negation signal
}

# Action negation verbs
_ACTION_NEGATIONS: Dict[str, float] = {
    "remove": 0.95,
    "disable": 0.95,
    "uninstall": 0.95,
    "delete": 0.95,
    "stop": 0.9,
    "prevent": 0.95,
    "avoid": 0.9,
    "block": 0.9,
    "deny": 0.9,
    "reject": 0.9,
    "revoke": 0.9,
    "disable": 0.95,
    "turn off": 0.95,
    "switch off": 0.95,
    "shut down": 0.9,
    "terminate": 0.9,
    "kill": 0.9,
    "drop": 0.8,
    "discard": 0.8,
    "ignore": 0.7,
    "skip": 0.7,
    "omit": 0.8,
    "exclude": 0.85,
    "uncheck": 0.9,
    "deselect": 0.9,
    "undo": 0.85,
    "revert": 0.85,
    "rollback": 0.85,
    "uninstall": 0.95,
    "uninstalling": 0.95,
    "removing": 0.95,
    "disabling": 0.95,
    "deleting": 0.95,
    "stopping": 0.9,
    "preventing": 0.95,
    "avoiding": 0.9,
    "blocking": 0.9,
    "denying": 0.9,
    "rejecting": 0.9,
    "revoking": 0.9,
}

# Contraction negations
_CONTRACTION_NEGATIONS: Dict[str, str] = {
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "haven't": "have not",
    "hasn't": "has not",
    "hadn't": "had not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "mustn't": "must not",
    "needn't": "need not",
    "mightn't": "might not",
    "shan't": "shall not",
}

# Prefix negations
_PREFIX_NEGATIONS: Set[str] = {
    "un", "in", "im", "ir", "il", "dis", "non", "anti", "counter",
    "de", "mis", "mal", "a", "an",  # a-/an- as in atypical, amoral
}

# Suffix that might indicate negation
_SUFFIX_NEGATIONS: Set[str] = {
    "less", "free",  # careless, carefree
}


def _compile_negation_patterns() -> List[Tuple[re.Pattern, str, float]]:
    """Compile regex patterns for negation detection."""
    patterns = []

    # Explicit negations (word boundaries)
    for word, conf in _EXPLICIT_NEGATIONS.items():
        patterns.append((re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE), word, conf))

    # Action negations
    for word, conf in _ACTION_NEGATIONS.items():
        patterns.append((re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE), word, conf))

    # Contractions
    for contraction, expansion in _CONTRACTION_NEGATIONS.items():
        patterns.append((re.compile(r"\b" + re.escape(contraction) + r"\b", re.IGNORECASE),
                        contraction, 0.95))

    # Prefix negations (un-, in-, dis-, etc.) - only for known words
    # This is tricky, so we'll use a simpler approach: look for known prefix-negated words
    known_prefix_negated = {
        "unable", "unavailable", "uninstall", "disable", "disconnect",
        "invalid", "incorrect", "impossible", "illegal", "irregular",
        "nonsense", "nonfunctional", "nonworking", "antivirus",
        "counterproductive", "deactivate", "deinstall", "misconfigure",
        "malfunction", "atypical", "amoral", "asymmetric",
    }
    for word in known_prefix_negated:
        patterns.append((re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE), word, 0.8))

    # "not" + verb patterns (clausal negation)
    patterns.append((re.compile(r"\bnot\s+\w+", re.IGNORECASE), "not + verb", 0.9))
    patterns.append((re.compile(r"\bnever\s+\w+", re.IGNORECASE), "never + verb", 0.9))
    patterns.append((re.compile(r"\bwithout\s+\w+", re.IGNORECASE), "without + noun", 0.95))

    return patterns


_COMPILED_NEGATION_PATTERNS = _compile_negation_patterns()


def detect_negations(text: str) -> List[NegationMatch]:
    """Detect all negations in a text."""
    matches = []
    text_lower = text.lower()

    for pattern, neg_type, confidence in _COMPILED_NEGATION_PATTERNS:
        for match in pattern.finditer(text_lower):
            # Determine scope
            scope = NegationScope.LOCAL
            matched_text = match.group()

            # Check if it's a clausal negation (not + verb, never + verb, etc.)
            if " " in matched_text:
                scope = NegationScope.CLAUSAL

            # Check if it's a question-level negation
            # (starts with negation or contains "can I not", "should I not", etc.)
            if match.start() < 20:  # Near beginning
                scope = NegationScope.QUESTION

            # Find target (what is being negated)
            target = _extract_negation_target(text_lower, match.start(), match.end())

            matches.append(NegationMatch(
                text=matched_text,
                start=match.start(),
                end=match.end(),
                negation_type=neg_type,
                scope=scope,
                confidence=confidence,
                target=target,
            ))

    # Sort by position
    matches.sort(key=lambda m: m.start)
    return matches


def _extract_negation_target(text: str, start: int, end: int, window: int = 30) -> Optional[str]:
    """Extract what is being negated (the target word/phrase after negation)."""
    # Look ahead for the next meaningful word
    after = text[end:end + window]
    words = after.split()
    if words:
        # Skip stop words
        stop_words = {"the", "a", "an", "to", "for", "of", "in", "on", "at", "by", "with", "is", "are", "was", "were"}
        for word in words:
            if word not in stop_words and len(word) > 2:
                return word
    return None


def has_negation(text: str) -> bool:
    """Quick check if text contains any negation."""
    return len(detect_negations(text)) > 0


def negation_mismatch(q1: str, q2: str) -> NegationResult:
    """Detect negation mismatch between two questions."""
    q1_negs = detect_negations(q1)
    q2_negs = detect_negations(q2)

    q1_has = len(q1_negs) > 0
    q2_has = len(q2_negs) > 0

    details = []
    penalty = 0.0

    if q1_has != q2_has:
        # One has negation, other doesn't - strong mismatch
        has_neg = "Q1" if q1_has else "Q2"
        no_neg = "Q2" if q1_has else "Q1"
        penalty = 0.6

        neg_words = [n.text for n in (q1_negs if q1_has else q2_negs)]
        details.append(f"{has_neg} has negation ({', '.join(neg_words)}), {no_neg} does not")

    elif q1_has and q2_has:
        # Both have negations - check if they negate different things
        q1_targets = {n.target for n in q1_negs if n.target}
        q2_targets = {n.target for n in q2_negs if n.target}

        if q1_targets and q2_targets and q1_targets != q2_targets:
            # Different targets being negated
            penalty = 0.4
            details.append(f"Different negation targets: Q1={q1_targets}, Q2={q2_targets}")

    # Check for specific action negation mismatches
    q1_action_negs = [n.text for n in q1_negs if n.text in _ACTION_NEGATIONS]
    q2_action_negs = [n.text for n in q2_negs if n.text in _ACTION_NEGATIONS]

    if q1_action_negs and not q2_action_negs:
        penalty = max(penalty, 0.5)
        details.append(f"Q1 has action negation ({q1_action_negs}), Q2 does not")
    elif q2_action_negs and not q1_action_negs:
        penalty = max(penalty, 0.5)
        details.append(f"Q2 has action negation ({q2_action_negs}), Q1 does not")

    # Check for "can I install" vs "can I uninstall" pattern
    q1_lower = q1.lower()
    q2_lower = q2.lower()

    install_q1 = "install" in q1_lower
    install_q2 = "install" in q2_lower
    uninstall_q1 = "uninstall" in q1_lower
    uninstall_q2 = "uninstall" in q2_lower

    if (install_q1 and uninstall_q2) or (uninstall_q1 and install_q2):
        penalty = max(penalty, 0.8)
        details.append("Install/uninstall mismatch detected")

    # Enable/disable
    enable_q1 = "enable" in q1_lower
    enable_q2 = "enable" in q2_lower
    disable_q1 = "disable" in q1_lower
    disable_q2 = "disable" in q2_lower

    if (enable_q1 and disable_q2) or (disable_q1 and enable_q2):
        penalty = max(penalty, 0.8)
        details.append("Enable/disable mismatch detected")

    return NegationResult(
        q1_negations=q1_negs,
        q2_negations=q2_negs,
        has_negation_mismatch=penalty > 0,
        mismatch_penalty=min(0.8, penalty),
        details=details if details else ["No negation mismatch detected"],
    )


def get_negation_penalty(q1: str, q2: str) -> Tuple[float, str]:
    """Get negation penalty for ensemble scoring."""
    result = negation_mismatch(q1, q2)
    if result.has_negation_mismatch:
        return result.mismatch_penalty, "; ".join(result.details)
    return 0.0, "No negation mismatch"