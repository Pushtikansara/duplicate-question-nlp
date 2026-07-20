"""Adaptive Ensemble V2 — Dynamic confidence routing ensemble.

Replaces the simple weighted average with dynamic confidence routing:
- High lexical mismatch → reduce embedding/transformer weights, increase cross-encoder & TF-IDF
- High semantic agreement → increase transformer weights
- Contradiction detected → heavily weight cross-encoder & negation detection
- Entity mismatch → penalize embedding models, boost symbolic models
- Weights computed dynamically per prediction
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.services.cache import cached_preprocessing
from app.services.cache import get_cache as get_global_cache
from duplicate_question_app._config.settings import (
    MODEL_CHOICES,
    AppPaths,
    get_app_paths,
    is_cross_encoder_model,
    is_ensemble_model,
    is_sentence_transformer_model,
)
from duplicate_question_app._ensemble.agreement import collect_all_votes
from duplicate_question_app._ensemble.v1 import compute_adaptive_weights
from duplicate_question_app._linguistics.contradiction import get_contradiction_penalty
from duplicate_question_app._linguistics.entity import get_entity_penalty
from duplicate_question_app._linguistics.intent import intent_mismatch_penalty
from duplicate_question_app._linguistics.lexical import get_lexical_penalty
from duplicate_question_app._linguistics.negation import get_negation_penalty
from duplicate_question_app._models.week2 import is_week2_model


def cached_normalize(text: str, expand_abbrevs: bool = True) -> str:
    from duplicate_question_app._preprocessing import normalize_question

    return cached_preprocessing(
        f"{text}|{expand_abbrevs}",
        lambda: normalize_question(text, expand_abbrevs=expand_abbrevs),
    )


@dataclass
class EnsembleFeatures:
    """Features used for dynamic weight computation."""

    lexical_overlap: float
    semantic_depth: float
    entity_penalty: float
    intent_penalty: float
    negation_penalty: float
    contradiction_penalty: float
    lexical_penalty: float
    abbreviations_detected: list[str]
    synonyms_detected: list[str]
    model_agreement: float
    prob_std: float
    is_borderline: bool


@dataclass
class AdaptiveWeightsV2:
    """Dynamic ensemble weights for each model group."""

    tfidf_weight: float = 0.15
    transformer_weight: float = 0.20
    embedding_weight: float = 0.30
    cross_encoder_weight: float = 0.35

    # Individual model weights (for detailed breakdown)
    individual_weights: dict[str, float] = field(default_factory=dict)

    # Feature values used for weight computation
    features: EnsembleFeatures | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tfidf_weight": self.tfidf_weight,
            "transformer_weight": self.transformer_weight,
            "embedding_weight": self.embedding_weight,
            "cross_encoder_weight": self.cross_encoder_weight,
            "individual_weights": self.individual_weights,
            "features": self.features.__dict__ if self.features else None,
        }


def compute_ensemble_features(
    q1: str,
    q2: str,
    paths: AppPaths,
) -> EnsembleFeatures:
    """Compute all features needed for dynamic weight computation."""

    # Lexical features
    weights = compute_adaptive_weights(q1, q2)

    # Entity mismatch penalty
    entity_penalty, _ = get_entity_penalty(q1, q2)

    # Intent mismatch penalty
    intent_penalty, _ = intent_mismatch_penalty(q1, q2)

    # Negation penalty
    negation_penalty, _ = get_negation_penalty(q1, q2)

    # Contradiction penalty
    contradiction_penalty, _ = get_contradiction_penalty(q1, q2)

    # Lexical penalty
    lexical_penalty, _ = get_lexical_penalty(q1, q2)

    # Model agreement
    votes = collect_all_votes(q1, q2, paths)
    valid_votes = [v for v in votes if v.error is None]
    if valid_votes:
        probs = np.array([v.prob_duplicate for v in valid_votes])
        prob_std = float(probs.std())
        labels = np.array([v.predicted_label for v in valid_votes])
        agreement = float((labels == labels[0]).mean()) if len(labels) > 0 else 0.0
    else:
        prob_std = 0.0
        agreement = 0.0

    is_borderline = abs(np.mean(probs) - 0.5) < 0.15 if valid_votes else False

    return EnsembleFeatures(
        lexical_overlap=weights.lexical_overlap,
        semantic_depth=weights.semantic_depth,
        entity_penalty=entity_penalty,
        intent_penalty=intent_penalty,
        negation_penalty=negation_penalty,
        contradiction_penalty=contradiction_penalty,
        lexical_penalty=lexical_penalty,
        abbreviations_detected=weights.abbreviations_detected,
        synonyms_detected=weights.synonyms_detected,
        model_agreement=agreement,
        prob_std=prob_std,
        is_borderline=is_borderline,
    )


def compute_dynamic_weights(features: EnsembleFeatures) -> AdaptiveWeightsV2:
    """Compute dynamic ensemble weights based on input features."""

    # Base weights
    tfidf_w = 0.15
    trans_w = 0.20
    embed_w = 0.30
    cross_w = 0.35

    # ============================================================
    # RULE 1: High lexical mismatch → reduce embedding/transformer
    # ============================================================
    if features.lexical_overlap < 0.2:
        # Very low lexical overlap - embeddings may hallucinate similarity
        embed_w *= 0.5
        trans_w *= 0.7
        # Boost cross-encoder (understands context better)
        cross_w *= 1.3
        tfidf_w *= 0.8
    elif features.lexical_overlap < 0.4:
        embed_w *= 0.8
        trans_w *= 0.9
        cross_w *= 1.1
        tfidf_w *= 0.9

    # ============================================================
    # RULE 2: High semantic depth needed → boost semantic models
    # ============================================================
    if features.semantic_depth > 0.6:
        embed_w += 0.1
        cross_w += 0.1
        trans_w -= 0.05
        tfidf_w -= 0.05
    elif features.semantic_depth > 0.4:
        embed_w += 0.05
        cross_w += 0.05

    # ============================================================
    # RULE 3: Entity mismatch → penalize embeddings, boost symbolic
    # ============================================================
    if features.entity_penalty > 0.3:
        embed_w *= 0.5
        cross_w *= 0.8
        tfidf_w *= 1.2
        trans_w *= 1.1
    elif features.entity_penalty > 0.1:
        embed_w *= 0.8
        tfidf_w *= 1.1

    # ============================================================
    # RULE 4: Intent mismatch → heavy penalty on all semantic models
    # ============================================================
    if features.intent_penalty > 0.3:
        embed_w *= 0.4
        cross_w *= 0.6
        trans_w *= 0.7
        tfidf_w *= 1.3
    elif features.intent_penalty > 0.1:
        embed_w *= 0.7
        cross_w *= 0.8
        tfidf_w *= 1.2

    # ============================================================
    # RULE 5: Negation mismatch → strong penalty on embeddings
    # ============================================================
    if features.negation_penalty > 0.4:
        embed_w *= 0.3
        cross_w *= 0.7
        trans_w *= 0.8
        tfidf_w *= 1.2
    elif features.negation_penalty > 0.1:
        embed_w *= 0.6
        cross_w *= 0.8
        tfidf_w *= 1.1

    # ============================================================
    # RULE 6: Contradiction detected → cross-encoder is king
    # ============================================================
    if features.contradiction_penalty > 0.4:
        cross_w *= 2.0
        embed_w *= 0.3
        trans_w *= 0.5
        tfidf_w *= 0.8
    elif features.contradiction_penalty > 0.2:
        cross_w *= 1.5
        embed_w *= 0.6
        trans_w *= 0.7
        tfidf_w *= 0.9

    # ============================================================
    # RULE 7: Low model agreement → boost cross-encoder
    # ============================================================
    if features.model_agreement < 0.5:
        cross_w *= 1.4
        embed_w *= 0.8
        trans_w *= 0.9
    elif features.model_agreement < 0.7:
        cross_w *= 1.2
        embed_w *= 0.9

    # ============================================================
    # RULE 8: Borderline predictions → more conservative weights
    # ============================================================
    if features.is_borderline:
        # Don't over-confident any model
        cross_w *= 0.9
        embed_w *= 0.9
        trans_w *= 1.0
        tfidf_w *= 1.1

    # ============================================================
    # RULE 9: Abbreviations detected → boost semantic models
    # ============================================================
    if features.abbreviations_detected:
        embed_w += 0.1
        cross_w += 0.05
        tfidf_w -= 0.1
        trans_w -= 0.05

    # ============================================================
    # RULE 10: Synonyms detected → boost embeddings
    # ============================================================
    if features.synonyms_detected:
        embed_w += 0.1
        cross_w += 0.05
        tfidf_w -= 0.1

    # Apply minimums and normalize
    tfidf_w = max(0.05, tfidf_w)
    trans_w = max(0.08, trans_w)
    embed_w = max(0.08, embed_w)
    cross_w = max(0.10, cross_w)

    total = tfidf_w + trans_w + embed_w + cross_w

    return AdaptiveWeightsV2(
        tfidf_weight=tfidf_w / total,
        transformer_weight=trans_w / total,
        embedding_weight=embed_w / total,
        cross_encoder_weight=cross_w / total,
        features=features,
    )


def get_model_predictions_batch(
    q1: str,
    q2: str,
    paths: AppPaths,
) -> dict[str, tuple[int, float]]:
    """Get predictions from all models, delegating to collect_all_votes()."""
    votes = collect_all_votes(q1, q2, paths)
    return {v.model_name: (v.predicted_label, v.prob_duplicate) for v in votes if v.error is None}


def adaptive_ensemble_predict(
    q1: str,
    q2: str,
    paths: AppPaths | None = None,
) -> dict[str, Any]:
    """Main entry point for Adaptive Ensemble V2 prediction."""
    start_time = time.time()

    if paths is None:
        paths = get_app_paths()

    # Compute features
    features = compute_ensemble_features(q1, q2, paths)

    # Compute dynamic weights
    weights = compute_dynamic_weights(features)

    # Get all model predictions
    predictions = get_model_predictions_batch(q1, q2, paths)

    # Group predictions by model type — built dynamically from MODEL_CHOICES
    tfidf_models: dict[str, float] = {}
    transformer_models: dict[str, float] = {}
    embedding_models: dict[str, float] = {}
    cross_encoder_models: dict[str, float] = {}
    for m_name in MODEL_CHOICES:
        if is_week2_model(m_name) and not is_ensemble_model(m_name):
            tfidf_models[m_name] = 0.0
        elif is_sentence_transformer_model(m_name) and not is_ensemble_model(m_name):
            embedding_models[m_name] = 0.0
        elif is_cross_encoder_model(m_name) and not is_ensemble_model(m_name):
            cross_encoder_models[m_name] = 0.0
        elif not is_ensemble_model(m_name):
            transformer_models[m_name] = 0.0

    # Fill in predictions
    for model_name, (_label, prob) in predictions.items():
        if model_name in tfidf_models:
            tfidf_models[model_name] = prob
        elif model_name in transformer_models:
            transformer_models[model_name] = prob
        elif model_name in embedding_models:
            embedding_models[model_name] = prob
        elif model_name in cross_encoder_models:
            cross_encoder_models[model_name] = prob

    # Compute weighted averages per group
    def weighted_avg(probs_dict: dict[str, float], weight: float) -> tuple[float, dict[str, float]]:
        valid = {k: v for k, v in probs_dict.items() if v > 0}
        if not valid:
            return 0.5, {}
        avg = np.mean(list(valid.values()))
        # Distribute group weight equally among models in group
        per_model_weight = weight / len(valid) if valid else 0
        contributions = {k: v * per_model_weight for k, v in valid.items()}
        return avg, contributions

    tfidf_avg, tfidf_contrib = weighted_avg(tfidf_models, weights.tfidf_weight)
    trans_avg, trans_contrib = weighted_avg(transformer_models, weights.transformer_weight)
    embed_avg, embed_contrib = weighted_avg(embedding_models, weights.embedding_weight)
    cross_avg, cross_contrib = weighted_avg(cross_encoder_models, weights.cross_encoder_weight)

    # Combine
    ensemble_prob = (
        tfidf_avg * weights.tfidf_weight
        + trans_avg * weights.transformer_weight
        + embed_avg * weights.embedding_weight
        + cross_avg * weights.cross_encoder_weight
    )

    # Apply penalties
    total_penalty = (
        features.entity_penalty * 0.5
        + features.intent_penalty * 0.5
        + features.negation_penalty * 0.6
        + features.contradiction_penalty * 0.8
        + features.lexical_penalty * 0.4
    )

    # Penalties reduce duplicate probability
    if total_penalty > 0:
        ensemble_prob = ensemble_prob * (1.0 - min(0.7, total_penalty))

    ensemble_label = 1 if ensemble_prob >= 0.5 else 0
    confidence = max(ensemble_prob, 1.0 - ensemble_prob)

    # Combine all contributions
    all_contributions = {}
    all_contributions.update(tfidf_contrib)
    all_contributions.update(trans_contrib)
    all_contributions.update(embed_contrib)
    all_contributions.update(cross_contrib)

    latency_ms = (time.time() - start_time) * 1000

    return {
        "question1": q1,
        "question2": q2,
        "predicted_label": ensemble_label,
        "prediction": "Duplicate" if ensemble_label == 1 else "Non-Duplicate",
        "prob_duplicate": float(ensemble_prob),
        "prob_non_duplicate": float(1.0 - ensemble_prob),
        "confidence": float(confidence),
        "threshold": 0.5,
        "model_label": "Adaptive Ensemble V2",
        "model_name": "Adaptive Ensemble V2",
        "device": "cpu",
        "latency_ms": latency_ms,
        "reason": (
            f"Dynamic weights: TF-IDF={weights.tfidf_weight:.1%}, "
            f"Transformer={weights.transformer_weight:.1%}, "
            f"Embedding={weights.embedding_weight:.1%}, "
            f"Cross-Encoder={weights.cross_encoder_weight:.1%} | "
            f"Penalties: entity={features.entity_penalty:.2f}, "
            f"intent={features.intent_penalty:.2f}, "
            f"negation={features.negation_penalty:.2f}, "
            f"contradiction={features.contradiction_penalty:.2f}, "
            f"lexical={features.lexical_penalty:.2f}"
        ),
        "feature_breakdown": all_contributions,
        "adaptive_weights": weights.to_dict(),
        "features": {
            "lexical_overlap": features.lexical_overlap,
            "semantic_depth": features.semantic_depth,
            "entity_penalty": features.entity_penalty,
            "intent_penalty": features.intent_penalty,
            "negation_penalty": features.negation_penalty,
            "contradiction_penalty": features.contradiction_penalty,
            "lexical_penalty": features.lexical_penalty,
            "model_agreement": features.model_agreement,
            "prob_std": features.prob_std,
            "is_borderline": features.is_borderline,
        },
    }


def clear_caches():
    get_global_cache().clear_all()


def get_cache_stats() -> dict[str, int]:
    stats = get_global_cache().stats()
    return {
        "embedding_cache_size": stats["embedding"].size,
        "preprocessing_cache_size": stats["preprocessing"].size,
    }
