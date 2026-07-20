"""Intelligent Adaptive Ensemble — dynamically weights models based on
input text features detected in each question pair.

Instead of fixed averaging, the ensemble adapts its strategy:
- High lexical overlap → increase TF-IDF weight
- High semantic similarity → increase embedding/transformer weight
- Abbreviations detected → reduce lexical influence, increase semantic
- Synonyms detected → increase semantic influence

Also provides a detailed decision trace for full explainability.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from duplicate_question_app._config.settings import AppPaths, get_app_paths
from duplicate_question_app._ensemble.agreement import analyze_agreement, collect_all_votes

# Common synonyms used for detection (lowercase)
_SYNONYM_PAIRS: list[tuple[str, str]] = [
    ("learn", "study"),
    ("benefits", "advantages"),
    ("tutorial", "guide"),
    ("difference", "distinction"),
    ("how to", "way to"),
    ("how to", "best way"),
    ("what is", "explain"),
    ("what is", "define"),
    ("how does", "explain"),
    ("how do", "how can"),
    ("capital", "largest city"),
    ("meaning", "definition"),
    ("example", "instance"),
    ("implement", "build"),
    ("install", "setup"),
    ("train", "teach"),
]


def _count_lexical_overlap(q1: str, q2: str) -> float:
    """Compute lexical overlap ratio between two questions."""
    t1 = set(q1.lower().split())
    t2 = set(q2.lower().split())
    # Remove very common words
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "to",
        "of",
        "in",
        "for",
        "on",
        "at",
        "by",
        "with",
        "from",
        "and",
        "or",
        "it",
        "i",
    }
    t1 = t1 - stop_words
    t2 = t2 - stop_words
    if not t1 or not t2:
        return 0.0
    intersection = t1 & t2
    union = t1 | t2
    return len(intersection) / len(union) if union else 0.0


def _detect_abbreviations(text: str) -> list[str]:
    """Detect common abbreviations in text (all-caps short tokens)."""
    abbrevs: list[str] = []
    # Common abbreviation patterns: 2-5 uppercase letters
    for token in re.findall(r"\b[A-Z]{2,5}\b", text):
        abbrevs.append(token)
    return abbrevs


def _detect_synonyms(q1: str, q2: str) -> list[str]:
    """Detect if question 1 and question 2 use synonyms for the same concept."""
    q1_lower = q1.lower()
    q2_lower = q2.lower()
    detected: list[str] = []
    for w1, w2 in _SYNONYM_PAIRS:
        in_q1 = w1 in q1_lower or w2 in q1_lower
        in_q2 = w1 in q2_lower or w2 in q2_lower
        if in_q1 and in_q2 and w1 not in q1_lower + q2_lower:
            # Both contain the synonym, but not the same word
            detected.append(f"'{w1}' ↔ '{w2}'")
    return detected


def _detect_semantic_depth(q1: str, q2: str) -> float:
    """Estimate how 'semantic' the match needs to be (0=lexical, 1=fully semantic)."""
    overlap = _count_lexical_overlap(q1, q2)
    abbrevs_q1 = _detect_abbreviations(q1)
    abbrevs_q2 = _detect_abbreviations(q2)
    synonyms = _detect_synonyms(q1, q2)

    # Low overlap + abbreviations or synonyms → high semantic depth needed
    semantic_score = 0.0

    if overlap < 0.3:
        semantic_score += 0.3
    if overlap < 0.1:
        semantic_score += 0.2
    if abbrevs_q1 or abbrevs_q2:
        semantic_score += 0.3
    if synonyms:
        semantic_score += 0.2

    return min(1.0, semantic_score)


@dataclass
class AdaptiveWeights:
    """Dynamic weights assigned to each model group based on input features."""

    lexical_weight: float = 0.15  # TF-IDF models
    transformer_weight: float = 0.25  # DistilBERT models
    embedding_weight: float = 0.35  # BGE, E5, MPNet
    cross_encoder_weight: float = 0.25  # DeBERTa
    semantic_depth: float = 0.0
    lexical_overlap: float = 0.0
    abbreviations_detected: list[str] = field(default_factory=list)
    synonyms_detected: list[str] = field(default_factory=list)


def compute_adaptive_weights(q1: str, q2: str) -> AdaptiveWeights:
    """Compute adaptive weights for the ensemble based on input features."""
    overlap = _count_lexical_overlap(q1, q2)
    abbrevs = _detect_abbreviations(q1) + _detect_abbreviations(q2)
    synonyms = _detect_synonyms(q1, q2)
    semantic_depth = _detect_semantic_depth(q1, q2)

    # Base weights
    lex_w = 0.15
    trans_w = 0.25
    embed_w = 0.35
    cross_w = 0.25

    # Reduce lexical weight if:
    # - Overlap is very low (no lexical signal)
    # - Abbreviations are present (need semantic understanding)
    if overlap < 0.2:
        lex_w *= 0.5
    if abbrevs:
        lex_w *= 0.3
        # Increase semantic models
        embed_w += 0.15
        cross_w += 0.10

    # Boost cross-encoder for high semantic depth
    if semantic_depth > 0.5:
        cross_w += 0.10
        embed_w += 0.10
        trans_w -= 0.05
        lex_w -= 0.05

    # Boost embedding models for synonym detection
    if synonyms:
        embed_w += 0.15
        lex_w -= 0.10

    # Ensure minimum weights and normalize
    lex_w = max(0.05, lex_w)
    trans_w = max(0.10, trans_w)
    embed_w = max(0.10, embed_w)
    cross_w = max(0.10, cross_w)

    total = lex_w + trans_w + embed_w + cross_w
    return AdaptiveWeights(
        lexical_weight=lex_w / total,
        transformer_weight=trans_w / total,
        embedding_weight=embed_w / total,
        cross_encoder_weight=cross_w / total,
        semantic_depth=semantic_depth,
        lexical_overlap=overlap,
        abbreviations_detected=list(set(abbrevs)),
        synonyms_detected=synonyms,
    )


def get_adaptive_ensemble_prediction(
    q1: str,
    q2: str,
    paths: AppPaths | None = None,
) -> dict[str, Any]:
    """Get prediction using the intelligent adaptive ensemble.

    Returns a detailed result dict with:
    - Standard prediction fields
    - Adaptive weights used
    - Per-model contributions
    - Decision trace
    - Feature analysis
    """
    if paths is None:
        from pathlib import Path

        paths = get_app_paths(Path(__file__).resolve().parents[3])

    start_time = time.time()

    # Get all model votes
    votes = collect_all_votes(q1, q2, paths)

    # Compute adaptive weights
    weights = compute_adaptive_weights(q1, q2)

    # Group models and their weights
    model_weights: dict[str, float] = {}

    # Lexical models (Week 2)
    for v in votes:
        if "Week 2" in v.model_name and v.error is None:
            model_weights[v.model_name] = weights.lexical_weight / max(
                1, sum(1 for v2 in votes if "Week 2" in v2.model_name and v2.error is None)
            )

    # Transformer models (Week 3, Week 4)
    for v in votes:
        if "DistilBERT" in v.model_name and v.error is None:
            model_weights[v.model_name] = weights.transformer_weight / max(
                1, sum(1 for v2 in votes if "DistilBERT" in v2.model_name and v2.error is None)
            )

    # Embedding models (BGE, E5, MPNet)
    for v in votes:
        if v.model_name in ("BGE-base-en-v1.5", "E5-base-v2", "MPNet-base-v2") and v.error is None:
            model_weights[v.model_name] = weights.embedding_weight / max(
                1,
                sum(
                    1
                    for v2 in votes
                    if v2.model_name in ("BGE-base-en-v1.5", "E5-base-v2", "MPNet-base-v2") and v2.error is None
                ),
            )

    # Cross-encoder (DeBERTa)
    for v in votes:
        if "DeBERTa" in v.model_name and v.error is None:
            model_weights[v.model_name] = weights.cross_encoder_weight / max(
                1, sum(1 for v2 in votes if "DeBERTa" in v2.model_name and v2.error is None)
            )

    # Compute weighted probability
    weighted_probs: list[float] = []
    model_contributions: dict[str, dict[str, float]] = {}
    for v in votes:
        if v.error is None and v.model_name in model_weights:
            w = model_weights[v.model_name]
            weighted_probs.append(v.prob_duplicate * w)
            model_contributions[v.model_name] = {
                "prob_dup": v.prob_duplicate,
                "prob_duplicate": v.prob_duplicate,
                "weight": w,
                "weighted_contribution": v.prob_duplicate * w,
            }

    ensemble_prob = float(sum(weighted_probs)) if weighted_probs else 0.5
    ensemble_label = 1 if ensemble_prob >= 0.5 else 0
    confidence = max(ensemble_prob, 1.0 - ensemble_prob)

    # Agreement analysis
    agreement = analyze_agreement(votes, q1, q2)

    # Feature analysis
    feature_analysis = {
        "lexical_overlap": weights.lexical_overlap,
        "semantic_depth": weights.semantic_depth,
        "abbreviations": weights.abbreviations_detected,
        "synonyms": weights.synonyms_detected,
        "model_agreement": agreement.agreement_score,
        "is_borderline": agreement.is_borderline,
        "prob_std": agreement.prob_std,
        "unanimous": agreement.unanimous,
    }

    return {
        "question1": q1.strip(),
        "question2": q2.strip(),
        "predicted_label": ensemble_label,
        "prediction": "Duplicate" if ensemble_label == 1 else "Non-Duplicate",
        "prob_duplicate": ensemble_prob,
        "prob_non_duplicate": 1.0 - ensemble_prob,
        "confidence": confidence,
        "threshold": 0.5,
        "model_label": "Semantic Ensemble",
        "model_name": "Semantic Ensemble",
        "device": "cpu",
        "latency_ms": (time.time() - start_time) * 1000,
        "reason": f"Adaptive ensemble weighting {len(model_weights)} models "
        f"(lexical={weights.lexical_weight:.1%}, "
        f"transformer={weights.transformer_weight:.1%}, "
        f"embedding={weights.embedding_weight:.1%}, "
        f"cross-encoder={weights.cross_encoder_weight:.1%})",
        "feature_breakdown": model_contributions,
        "adaptive_weights": {
            "lexical_weight": weights.lexical_weight,
            "transformer_weight": weights.transformer_weight,
            "embedding_weight": weights.embedding_weight,
            "cross_encoder_weight": weights.cross_encoder_weight,
            "semantic_depth": weights.semantic_depth,
            "lexical_overlap": weights.lexical_overlap,
            "abbreviations_detected": weights.abbreviations_detected,
            "synonyms_detected": weights.synonyms_detected,
        },
        "feature_analysis": feature_analysis,
        "models_agreeing": agreement.models_agreeing,
        "models_disagreeing": agreement.models_disagreeing,
    }
