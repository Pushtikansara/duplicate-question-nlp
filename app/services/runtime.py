"""Unified runtime services for model loading, inference, and context management.

Provides a single source of truth for:
- Model resolution (Week 2/3/4/Phase 2)
- Inference service creation
- Runtime context management
- Model metadata
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from app.utils.constants import PATHS, _model_cache
from duplicate_question_app._config.settings import (
    get_config,
    is_ensemble_model,
    is_new_embedding_model,
    resolve_model_selection,
)
from duplicate_question_app._inference.transformer import (
    DuplicateQuestionInferenceService,
    ModelArtifactsNotFoundError,
    load_model_and_tokenizer,
)
from duplicate_question_app._models.week2 import Week2InferenceService, is_week2_model


def get_model_resolution():
    """Get the current model resolution (Week 3/4 directory status)."""
    return resolve_model_selection(PATHS)


def load_model_config(model_dir: Path) -> dict[str, Any]:
    """Load model config.json from disk."""
    config_path = model_dir / "config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def _get_default_model() -> str:
    """Get default model from config or fallback."""
    app_cfg = get_config("app") or {}
    return app_cfg.get("default_model", "Improved DistilBERT (Week 4)")


def _get_default_threshold() -> float:
    """Get default decision threshold from config."""
    inf_cfg = get_config("inference") or {}
    return inf_cfg.get("default_threshold", 0.5)


def _get_device() -> str:
    """Get default device from config."""
    inf_cfg = get_config("inference") or {}
    return inf_cfg.get("default_device", "cpu")


def _build_metadata(
    model_label: str,
    model_version: str,
    decision_threshold: float,
    device: str,
    fallback_reason: str | None = None,
    load_errors: tuple[str, ...] = (),
    model_name: str = "",
) -> dict[str, Any]:
    """Build a consistent metadata dict for any model type."""
    return {
        "model_label": model_label,
        "model_version": model_version,
        "decision_threshold": decision_threshold,
        "threshold_source": f"Default {decision_threshold:.2f} threshold",
        "device": device,
        "fallback_reason": fallback_reason,
        "load_errors": load_errors,
        "model_name": model_name or model_label,
    }


def get_inference_service(_cache_key: str = "default") -> tuple[Any, dict[str, Any]]:
    """Get the appropriate inference service and metadata for the selected model.

    Returns:
        Tuple of (service, metadata) where service may be None for
        embedding/ensemble models that have their own prediction paths.
    """
    selected = st.session_state.get("selected_model", _get_default_model())
    cache_lookup_key = _cache_key if _cache_key != "default" else selected
    if cache_lookup_key in _model_cache:
        return _model_cache[cache_lookup_key]

    _default_th = _get_default_threshold()
    _device = _get_device()

    # Week 2 models (classical ML)
    if is_week2_model(selected):
        service = Week2InferenceService(PATHS)
        metadata = _build_metadata(
            model_label=selected,
            model_version="week2",
            decision_threshold=_default_th,
            device=_device,
        )
        _model_cache[cache_lookup_key] = (service, metadata)
        return service, metadata

    # Semantic Ensemble
    if is_ensemble_model(selected):
        metadata = _build_metadata(
            model_label="Semantic Ensemble",
            model_version="ensemble",
            decision_threshold=_default_th,
            device=_device,
        )
        _model_cache[cache_lookup_key] = (None, metadata)
        return None, metadata

    # Phase 2 embedding models (BGE, E5, MPNet, DeBERTa)
    if is_new_embedding_model(selected):
        metadata = _build_metadata(
            model_label=selected,
            model_version="phase2",
            decision_threshold=_default_th,
            device=_device,
            model_name=selected,
        )
        _model_cache[cache_lookup_key] = (None, metadata)
        return None, metadata

    # Week 3/4 transformer models (DistilBERT)
    try:
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS, model_version=selected)
    except (ValueError, FileNotFoundError, ModelArtifactsNotFoundError):
        try:
            model, tokenizer, metadata = load_model_and_tokenizer(PATHS)
        except (FileNotFoundError, ModelArtifactsNotFoundError):
            fallback_metadata = _build_metadata(
                model_label="No model available",
                model_version="none",
                decision_threshold=_default_th,
                device=_device,
                fallback_reason="No loadable model artifacts found on disk.",
                load_errors=("Week 4 and Week 3 directories are both missing or incomplete",),
            )
            _model_cache[cache_lookup_key] = (None, fallback_metadata)
            return None, fallback_metadata

    service = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
    _model_cache[cache_lookup_key] = (service, metadata)
    return service, metadata


def get_runtime_context() -> tuple[Any, Any, Any]:
    """Get the complete runtime context: (service, metadata, resolution)."""
    resolution = get_model_resolution()
    selected = st.session_state.get("selected_model", _get_default_model())
    cache_key = f"{resolution.cache_key}|model:{selected}"
    service, metadata = get_inference_service(cache_key)
    return service, metadata, resolution


def render_model_runtime_message(metadata: Any) -> None:
    """Render a status message about the currently active model."""
    _default_th = _get_default_threshold()
    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        threshold = metadata.get("decision_threshold", _default_th)
        st.info(f"Active model: **{model_label}** | Threshold: **{threshold:.2f}** | Device: **CPU**")
    elif hasattr(metadata, "model_label"):
        model_label = metadata.model_label
        threshold = getattr(metadata, "decision_threshold", _default_th)
        device = getattr(metadata, "device", "cpu")
        st.info(f"Active model: **{model_label}** | Threshold: **{threshold}** | Device: **{device}**")
        if hasattr(metadata, "load_errors") and metadata.load_errors:
            st.info("Earlier load attempts: " + " | ".join(metadata.load_errors))
