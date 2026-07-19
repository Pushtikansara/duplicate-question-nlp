"""🏠 Home — Professional dashboard with KPI cards and system metrics."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from duplicate_question_app.config import (
    is_transformer_model,
    resolve_model_selection,
)
from duplicate_question_app.model_registry import build_registry
from duplicate_question_app.week2_inference import check_week2_artifacts, is_week2_model


def render(
    get_runtime_context: Any,
    get_dataset_summary: Any,
    get_model_metrics_for: Any,
    safe_metric: Any,
    metric_card_row: Any,
    PATHS: Any,
) -> None:
    """Render the professional dashboard homepage."""
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    try:
        _, metadata, resolution = get_runtime_context()
    except Exception:
        try:
            resolution = resolve_model_selection(PATHS)
        except Exception:
            resolution = None
        metadata = None

    try:
        summary = get_dataset_summary()
    except Exception:
        summary = {"rows": 0, "duplicate_ratio": 0.0}

    week2_arts = check_week2_artifacts(PATHS)
    week2_ready = all(week2_arts.values())
    active_metrics = get_model_metrics_for(selected_model)

    registry = build_registry(PATHS)
    total_models = len(registry)

    # Active model info
    if is_transformer_model(selected_model) and metadata and not isinstance(metadata, dict):
        model_desc = metadata.model_label
        model_device = metadata.device
        model_threshold = metadata.decision_threshold
    elif is_week2_model(selected_model):
        model_desc = selected_model
        model_device = "cpu"
        model_threshold = 0.5
    else:
        model_desc = selected_model
        model_device = "cpu"
        model_threshold = 0.5

    # Hero section
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

    # KPI cards row
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Active Model", model_desc[:28] + "..." if len(model_desc) > 28 else model_desc)
    r2.metric(
        "Available Models", f"{sum(1 for e in registry if e.has_artifacts or e.source == 'built-in')}/{total_models}"
    )
    r3.metric("Inference Device", model_device.upper())
    r4.metric("Dataset Size", f"{summary.get('rows', 0):,} pairs")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Duplicate Ratio", safe_metric(summary.get("duplicate_ratio", 0)))
    r2.metric("Week 2 (LR/SVM)", "✅ Ready" if week2_ready else "❌ Missing")
    r3.metric("Week 3 (DistilBERT)", "✅" if resolution and resolution.week3.ready else "❌")
    r4.metric("Week 4 (Improved)", "✅" if resolution and resolution.week4.ready else "❌")

    # Model registry overview
    st.markdown("<div class='section-header'>Model Registry</div>", unsafe_allow_html=True)
    reg_data = []
    for e in registry:
        status_icon = (
            "✅" if e.has_artifacts or e.source == "built-in" else ("⬇️" if e.source == "huggingface" else "❌")
        )
        reg_data.append(
            {
                "Model": e.display_name,
                "Type": e.model_type.replace("-", " ").title(),
                "Framework": e.framework.upper(),
                "Source": e.source.title(),
                "Status": status_icon,
                "Params": e.parameters,
            }
        )
    # Active model performance
    if active_metrics and any(v is not None for v in [active_metrics.get("accuracy"), active_metrics.get("f1")]):
        st.markdown("<div class='section-header'>Active Model Performance</div>", unsafe_allow_html=True)
        metric_card_row(active_metrics)

    st.dataframe(
        pd.DataFrame(reg_data),
        use_container_width=True,
        hide_index=True,
        column_config={"Status": st.column_config.TextColumn("Status", width="small")},
    )
