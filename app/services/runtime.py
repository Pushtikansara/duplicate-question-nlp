from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from app.utils.constants import PATHS, _model_cache
from duplicate_question_app.config import (
    get_config,
    is_ensemble_model,
    is_new_embedding_model,
    resolve_model_selection,
)
from duplicate_question_app.inference import (
    DuplicateQuestionInferenceService,
    ModelArtifactsNotFoundError,
    load_model_and_tokenizer,
)
from duplicate_question_app.week2_inference import Week2InferenceService, is_week2_model


def get_model_resolution():
    return resolve_model_selection(PATHS)


def load_model_config(model_dir: Path) -> dict[str, Any]:
    config_path = model_dir / "config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def _get_default_model() -> str:
    app_cfg = get_config("app") or {}
    return app_cfg.get("default_model", "Improved DistilBERT (Week 4)")


def _get_default_threshold() -> float:
    inf_cfg = get_config("inference") or {}
    return inf_cfg.get("default_threshold", 0.5)


def get_inference_service(_cache_key: str = "default") -> tuple[Any, Any]:
    selected = st.session_state.get("selected_model", _get_default_model())
    cache_lookup_key = _cache_key if _cache_key != "default" else selected
    if cache_lookup_key in _model_cache:
        return _model_cache[cache_lookup_key]

    _default_th = _get_default_threshold()
    _device = get_config("inference").get("default_device", "cpu")

    if is_week2_model(selected):
        service = Week2InferenceService(PATHS)
        metadata = {
            "model_label": selected,
            "model_version": "week2",
            "decision_threshold": _default_th,
            "threshold_source": f"Default {_default_th:.2f} threshold for classical ML model",
            "device": _device,
            "fallback_reason": None,
            "load_errors": (),
            "model_name": selected,
        }
        return service, metadata

    if is_ensemble_model(selected):
        return None, {"model_label": "Semantic Ensemble", "model_version": "ensemble", "device": _device}

    if is_new_embedding_model(selected):
        metadata = {
            "model_label": selected,
            "model_version": "phase2",
            "decision_threshold": _default_th,
            "threshold_source": f"Default {_default_th:.2f} threshold",
            "device": _device,
            "fallback_reason": None,
            "load_errors": (),
            "model_name": selected,
        }
        return None, metadata

    try:
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS, model_version=selected)
    except (ValueError, FileNotFoundError):
        try:
            model, tokenizer, metadata = load_model_and_tokenizer(PATHS)
        except (FileNotFoundError, ModelArtifactsNotFoundError):
            fallback_metadata = {
                "model_label": "No model available",
                "model_version": "none",
                "decision_threshold": _default_th,
                "threshold_source": f"Default {_default_th:.2f} threshold (no artifacts)",
                "device": _device,
                "fallback_reason": "No loadable model artifacts found on disk.",
                "load_errors": ("Week 4 and Week 3 directories are both missing or incomplete",),
                "model_name": "",
            }
            _model_cache[cache_lookup_key] = (None, fallback_metadata)
            return None, fallback_metadata
    service = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
    _model_cache[cache_lookup_key] = (service, metadata)
    return service, metadata


def get_transformer_service(selected: str) -> tuple[DuplicateQuestionInferenceService | None, Any]:
    try:
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS, model_version=selected)
    except (ValueError, FileNotFoundError):
        try:
            model, tokenizer, metadata = load_model_and_tokenizer(PATHS)
        except (FileNotFoundError, ModelArtifactsNotFoundError):
            fallback_metadata: dict[str, Any] = {
                "model_label": "No model available",
                "model_version": "none",
                "decision_threshold": _get_default_threshold(),
                "threshold_source": "No model artifacts",
                "device": "cpu",
                "fallback_reason": "No loadable model artifacts found on disk.",
                "load_errors": ("Week 4 and Week 3 directories are both missing or incomplete",),
                "model_name": "",
            }
            return None, fallback_metadata
    service = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
    return service, metadata


def get_runtime_context() -> tuple[Any, Any, Any]:
    resolution = get_model_resolution()
    selected = st.session_state.get("selected_model", _get_default_model())
    cache_key = f"{resolution.cache_key}|model:{selected}"
    service, metadata = get_inference_service(cache_key)
    return service, metadata, resolution


def render_model_runtime_message(metadata: Any) -> None:
    _default_th = _get_default_threshold()
    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        threshold = metadata.get("decision_threshold", _default_th)
        st.info(f"Active model: **{model_label}** | Threshold: **{threshold:.2f}** | Device: **CPU**")
    elif hasattr(metadata, "model_label"):
        model_label = metadata.model_label
        threshold = getattr(metadata, "decision_threshold", _default_th)
        device = getattr(metadata, "device", "cpu")
        if metadata.model_version == "week4":
            st.success(f"Active model: **{model_label}** | Threshold: **{threshold}** | Device: **{device}**")
        else:
            st.info(f"Active model: **{model_label}** | Threshold: **{threshold}** | Device: **{device}**")
        if hasattr(metadata, "load_errors") and metadata.load_errors:
            st.info("Earlier load attempts: " + " | ".join(metadata.load_errors))
