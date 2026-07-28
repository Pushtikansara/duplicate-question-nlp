from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from ares._config import get_app_paths, resolve_device
from ares.model_registry import ModelBackend, ModelEntry, find_entry

logger = logging.getLogger(__name__)

_model_cache: dict[str, Any] = {}
_model_load_times: dict[str, float] = {}
_model_load_errors: dict[str, str] = {}

MAX_CACHED_MODELS = 20


def get_cached_model(model_name: str) -> Any:
    return _model_cache.get(model_name)


def is_model_cached(model_name: str) -> bool:
    return model_name in _model_cache


def get_load_error(model_name: str) -> str | None:
    return _model_load_errors.get(model_name)


def get_load_time(model_name: str) -> float | None:
    return _model_load_times.get(model_name)


def clear_model_cache(model_name: str | None = None) -> None:
    if model_name:
        _model_cache.pop(model_name, None)
        _model_load_times.pop(model_name, None)
        _model_load_errors.pop(model_name, None)
    else:
        _model_cache.clear()
        _model_load_times.clear()
        _model_load_errors.clear()


def unload_least_recently_used() -> None:
    if len(_model_cache) <= MAX_CACHED_MODELS:
        return
    sorted_models = sorted(_model_load_times.items(), key=lambda x: x[1])
    to_remove = sorted_models[0][0]
    _model_cache.pop(to_remove, None)
    _model_load_times.pop(to_remove, None)
    _model_load_errors.pop(to_remove, None)
    logger.info("Unloaded model '%s' (LRU eviction)", to_remove)


def load_model(model_name: str) -> Any:
    if model_name in _model_cache:
        _model_load_times[model_name] = time.time()
        return _model_cache[model_name]

    paths = get_app_paths()
    entry = find_entry(model_name, paths)
    if entry is None:
        raise ValueError(f"Unknown model: '{model_name}'")

    if entry.backend == ModelBackend.ENSEMBLE:
        raise ValueError("Ensemble model cannot be loaded directly; use FusionEngine")

    start = time.perf_counter()
    try:
        model = _do_load(entry, paths)
        elapsed = (time.perf_counter() - start) * 1000
        _model_cache[model_name] = model
        _model_load_times[model_name] = time.time()
        logger.info("Loaded model '%s' in %.1fms", model_name, elapsed)
        unload_least_recently_used()
        return model
    except Exception as e:
        _model_load_errors[model_name] = str(e)
        logger.error("Failed to load model '%s': %s", model_name, e)
        raise


def load_model_with_diagnostics(model_name: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        model = load_model(model_name)
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "success": True,
            "model": model,
            "load_time_ms": elapsed,
            "cache_hit": model_name in _model_cache and _model_load_times.get(model_name, 0) > start,
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "error": str(e),
            "load_time_ms": elapsed,
        }


def _do_load(entry: ModelEntry, paths: Any) -> Any:
    backend = entry.backend

    if backend == ModelBackend.CLASSICAL_ML:
        return _load_classical(entry, paths)
    elif backend == ModelBackend.TRANSFORMER:
        return _load_transformer(entry, paths)
    elif backend == ModelBackend.BI_ENCODER:
        return _load_bi_encoder(entry)
    elif backend == ModelBackend.CROSS_ENCODER:
        return _load_cross_encoder(entry)
    else:
        raise ValueError(f"Unsupported backend: {backend}")


def _load_classical(entry: ModelEntry, paths: Any) -> Any:
    import joblib

    model_dir = paths.models_dir / "week2_models"
    if entry.internal_id == "week2_lr":
        path = model_dir / "logistic_regression.joblib"
    elif entry.internal_id == "week2_svm":
        path = model_dir / "linear_svm.joblib"
    else:
        raise ValueError(f"Unknown classical model: {entry.internal_id}")

    if not path.exists():
        raise FileNotFoundError(f"Model weights not found: {path}")

    vectorizer_path = model_dir / "tfidf_vectorizer.joblib"
    if not vectorizer_path.exists():
        raise FileNotFoundError(f"Vectorizer not found: {vectorizer_path}")

    clf = joblib.load(path)
    vectorizer = joblib.load(vectorizer_path)
    return {"classifier": clf, "vectorizer": vectorizer, "type": "classical"}


def _load_transformer(entry: ModelEntry, paths: Any) -> Any:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_dir = Path(entry.artifact_path) if entry.artifact_path else None
    if model_dir is None or not model_dir.exists():
        raise FileNotFoundError(f"Model directory not found: {model_dir}")

    device = resolve_device()
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    model = model.to(device)
    model.eval()
    return {"model": model, "tokenizer": tokenizer, "device": device, "type": "transformer"}


def _load_bi_encoder(entry: ModelEntry) -> Any:
    from sentence_transformers import SentenceTransformer

    model_key = entry.hub_name or entry.artifact_path
    if model_key is None:
        raise ValueError(f"No model key for {entry.display_name}")

    device = resolve_device()
    model = SentenceTransformer(model_key, device=device)
    return {"model": model, "device": device, "type": "bi-encoder", "use_e5_prefix": "e5" in entry.internal_id}


def _load_cross_encoder(entry: ModelEntry) -> Any:
    from sentence_transformers import CrossEncoder

    model_key = entry.hub_name or entry.artifact_path
    if model_key is None:
        raise ValueError(f"No model key for {entry.display_name}")

    device = "cuda" if resolve_device() == "cuda" else "cpu"
    model = CrossEncoder(model_key, device=device)
    return {"model": model, "device": device, "type": "cross-encoder"}


def get_model_info(model_name: str) -> dict[str, Any]:
    paths = get_app_paths()
    entry = find_entry(model_name, paths)
    if entry is None:
        return {"error": f"Unknown model: {model_name}"}
    return {
        "display_name": entry.display_name,
        "internal_id": entry.internal_id,
        "backend": entry.backend.value,
        "status": entry.status.value,
        "availability": entry.availability,
        "is_cached": is_model_cached(model_name),
        "load_error": get_load_error(model_name),
        "parameter_count": entry.parameter_count,
        "memory_usage_mb": entry.memory_usage_mb,
        "supports_gpu": entry.capabilities.supports_gpu,
    }
