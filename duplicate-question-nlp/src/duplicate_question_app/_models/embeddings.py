"""Embedding model inference for Phase 2 models (BGE, E5, MPNet, DeBERTa, Ensemble)."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app.config import is_cross_encoder_model, get_app_paths, is_finetuned_embedding_model, get_config

_logger = get_logger(__name__)
from duplicate_question_app.preprocessing import normalize_question
from duplicate_question_app.week2_inference import Week2InferenceService, check_week2_artifacts, is_week2_model

_sentence_transformer_cache: dict[str, Any] = {}
PATHS = None


def get_paths(project_root=None):
    global PATHS
    if PATHS is None:
        from pathlib import Path
        if project_root is None:
            project_root = Path(__file__).resolve().parents[2]
        PATHS = get_app_paths(project_root)
    return PATHS


def _resolve_device() -> str:
    """Auto-detect: use CUDA if available, else CPU."""
    inf_cfg = get_config("inference") or {}
    if not inf_cfg.get("auto_device", True):
        return inf_cfg.get("default_device", "cpu")
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def resolve_best_available_e5_model(model_name: str) -> str:
    """Auto-upgrade E5 to the best available variant.

    If model_name contains 'E5-base-v2' or 'e5' and the fine-tuned
    model exists on disk, we resolve to the fine-tuned variant, which
    gives significantly better accuracy. Falls back gracefully.
    """
    if "e5" not in model_name.lower():
        return model_name
    # Check for fine-tuned model
    paths = get_paths()
    ft_path = paths.finetuned_e5_dir
    if ft_path.exists() and (ft_path / "model.safetensors").exists():
        if model_name in ("E5-base-v2", "E5-base-v2+LR", "E5-base-v2+MLP"):
            return "E5-quora-finetuned"
    # Check for LR head
    lr_path = paths.models_dir / "e5_base_v2_lr_head.pkl"
    if lr_path.exists():
        return model_name  # LR head will be used separately
    return model_name


def get_sentence_transformer_model(model_name: str) -> Any:
    """Load a sentence-transformers model, with caching (GPU if available).

    Supports:
    - Original frozen models (BGE, E5, MPNet)
    - Fine-tuned models (E5-quora-finetuned, BGE-quora-finetuned)
    - Cross-encoder models (DeBERTa-v3)
    """
    global _sentence_transformer_cache
    if model_name not in _sentence_transformer_cache:
        from sentence_transformers import SentenceTransformer, CrossEncoder
        device = _resolve_device()

        hubs = get_config("models").get("hub_names", {})
        if is_cross_encoder_model(model_name):
            paths = get_paths()
            model_key = {
                "DeBERTa-v3 Cross-Encoder": hubs.get("DeBERTa-v3-Cross-Encoder", "cross-encoder/nli-deberta-v3-base"),
                "Cross-Encoder-Quora (Trained)": str(paths.finetuned_cross_encoder_dir),
            }.get(model_name, "cross-encoder/nli-deberta-v3-base")
            # Validate local path before loading
            if model_name == "Cross-Encoder-Quora (Trained)":
                model_path_obj = Path(model_key)
                if not model_path_obj.exists() or not (model_path_obj / "config.json").exists():
                    raise FileNotFoundError(
                        f"Trained cross-encoder not found at {model_key}. "
                        f"Run scripts/train_cross_encoder.py first."
                    )
            _sentence_transformer_cache[model_name] = CrossEncoder(model_key, device=device)
        elif is_finetuned_embedding_model(model_name):
            # Load fine-tuned model from local path
            paths = get_paths()
            model_key = {
                "E5-quora-finetuned": str(paths.finetuned_e5_dir),
                "BGE-quora-finetuned": str(paths.finetuned_bge_dir),
            }.get(model_name)
            if not model_key or not Path(model_key).exists():
                raise FileNotFoundError(
                    f"Fine-tuned model '{model_name}' not found at {model_key}. "
                    f"Run scripts/train_e5_quora.py first."
                )
            _logger.info("Loading fine-tuned model from %s", model_key)
            _sentence_transformer_cache[model_name] = SentenceTransformer(model_key, device=device)
        else:
            hubs = get_config("models").get("hub_names", {})
            model_key = {
                "BGE-base-en-v1.5": hubs.get("BGE-base-en-v1.5", "BAAI/bge-base-en-v1.5"),
                "E5-base-v2": hubs.get("E5-base-v2", "intfloat/e5-base-v2"),
                "MPNet-base-v2": hubs.get("MPNet-base-v2", "sentence-transformers/all-mpnet-base-v2"),
            }.get(model_name, hubs.get("MPNet-base-v2", "sentence-transformers/all-mpnet-base-v2"))
            _sentence_transformer_cache[model_name] = SentenceTransformer(model_key, device=device)
    return _sentence_transformer_cache[model_name]


def _get_sigmoid_params(model_name: str) -> tuple[float, float]:
    """Return (steepness, midpoint) for sigmoid calibration.

    Values from configs/inference.yaml (per-model sigmoid_params).
    Learned via Platt scaling on held-out validation data.
    Fine-tuned models use different params as their similarity distributions
    shift after contrastive fine-tuning.
    """
    inf_cfg = get_config("inference") or {}
    sigmoid_params = inf_cfg.get("sigmoid_params", {})
    default = tuple(sigmoid_params.get("default", [15.0, 0.50]))

    name_lower = model_name.lower()
    if "e5-quora" in name_lower or "finetuned" in name_lower:
        return tuple(sigmoid_params.get("E5-quora-finetuned", default))
    elif "e5" in name_lower:
        return tuple(sigmoid_params.get("E5-base-v2", default))
    elif "bge-quora" in name_lower or "bge-finetuned" in name_lower:
        return tuple(sigmoid_params.get("BGE-quora-finetuned", default))
    elif "bge" in name_lower:
        return tuple(sigmoid_params.get("BGE-base-en-v1.5", default))
    elif "mpnet" in name_lower:
        return tuple(sigmoid_params.get("MPNet-base-v2", default))
    else:
        return default


def _get_threshold(model_name: str) -> float:
    """Optimal decision threshold per model (maximizes F1 on validation set).

    Values from configs/inference.yaml (per_model_thresholds).
    Fine-tuned models typically need different thresholds than frozen ones
    because contrastive fine-tuning shifts the similarity distribution.
    """
    inf_cfg = get_config("inference") or {}
    thresholds = inf_cfg.get("per_model_thresholds", {})
    default = inf_cfg.get("default_threshold", 0.5)

    name_lower = model_name.lower()
    if "cross-encoder-quora" in name_lower:
        return thresholds.get("Cross-Encoder-Quora (Trained)", 0.10)
    elif "e5-quora" in name_lower or "finetuned" in name_lower:
        return thresholds.get("E5-quora-finetuned", 0.40)
    elif "e5" in name_lower:
        return thresholds.get("E5-base-v2", 0.35)
    elif "bge-quora" in name_lower or "bge-finetuned" in name_lower:
        return thresholds.get("BGE-quora-finetuned", 0.38)
    elif "bge" in name_lower:
        return thresholds.get("BGE-base-en-v1.5", 0.30)
    elif "mpnet" in name_lower:
        return thresholds.get("MPNet-base-v2", 0.36)
    else:
        return default


def _result_dict(q1: str, q2: str, pred_label: int, prob_dup: float,
                 prob_non: float, threshold: float, model_name: str,
                 device: str, latency_ms: float) -> dict[str, Any]:
    return {
        "question1": q1,
        "question2": q2,
        "predicted_label": pred_label,
        "prediction": "Duplicate" if pred_label == 1 else "Non-Duplicate",
        "prob_non_duplicate": prob_non,
        "prob_duplicate": prob_dup,
        "confidence": max(prob_non, prob_dup),
        "threshold": threshold,
        "model_label": model_name,
        "model_name": model_name,
        "device": device,
        "latency_ms": latency_ms,
        "reason": None,
        "feature_breakdown": None,
    }


def predict_with_sentence_transformer(model_name: str, q1: str, q2: str) -> dict[str, Any]:
    """Predict single pair using sentence-transformers bi-encoder or cross-encoder.

    Supports:
    - Frozen models (BGE, E5, MPNet) with cosine similarity + sigmoid
    - Fine-tuned models (E5-quora-finetuned) with cosine similarity + adjusted sigmoid
    - Cross-encoders with softmax over NLI classes

    Note: If an E5 model is requested and a fine-tuned version is available on
    disk, we auto-upgrade for better accuracy.
    """
    model_name = resolve_best_available_e5_model(model_name)
    start = time.time()
    q1_norm = normalize_question(q1, expand_abbrevs=True, fix_typos=True)
    q2_norm = normalize_question(q2, expand_abbrevs=True, fix_typos=True)

    is_ft = is_finetuned_embedding_model(model_name)

    if is_cross_encoder_model(model_name):
        model = get_sentence_transformer_model(model_name)
        scores = model.predict([(q1_norm, q2_norm)], apply_softmax=True)[0]
        if isinstance(scores, (list, np.ndarray)) and len(scores) >= 3:
            contra = float(scores[0])
            entail = float(scores[2])
            denom = contra + entail
            prob_duplicate = entail / denom if denom > 0.01 else 0.5
        elif isinstance(scores, (list, np.ndarray)) and len(scores) == 2:
            # Binary cross-encoder: [p_not_dup, p_dup]
            prob_duplicate = float(scores[1])
        elif isinstance(scores, (list, np.ndarray)) and len(scores) == 1:
            prob_duplicate = max(0.0, min(1.0, (float(scores[0]) + 1) / 2))
        else:
            prob_duplicate = max(0.0, min(1.0, (float(scores[0]) + 1) / 2))
    else:
        model = get_sentence_transformer_model(model_name)
        # Determine if E5-style prefix is needed
        # Fine-tuned models that were trained with prefixes still need them
        use_e5_prefix = ("e5" in model_name.lower() and not is_ft) or (
            is_ft and "e5" in model_name.lower()
        )
        q1_enc = f"query: {q1_norm}" if use_e5_prefix else q1_norm
        q2_enc = f"passage: {q2_norm}" if use_e5_prefix else q2_norm

        emb1 = model.encode(q1_enc, normalize_embeddings=True)
        emb2 = model.encode(q2_enc, normalize_embeddings=True)
        similarity = float(np.dot(emb1, emb2))
        steepness, midpoint = _get_sigmoid_params(model_name.lower())
        prob_duplicate = 1.0 / (1.0 + np.exp(-steepness * (similarity - midpoint)))

    prob_non = 1.0 - prob_duplicate
    threshold = _get_threshold(model_name)
    pred_label = int(prob_duplicate >= threshold)
    latency_ms = (time.time() - start) * 1000

    return _result_dict(q1_norm, q2_norm, pred_label, prob_duplicate,
                        prob_non, threshold, model_name, _resolve_device(), latency_ms)


def predict_batch_sentence_transformer(model_name: str, pairs: list[tuple[str, str]],
                                       batch_size: int = 64) -> list[dict[str, Any]]:
    """Batched prediction using GPU-accelerated encoding.

    Supports both bi-encoders (batch encoding + cosine similarity) and
    cross-encoders (batch pair prediction). Vectorizes normalization,
    encodes all questions in batches, computes similarities, then applies
    calibration + threshold.

    Note: If an E5 model is requested and a fine-tuned version is available on
    disk, we auto-upgrade for better accuracy.
    """
    model_name = resolve_best_available_e5_model(model_name)
    if not pairs:
        return []

    start = time.time()
    device = _resolve_device()
    n = len(pairs)

    # Pre-normalize all questions (still sequential, negligible cost)
    q1s = [normalize_question(p[0], expand_abbrevs=True, fix_typos=True) for p in pairs]
    q2s = [normalize_question(p[1], expand_abbrevs=True, fix_typos=True) for p in pairs]

    model = get_sentence_transformer_model(model_name)
    threshold = _get_threshold(model_name)

    # Cross-encoder batch path
    if is_cross_encoder_model(model_name):
        all_scores = model.predict(list(zip(q1s, q2s)), batch_size=batch_size,
                                   apply_softmax=True, show_progress_bar=False)
        encode_time_ms = (time.time() - start) * 1000
        results = []
        for i in range(n):
            scores = all_scores[i]
            if len(scores) >= 3:
                # NLI 3-class: [contradiction, neutral, entailment]
                contra = float(scores[0])
                entail = float(scores[2])
                denom = contra + entail
                prob_dup = entail / denom if denom > 0.01 else 0.5
            elif len(scores) == 2:
                # Binary cross-encoder: [p_not_dup, p_dup]
                prob_dup = float(scores[1])
            else:
                prob_dup = max(0.0, min(1.0, (float(scores[0]) + 1) / 2))
            pred_label = int(prob_dup >= threshold)
            results.append(
                _result_dict(q1s[i], q2s[i], pred_label, prob_dup,
                             1.0 - prob_dup, threshold, model_name, device,
                             encode_time_ms)
            )
        return results

    # Bi-encoder batch path
    is_ft = is_finetuned_embedding_model(model_name)
    use_e5_prefix = ("e5" in model_name.lower() and not is_ft) or (
        is_ft and "e5" in model_name.lower()
    )
    q1_encoded = [f"query: {q}" if use_e5_prefix else q for q in q1s]
    q2_encoded = [f"passage: {q}" if use_e5_prefix else q for q in q2s]

    # Batch encode all questions (GPU accelerated)
    emb1 = model.encode(q1_encoded, normalize_embeddings=True,
                        batch_size=batch_size, show_progress_bar=False)
    emb2 = model.encode(q2_encoded, normalize_embeddings=True,
                        batch_size=batch_size, show_progress_bar=False)

    # Vectorized cosine similarity
    similarities = (emb1 * emb2).sum(axis=1)

    # Vectorized sigmoid calibration
    steepness, midpoint = _get_sigmoid_params(model_name.lower())
    probs = 1.0 / (1.0 + np.exp(-steepness * (similarities - midpoint)))
    preds = (probs >= threshold).astype(int)
    prob_nons = 1.0 - probs
    encode_time_ms = (time.time() - start) * 1000

    return [
        _result_dict(q1s[i], q2s[i], int(preds[i]), float(probs[i]),
                     float(prob_nons[i]), threshold, model_name, device,
                     encode_time_ms)
        for i in range(n)
    ]


def get_ensemble_prediction(q1: str, q2: str, paths=None) -> dict[str, Any]:
    """Ensemble: uses the adaptive weighted ensemble for higher quality.

    This replaces the simple trimmed-mean with the intelligent ensemble
    that dynamically weights models based on input features.
    If fine-tuned models are available, they are included in the ensemble.
    """
    if paths is None:
        paths = get_paths()
    from duplicate_question_app.intelligent_ensemble import get_adaptive_ensemble_prediction
    return get_adaptive_ensemble_prediction(q1, q2, paths)


# Convenience functions for checking model availability

def is_finetuned_model_available(model_name: str, paths=None) -> bool:
    """Check if a fine-tuned model is available on disk."""
    if paths is None:
        paths = get_paths()
    model_paths = {
        "E5-quora-finetuned": paths.finetuned_e5_dir,
        "BGE-quora-finetuned": paths.finetuned_bge_dir,
    }
    model_path = model_paths.get(model_name)
    if model_path is None:
        return False
    return model_path.exists() and (model_path / "config.json").exists()


def list_available_finetuned_models(paths=None) -> list[str]:
    """List all available fine-tuned models."""
    if paths is None:
        paths = get_paths()
    available = []
    if is_finetuned_model_available("E5-quora-finetuned", paths):
        available.append("E5-quora-finetuned")
    if is_finetuned_model_available("BGE-quora-finetuned", paths):
        available.append("BGE-quora-finetuned")
    return available
