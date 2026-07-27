from __future__ import annotations

from typing import Any

import streamlit as st

from app.context import get_paths
from app.utils.constants import _model_cache
from ares.inference.dispatcher import InferenceDispatcher
from duplicate_question_app._config.settings import (
    get_config,
    resolve_model_selection,
)


def get_model_resolution():
    return resolve_model_selection(get_paths())


def load_model_config(model_dir: Path) -> dict[str, Any]:
    config_path = model_dir / "config.json"
    if not config_path.exists():
        return {}
    import json

    return json.loads(config_path.read_text(encoding="utf-8"))


def _get_default_threshold() -> float:
    inf_cfg = get_config("inference") or {}
    return inf_cfg.get("default_threshold", 0.5)


def _get_device() -> str:
    inf_cfg = get_config("inference") or {}
    return inf_cfg.get("default_device", "cpu")


def get_inference_service(_cache_key: str = "default") -> tuple[Any, dict[str, Any]]:
    selected = st.session_state.get("selected_model", "")
    if not selected:
        models = InferenceDispatcher.list_models()
        if models:
            selected = models[0]
        else:
            return None, {"model_label": "No models available"}

    if _cache_key in _model_cache:
        return _model_cache[_cache_key]

    return None, {
        "model_label": selected,
        "decision_threshold": _get_default_threshold(),
        "device": _get_device(),
        "model_name": selected,
    }


def get_runtime_context() -> tuple[Any, Any, Any]:
    resolution = get_model_resolution()
    selected = st.session_state.get("selected_model", "")
    if not selected:
        models = InferenceDispatcher.list_models()
        if models:
            selected = models[0]
    service, metadata = get_inference_service()
    return service, metadata, resolution


def render_model_runtime_message(metadata: Any) -> None:
    model_label = metadata.get("model_label", "Unknown") if isinstance(metadata, dict) else "Unknown"
    st.info(f"Active model: **{model_label}**")
