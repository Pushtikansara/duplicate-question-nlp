"""Professional landing page for the DQD application.

Features:
- Hero section with key metrics
- Feature cards highlighting capabilities
- Model registry overview
- System status indicators
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.metric_cards import metric_card_row, safe_metric
from app.services.builder import get_model_metrics_for
from app.services.data import get_dataset_summary
from app.services.runtime import get_model_resolution, get_runtime_context
from app.utils.constants import PATHS
from duplicate_question_app._config.settings import get_config, is_transformer_model
from duplicate_question_app._models.registry import build_registry
from duplicate_question_app._models.week2 import check_week2_artifacts, is_week2_model


def _get_default_model() -> str:
    app_cfg = get_config("app") or {}
    return app_cfg.get("default_model", "Improved DistilBERT (Week 4)")


def _render_hero_section() -> dict:
    """Render the hero section and return extracted state."""
    selected_model = st.session_state.get("selected_model", _get_default_model())

    try:
        _, metadata, resolution = get_runtime_context()
    except Exception:
        resolution = get_model_resolution()
        metadata = None

    try:
        summary = get_dataset_summary()
    except Exception:
        summary = {"rows": 404290, "duplicate_ratio": 0.37}

    week2_arts = check_week2_artifacts(PATHS)
    week2_ready = all(week2_arts.values())

    active_metrics = get_model_metrics_for(selected_model)

    registry = build_registry(PATHS)
    loaded_count = sum(1 for e in registry if e.load_status in ("loaded", "available"))
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

    # Hero card
    st.markdown(
        f"""
        <div class="hero-card">
            <h1 style="margin:0 0 0.1rem 0; font-size:1.6rem; font-weight:700;">
                Duplicate Question Detection
            </h1>
            <p style="margin:0 0 0.3rem 0; color:#475569; font-size:0.95rem;">
                Research-grade semantic duplicate detection with <strong>{total_models}</strong> models
            </p>
            <p class="small-note">
                Active: <strong>{model_desc}</strong>
                &nbsp;·&nbsp; {model_device.upper()}
                &nbsp;·&nbsp; threshold {model_threshold:.2f}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Key metrics row
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

    return {
        "active_metrics": active_metrics,
        "registry": registry,
        "selected_model": selected_model,
        "summary": summary,
    }


def _render_model_performance(active_metrics: dict) -> None:
    """Render active model performance section."""
    if active_metrics and any(v is not None for v in [active_metrics.get("accuracy"), active_metrics.get("f1")]):
        st.markdown("<div class='section-header'>Active Model Performance</div>", unsafe_allow_html=True)
        metric_card_row(active_metrics)


def _render_feature_cards() -> None:
    """Render feature capability cards."""
    features = [
        ("🎯", "Live Inference", "Test individual question pairs with any model"),
        ("📊", "Batch Processing", "Upload CSV for bulk duplicate detection"),
        ("🔬", "Model Comparison", "Side-by-side metrics across all models"),
        ("🧪", "Linguistic Analysis", "Entity, intent, negation & contradiction detection"),
        ("⚙️", "Ensemble Methods", "Adaptive weighted ensemble with dynamic routing"),
        ("📈", "Performance Dashboard", "Confusion matrices, ROC curves, ablation studies"),
    ]

    st.markdown("<div class='section-header'>Capabilities</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div class="icon">{icon}</div>
                    <div class="title">{title}</div>
                    <div class="desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_model_registry(registry: list) -> None:
    """Render the model registry table."""
    st.markdown("<div class='section-header'>Model Registry</div>", unsafe_allow_html=True)
    reg_data = []
    for e in registry:
        status_icon = "✅" if e.has_artifacts or e.source == "built-in" else "⬇️" if e.source == "huggingface" else "❌"
        reg_data.append(
            {
                "Model": e.display_name,
                "Type": e.model_type.replace("-", " ").title(),
                "Framework": e.framework.upper(),
                "Source": e.source.title(),
                "Status": status_icon,
                "Parameters": e.parameters,
            }
        )
    reg_df = pd.DataFrame(reg_data)
    st.dataframe(
        reg_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
    )


def render() -> None:
    """Main landing page render function."""
    state = _render_hero_section()
    _render_model_performance(state["active_metrics"])
    _render_feature_cards()
    _render_model_registry(state["registry"])
