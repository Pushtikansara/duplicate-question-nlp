from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.metric_cards import safe_metric, metric_card_row
from app.services.data import get_dataset_summary
from app.services.runtime import get_model_resolution, get_runtime_context
from app.services.builder import get_model_metrics_for
from app.utils.constants import PATHS
from duplicate_question_app.config import get_config, is_transformer_model
from duplicate_question_app.week2_inference import is_week2_model
from duplicate_question_app.week2_inference import check_week2_artifacts
from duplicate_question_app.model_registry import build_registry


def _get_default_model() -> str:
    app_cfg = get_config("app") or {}
    return app_cfg.get("default_model", "Improved DistilBERT (Week 4)")


def render() -> None:
    selected_model = st.session_state.get("selected_model", _get_default_model())

    try:
        _, metadata, resolution = get_runtime_context()
    except Exception:
        resolution = get_model_resolution()
        metadata = None

    try:
        summary = get_dataset_summary()
    except Exception:
        summary = {"rows": 0, "duplicate_ratio": 0.0}

    week2_arts = check_week2_artifacts(PATHS)
    week2_ready = all(week2_arts.values())
    active_metrics = get_model_metrics_for(selected_model)

    registry = build_registry(PATHS)
    loaded_count = sum(1 for e in registry if e.load_status == "loaded" or e.load_status == "available")
    total_models = len(registry)

    inf_cfg = get_config("inference") or {}
    _default_th = inf_cfg.get("default_threshold", 0.5)
    _default_device = inf_cfg.get("default_device", "cpu")

    if is_transformer_model(selected_model) and metadata and not isinstance(metadata, dict):
        model_desc = metadata.model_label
        model_device = metadata.device
        model_threshold = metadata.decision_threshold
    elif is_week2_model(selected_model):
        model_desc = selected_model
        model_device = _default_device
        model_threshold = _default_th
    else:
        model_desc = selected_model
        model_device = _default_device
        model_threshold = _default_th

    st.markdown(
        f"""
        <div class="hero-card">
            <h1 style="margin:0 0 0.15rem 0; font-size:1.6rem;">Duplicate Question Detection</h1>
            <p style="margin:0 0 0.4rem 0; color:#475569; font-size:0.95rem;">
                Research-grade semantic duplicate detection with {total_models} models
            </p>
            <p class="small-note">
                Active: <strong>{model_desc}</strong> · {model_device.upper()} · threshold {model_threshold:.2f}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-header'>System Overview</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Model", model_desc[:28] + "..." if len(model_desc) > 28 else model_desc)
    col2.metric("Available Models", f"{loaded_count}/{total_models}")
    col3.metric("Inference Device", model_device.upper())
    col4.metric("Dataset Size", f"{summary['rows']:,} pairs")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Duplicate Ratio", safe_metric(summary.get("duplicate_ratio", 0)))
    col2.metric("Week 2 (LR/SVM)", "✅ Ready" if week2_ready else "❌ Missing")
    col3.metric("Week 3 (DistilBERT)", "✅" if resolution.week3.ready else "❌")
    col4.metric("Week 4 (Improved)", "✅" if resolution.week4.ready else "❌")

    if active_metrics and any(v is not None for v in [active_metrics.get("accuracy"), active_metrics.get("f1")]):
        st.markdown("<div class='section-header'>Active Model Performance</div>", unsafe_allow_html=True)
        metric_card_row(active_metrics)

    st.markdown("<div class='section-header'>Model Registry</div>", unsafe_allow_html=True)
    reg_data = []
    for e in registry:
        status_icon = "✅" if e.has_artifacts or e.source == "built-in" else ("⬇️" if e.source == "huggingface" else "❌")
        reg_data.append({
            "Model": e.display_name,
            "Type": e.model_type.replace("-", " ").title(),
            "Framework": e.framework.upper(),
            "Source": e.source.title(),
            "Status": status_icon,
            "Params": e.parameters,
        })
    reg_df = pd.DataFrame(reg_data)
    st.dataframe(reg_df, use_container_width=True, hide_index=True,
                 column_config={"Status": st.column_config.TextColumn("Status", width="small")})
