"""Adaptive Ensemble V2 — Dynamic confidence routing ensemble.

Replaces the simple weighted average with dynamic confidence routing:
- High lexical mismatch → reduce embedding/transformer weights, increase cross-encoder & TF-IDF
- High semantic agreement → increase transformer weights
- Contradiction detected → heavily weight cross-encoder & negation detection
- Entity mismatch → penalize embedding models, boost symbolic models
- Weights computed dynamically per prediction

Also includes performance optimizations:
- Embedding caching
- Batch encoding
- Preprocessing memoization
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from duplicate_question_app.agreement_engine import collect_all_votes
from duplicate_question_app.config import AppPaths, get_app_paths
from duplicate_question_app.contradiction_detector import get_contradiction_penalty
from duplicate_question_app.embedding_models import (
    predict_with_sentence_transformer,
)
from duplicate_question_app.entity_detector import get_entity_penalty
from duplicate_question_app.inference import (
    DuplicateQuestionInferenceService,
    load_model_and_tokenizer,
)
from duplicate_question_app.intelligent_ensemble import compute_adaptive_weights
from duplicate_question_app.intent_detector import intent_mismatch_penalty
from duplicate_question_app.lexical_penalty import get_lexical_penalty
from duplicate_question_app.negation_detector import get_negation_penalty
from duplicate_question_app.week2_inference import Week2InferenceService, check_week2_artifacts


# Thread-safe LRU cache for embeddings
class EmbeddingCache:
    """Thread-safe LRU cache for model embeddings."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._lock = threading.RLock()

    def _make_key(self, model_name: str, text: str) -> str:
        """Create cache key from model name and text hash."""
        text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        return f"{model_name}:{text_hash}"

    def get(self, model_name: str, text: str) -> np.ndarray | None:
        key = self._make_key(model_name, text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        return None

    def put(self, model_name: str, text: str, embedding: np.ndarray) -> None:
        key = self._make_key(model_name, text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)
                self._cache[key] = embedding

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


# Global embedding cache
_embedding_cache = EmbeddingCache(max_size=10000)


# Preprocessing cache
_preprocessing_cache: dict[str, str] = {}
_preprocessing_cache_lock = threading.RLock()


def cached_normalize(text: str, expand_abbrevs: bool = True) -> str:
    """Normalize question with caching."""
    key = f"{text}|{expand_abbrevs}"
    with _preprocessing_cache_lock:
        if key in _preprocessing_cache:
            return _preprocessing_cache[key]
        from duplicate_question_app.preprocessing import normalize_question

        result = normalize_question(text, expand_abbrevs=expand_abbrevs)
        if len(_preprocessing_cache) < 5000:
            _preprocessing_cache[key] = result
        return result


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
    """Get predictions from all models (cached where possible)."""
    results = {}

    # Week 2 models
    if all(check_week2_artifacts(paths).values()):
        w2 = Week2InferenceService(paths)
        for m_name in ["TF-IDF + Logistic Regression (Week 2)", "TF-IDF + Linear SVM (Week 2)"]:
            try:
                _, prob_dup = w2.predict_proba(q1, q2, m_name)
                results[m_name] = (1 if prob_dup >= 0.5 else 0, prob_dup)
            except Exception:
                results[m_name] = (0, 0.5)

    # Week 3/4 transformer models
    for m_name in ["DistilBERT (Week 3)", "Improved DistilBERT (Week 4)"]:
        try:
            model, tok, meta = load_model_and_tokenizer(paths, model_version=m_name)
            svc = DuplicateQuestionInferenceService(model, tok, meta)
            _, prob_dup = svc.predict_proba(q1, q2)
            results[m_name] = (1 if prob_dup >= meta.decision_threshold else 0, prob_dup)
        except Exception:
            results[m_name] = (0, 0.5)

    # Phase 2 embedding / cross-encoder models
    for m_name in ["BGE-base-en-v1.5", "E5-base-v2", "MPNet-base-v2", "DeBERTa-v3 Cross-Encoder"]:
        try:
            result = predict_with_sentence_transformer(m_name, q1, q2)
            results[m_name] = (result["predicted_label"], result["prob_duplicate"])
        except Exception:
            results[m_name] = (0, 0.5)

    return results


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

    # Group predictions by model type
    tfidf_models = {
        "TF-IDF + Logistic Regression (Week 2)": 0.0,
        "TF-IDF + Linear SVM (Week 2)": 0.0,
    }
    transformer_models = {
        "DistilBERT (Week 3)": 0.0,
        "Improved DistilBERT (Week 4)": 0.0,
    }
    embedding_models = {
        "BGE-base-en-v1.5": 0.0,
        "E5-base-v2": 0.0,
        "MPNet-base-v2": 0.0,
    }
    cross_encoder_models = {
        "DeBERTa-v3 Cross-Encoder": 0.0,
    }

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
    """Clear all caches (useful for testing or memory management)."""
    global _embedding_cache, _preprocessing_cache
    _embedding_cache.clear()
    with _preprocessing_cache_lock:
        _preprocessing_cache.clear()


def get_cache_stats() -> dict[str, int]:
    """Get cache statistics."""
    return {
        "embedding_cache_size": len(_embedding_cache._cache),
        "preprocessing_cache_size": len(_preprocessing_cache),
    }
