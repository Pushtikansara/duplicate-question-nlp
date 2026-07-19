"""Contradiction Detection — detects when two questions contain opposite meanings.

Uses NLI (Natural Language Inference) patterns and semantic analysis to
identify contradictions that should result in Non-Duplicate predictions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set, Optional
from enum import Enum

# Try to import cross-encoder for NLI-based contradiction detection
try:
    from sentence_transformers import CrossEncoder
    _CROSSENCODER_AVAILABLE = True
except ImportError:
    _CROSSENCODER_AVAILABLE = False


class ContradictionType(Enum):
    DIRECT_NEGATION = "direct_negation"           # "Can I install X?" vs "Can I uninstall X?"
    OPPOSITE_ACTION = "opposite_action"           # "Enable X" vs "Disable X"
    OPPOSITE_INTENT = "opposite_intent"           # "How to install" vs "How to uninstall"
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"     # "Is X free?" vs "How much does X cost?"
    TEMPORAL_CONTRADICTION = "temporal_contradiction"  # "Before X" vs "After X"
    CONDITIONAL_CONTRADICTION = "conditional_contradiction"  # "If X then Y" vs "If X then not Y"


@dataclass
class ContradictionResult:
    """Result of contradiction detection between two questions."""
    has_contradiction: bool
    contradiction_score: float  # 0-1, higher = more contradictory
    contradiction_types: List[ContradictionType]
    details: str
    nli_scores: Optional[Dict[str, float]] = None  # contradiction, neutral, entailment


# Opposite action verb pairs
_OPPOSITE_VERBS: Dict[str, str] = {
    "install": "uninstall",
    "enable": "disable",
    "activate": "deactivate",
    "start": "stop",
    "begin": "end",
    "open": "close",
    "create": "delete",
    "add": "remove",
    "insert": "delete",
    "connect": "disconnect",
    "link": "unlink",
    "attach": "detach",
    "mount": "unmount",
    "load": "unload",
    "import": "export",
    "upload": "download",
    "push": "pull",
    "commit": "revert",
    "apply": "revert",
    "enable": "disable",
    "allow": "deny",
    "grant": "revoke",
    "include": "exclude",
    "accept": "reject",
    "approve": "deny",
    "pass": "fail",
    "succeed": "fail",
    "work": "break",
    "fix": "break",
    "repair": "damage",
    "build": "destroy",
    "compile": "decompile",
    "encrypt": "decrypt",
    "encode": "decode",
    "compress": "decompress",
    "pack": "unpack",
    "zip": "unzip",
    "lock": "unlock",
    "sign": "verify",
    "generate": "consume",
    "produce": "consume",
    "write": "read",
    "send": "receive",
    "transmit": "receive",
    "publish": "subscribe",
    "subscribe": "unsubscribe",
    "join": "leave",
    "enter": "exit",
    "login": "logout",
    "signin": "signout",
    "register": "unregister",
    "subscribe": "unsubscribe",
    "follow": "unfollow",
    "like": "dislike",
    "upvote": "downvote",
    "agree": "disagree",
    "confirm": "deny",
    "verify": "refute",
    "prove": "disprove",
    "validate": "invalidate",
    "authorize": "unauthorize",
    "authenticate": "deauthenticate",
}


# Opposite adjective pairs
_OPPOSITE_ADJECTIVES: Dict[str, str] = {
    "free": "paid",
    "open": "closed",
    "public": "private",
    "enabled": "disabled",
    "active": "inactive",
    "running": "stopped",
    "working": "broken",
    "valid": "invalid",
    "true": "false",
    "yes": "no",
    "on": "off",
    "online": "offline",
    "connected": "disconnected",
    "available": "unavailable",
    "supported": "unsupported",
    "compatible": "incompatible",
    "allowed": "forbidden",
    "permitted": "prohibited",
    "legal": "illegal",
    "correct": "incorrect",
    "right": "wrong",
    "good": "bad",
    "better": "worse",
    "best": "worst",
    "fast": "slow",
    "quick": "slow",
    "easy": "hard",
    "simple": "complex",
    "basic": "advanced",
    "old": "new",
    "latest": "oldest",
    "first": "last",
    "before": "after",
    "earlier": "later",
    "previous": "next",
    "initial": "final",
    "start": "end",
    "beginning": "end",
    "minimum": "maximum",
    "min": "max",
    "small": "large",
    "little": "big",
    "short": "long",
    "few": "many",
    "less": "more",
    "lower": "higher",
    "decrease": "increase",
    "reduce": "increase",
    "shrink": "grow",
}


# Mutually exclusive concepts
_MUTUALLY_EXCLUSIVE: List[Tuple[Set[str], Set[str]]] = [
    ({"free", "gratis", "no cost", "zero cost"}, {"paid", "cost", "price", "buy", "purchase", "subscription", "license fee"}),
    ({"open source", "oss", "free software"}, {"proprietary", "closed source", "commercial license"}),
    ({"python 2", "py2"}, {"python 3", "py3"}),
    ({"windows", "win32", "win64"}, {"linux", "unix", "macos", "mac os", "osx"}),
    ({"cpu", "processor"}, {"gpu", "graphics card"}),
    ({"sql", "relational"}, {"nosql", "non-relational", "document db"}),
    ({"sync", "synchronous"}, {"async", "asynchronous"}),
    ({"blocking", "blocking call"}, {"non-blocking", "non blocking"}),
    ({"compile time", "static"}, {"runtime", "dynamic"}),
    ({"client", "frontend"}, {"server", "backend"}),
    ({"http", "rest"}, {"grpc", "graphql", "websocket"}),
    ({"32 bit", "x86"}, {"64 bit", "x64", "arm64"}),
    ({"dev", "development"}, {"prod", "production"}),
    ({"debug", "debugging"}, {"release", "optimized"}),
]


# Temporal contradiction patterns
_TEMPORAL_PATTERNS: List[Tuple[str, str]] = [
    (r"\bbefore\b", r"\bafter\b"),
    (r"\bearlier\b", r"\blater\b"),
    (r"\bprevious\b", r"\bnext\b"),
    (r"\bprior\b", r"\bfollowing\b"),
    (r"\bfirst\b", r"\blast\b"),
    (r"\bstart\b", r"\bend\b"),
    (r"\bbegin\b", r"\bfinish\b"),
    (r"\binitial\b", r"\bfinal\b"),
]


# NLI Cross-encoder for contradiction detection (lazy loaded)
_nli_model = None


def _get_nli_model():
    """Lazy load the NLI cross-encoder model."""
    global _nli_model
    if _nli_model is None and _CROSSENCODER_AVAILABLE:
        try:
            _nli_model = CrossEncoder("cross-encoder/nli-deberta-v3-base", device="cpu")
        except Exception:
            _nli_model = "error"
    return _nli_model if _nli_model != "error" else None


def _normalize_for_comparison(text: str) -> str:
    """Normalize text for pattern matching."""
    text = text.lower()
    # Expand common contractions
    text = re.sub(r"\bcan't\b", "cannot", text)
    text = re.sub(r"\bwon't\b", "will not", text)
    text = re.sub(r"\bn't\b", " not", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _find_opposite_verbs(text1: str, text2: str) -> List[str]:
    """Find opposite verb pairs between two texts."""
    opposites = []
    words1 = set(text1.split())
    words2 = set(text2.split())

    for verb, opposite in _OPPOSITE_VERBS.items():
        if verb in words1 and opposite in words2:
            opposites.append(f"{verb} ↔ {opposite}")
        elif opposite in words1 and verb in words2:
            opposites.append(f"{opposite} ↔ {verb}")

    return opposites


def _find_opposite_adjectives(text1: str, text2: str) -> List[str]:
    """Find opposite adjective pairs between two texts."""
    opposites = []
    words1 = set(text1.split())
    words2 = set(text2.split())

    for adj, opposite in _OPPOSITE_ADJECTIVES.items():
        if adj in words1 and opposite in words2:
            opposites.append(f"{adj} ↔ {opposite}")
        elif opposite in words1 and adj in words2:
            opposites.append(f"{opposite} ↔ {adj}")

    return opposites


def _check_mutually_exclusive(text1: str, text2: str) -> List[str]:
    """Check for mutually exclusive concepts."""
    conflicts = []
    words1 = set(text1.split())
    words2 = set(text2.split())

    for set1, set2 in _MUTUALLY_EXCLUSIVE:
        if words1 & set1 and words2 & set2:
            conflicts.append(f"Mutually exclusive: {words1 & set1} vs {words2 & set2}")
        elif words2 & set1 and words1 & set2:
            conflicts.append(f"Mutually exclusive: {words2 & set1} vs {words1 & set2}")

    return conflicts


def _check_temporal_contradiction(text1: str, text2: str) -> List[str]:
    """Check for temporal contradictions."""
    conflicts = []
    for pattern1, pattern2 in _TEMPORAL_PATTERNS:
        if re.search(pattern1, text1) and re.search(pattern2, text2):
            conflicts.append(f"Temporal: '{pattern1}' vs '{pattern2}'")
        elif re.search(pattern2, text1) and re.search(pattern1, text2):
            conflicts.append(f"Temporal: '{pattern2}' vs '{pattern1}'")
    return conflicts


def _check_direct_negation(text1: str, text2: str) -> List[str]:
    """Check for direct negation patterns (install vs uninstall, etc.)."""
    conflicts = []

    # Check for install/uninstall patterns
    install_patterns = [
        (r"\binstall\b", r"\buninstall\b"),
        (r"\benable\b", r"\bdisable\b"),
        (r"\bactivate\b", r"\bdeactivate\b"),
        (r"\bstart\b", r"\bstop\b"),
        (r"\bturn\s+on\b", r"\bturn\s+off\b"),
        (r"\bconnect\b", r"\bdisconnect\b"),
        (r"\ballow\b", r"\bdeny\b"),
        (r"\bgrant\b", r"\brevoke\b"),
        (r"\badd\b", r"\bremove\b"),
        (r"\bcreate\b", r"\bdelete\b"),
        (r"\bmake\b", r"\bdestroy\b"),
        (r"\bbuild\b", r"\bdestroy\b"),
    ]

    for pos, neg in install_patterns:
        if re.search(pos, text1) and re.search(neg, text2):
            conflicts.append(f"Direct opposite: {pos} vs {neg}")
        elif re.search(neg, text1) and re.search(pos, text2):
            conflicts.append(f"Direct opposite: {neg} vs {pos}")

    return conflicts


def detect_contradiction_patterns(q1: str, q2: str) -> Tuple[float, List[ContradictionType], List[str]]:
    """Detect contradictions using pattern matching."""
    t1 = _normalize_for_comparison(q1)
    t2 = _normalize_for_comparison(q2)

    all_conflicts = []
    contradiction_types = []

    # Direct negation / opposite actions
    direct_conflicts = _check_direct_negation(t1, t2)
    if direct_conflicts:
        all_conflicts.extend(direct_conflicts)
        contradiction_types.append(ContradictionType.DIRECT_NEGATION)
        contradiction_types.append(ContradictionType.OPPOSITE_ACTION)

    # Opposite verbs
    verb_conflicts = _find_opposite_verbs(t1, t2)
    if verb_conflicts:
        all_conflicts.extend([f"Opposite verbs: {v}" for v in verb_conflicts])
        contradiction_types.append(ContradictionType.OPPOSITE_ACTION)

    # Opposite adjectives
    adj_conflicts = _find_opposite_adjectives(t1, t2)
    if adj_conflicts:
        all_conflicts.extend([f"Opposite adjectives: {a}" for a in adj_conflicts])
        contradiction_types.append(ContradictionType.OPPOSITE_ACTION)

    # Mutually exclusive
    mutex_conflicts = _check_mutually_exclusive(t1, t2)
    if mutex_conflicts:
        all_conflicts.extend(mutex_conflicts)
        contradiction_types.append(ContradictionType.MUTUALLY_EXCLUSIVE)

    # Temporal
    temp_conflicts = _check_temporal_contradiction(t1, t2)
    if temp_conflicts:
        all_conflicts.extend(temp_conflicts)
        contradiction_types.append(ContradictionType.TEMPORAL_CONTRADICTION)

    # Score based on number and type of conflicts
    score = 0.0
    if direct_conflicts:
        score += 0.5 * len(direct_conflicts)
    if verb_conflicts:
        score += 0.3 * len(verb_conflicts)
    if adj_conflicts:
        score += 0.2 * len(adj_conflicts)
    if mutex_conflicts:
        score += 0.4 * len(mutex_conflicts)
    if temp_conflicts:
        score += 0.3 * len(temp_conflicts)

    score = min(1.0, score)

    return score, list(set(contradiction_types)), all_conflicts


def detect_contradiction_nli(q1: str, q2: str) -> Optional[Dict[str, float]]:
    """Use NLI cross-encoder to detect contradiction."""
    model = _get_nli_model()
    if model is None:
        return None

    try:
        # NLI models expect premise, hypothesis
        # For contradiction detection, we check both directions
        scores_12 = model.predict([(q1, q2)], apply_softmax=True)[0]
        scores_21 = model.predict([(q2, q1)], apply_softmax=True)[0]

        # NLI labels: [contradiction, neutral, entailment]
        contra_12 = float(scores_12[0])
        contra_21 = float(scores_21[0])

        return {
            "contradiction": max(contra_12, contra_21),
            "neutral": (float(scores_12[1]) + float(scores_21[1])) / 2,
            "entailment": (float(scores_12[2]) + float(scores_21[2])) / 2,
        }
    except Exception:
        return None


def detect_contradiction(q1: str, q2: str) -> ContradictionResult:
    """Main entry point: detect contradiction between two questions."""
    # Pattern-based detection
    pattern_score, pattern_types, pattern_details = detect_contradiction_patterns(q1, q2)

    # NLI-based detection
    nli_scores = detect_contradiction_nli(q1, q2)

    # Combine scores
    final_score = pattern_score
    final_types = pattern_types
    all_details = pattern_details.copy()

    if nli_scores:
        nli_contra = nli_scores["contradiction"]
        # Weight NLI contradiction score
        final_score = max(final_score, nli_contra * 0.8)
        if nli_contra > 0.5:
            if ContradictionType.DIRECT_NEGATION not in final_types:
                final_types.append(ContradictionType.DIRECT_NEGATION)
            all_details.append(f"NLI contradiction score: {nli_contra:.2f}")

    has_contradiction = final_score > 0.3

    return ContradictionResult(
        has_contradiction=has_contradiction,
        contradiction_score=final_score,
        contradiction_types=final_types,
        details="; ".join(all_details) if all_details else "No contradiction detected",
        nli_scores=nli_scores,
    )


def get_contradiction_penalty(q1: str, q2: str) -> Tuple[float, str]:
    """Get contradiction penalty for ensemble."""
    result = detect_contradiction(q1, q2)
    if result.has_contradiction:
        # High penalty for contradictions
        penalty = min(0.7, result.contradiction_score * 1.2)
        return penalty, result.details
    return 0.0, "No contradiction"