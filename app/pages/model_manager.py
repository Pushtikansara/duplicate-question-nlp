from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app._models.registry import build_registry, find_registry_entry


def _render_prediction_mode_section() -> None:
    st.markdown("<div class='section-header'>Prediction Mode</div>", unsafe_allow_html=True)
    current_mode = st.session_state.get("prediction_mode", "fusion")

    mode_options = {
        "cross_encoder_only": "CrossEncoder Only — fastest, uses only the neural classifier",
        "cross_encoder_dominant": "CrossEncoder Dominant — CE=0.80, Semantic=0.08 (recommended default)",
        "fusion": "Fusion (Original) — balanced CE=0.40, Semantic=0.25 combination",
        "confidence_weighted": "Confidence Weighted — weights adjust based on prediction confidence",
        "adaptive": "Adaptive — dynamically adjusts CE vs Semantic weight per pair",
        "semantic_dominant": "Semantic Dominant — Semantic=0.40, CE=0.20",
        "semantic_only": "Semantic Intelligence Only — no CrossEncoder needed",
    }

    def _on_mode_change():
        st.session_state["prediction_mode"] = st.session_state.prediction_mode_selector
        st.rerun()

    st.selectbox(
        "Select prediction mode",
        options=list(mode_options.keys()),
        format_func=lambda k: f"{k.replace('_', ' ').title()}",
        index=list(mode_options.keys()).index(current_mode) if current_mode in mode_options else 0,
        key="prediction_mode_selector",
        on_change=_on_mode_change,
        help=mode_options.get(current_mode, ""),
    )

    mode_info = {
        "cross_encoder_only": "🔴 CrossEncoder Only — Semantic Engine is NOT loaded",
        "cross_encoder_dominant": "🔵 CrossEncoder Dominant — Semantic Engine provides explanations only",
        "fusion": "🔵 Fusion (Original) — Balanced combination",
        "confidence_weighted": "🟣 Confidence Weighted — Adjusts based on prediction certainty",
        "adaptive": "🟠 Adaptive — Best of both worlds, auto-adjusts per pair",
        "semantic_dominant": "🟢 Semantic Dominant — Semantic Engine takes lead",
        "semantic_only": "🟢 Semantic Intelligence Only — CrossEncoder is NOT loaded",
    }
    st.info(f"Active: **{mode_info.get(current_mode, current_mode)}**")

    st.markdown("---")


def _render_model_table(registry: list) -> None:
    st.markdown("<div class='section-header'>All Models</div>", unsafe_allow_html=True)

    search_query = st.text_input("Search models", placeholder="Type to filter models...", key="model_mgr_search")

    rows = []
    for e in registry:
        if search_query and search_query.lower() not in e.display_name.lower():
            continue
        status_badge = (
            "✅ Ready"
            if e.has_artifacts or e.source == "built-in"
            else "⬇️ Auto-download"
            if e.source == "huggingface"
            else "❌ Missing"
        )
        rows.append(
            {
                "Model": e.display_name,
                "Type": e.model_type.replace("-", " ").title(),
                "Framework": e.framework.upper(),
                "Status": status_badge,
                "Size": f"{e.size_mb:.0f} MB" if e.size_mb else "N/A",
                "Params": e.parameters,
                "Accuracy": f"{e.accuracy:.3f}" if e.accuracy else "",
                "F1": f"{e.f1_score:.3f}" if e.f1_score else "",
            }
        )

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Accuracy": st.column_config.NumberColumn(format="%.3f"),
                "F1": st.column_config.NumberColumn(format="%.3f"),
            },
        )
    else:
        st.info("No models match your search.")


def _render_model_details(registry: list) -> None:
    st.markdown("<div class='section-header'>Model Details</div>", unsafe_allow_html=True)

    model_names = [e.display_name for e in registry]
    search_term = st.text_input(
        "Find model by name", placeholder="Search for a model...", key="model_mgr_detail_search"
    )

    filtered = [n for n in model_names if search_term.lower() in n.lower()] if search_term else model_names

    if not filtered:
        st.info("No models found matching your search.")
        return

    selected = st.selectbox("Select a model for details", filtered, key="model_mgr_select")
    entry = find_registry_entry(selected, PATHS)
    if entry:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"**Display Name:** {entry.display_name}")
            st.markdown(f"**Internal ID:** `{entry.internal_id}`")
            st.markdown(f"**Type:** {entry.model_type}")
            st.markdown(f"**Framework:** {entry.framework}")
            st.markdown(f"**Source:** {entry.source}")
            st.markdown(f"**Version:** {entry.version}")
            st.markdown(f"**Device:** {entry.device}")
        with col2:
            st.markdown(f"**Parameters:** {entry.parameters}")
            st.markdown(f"**Embedding Size:** {entry.embedding_size or 'N/A'}")
            st.markdown(f"**Hidden Size:** {entry.hidden_size or 'N/A'}")
            st.markdown(f"**Local Path:** `{entry.local_path or 'N/A'}`")
            st.markdown(f"**Status:** {entry.load_status}")
            if entry.accuracy:
                st.markdown(f"**Accuracy:** {entry.accuracy:.3f}")
            if entry.f1_score:
                st.markdown(f"**F1 Score:** {entry.f1_score:.3f}")
        st.markdown(f"**Description:** {entry.description}")
        if entry.advantages:
            st.markdown(f"**Advantages:** {'; '.join(entry.advantages)}")
        if entry.weaknesses:
            st.markdown(f"**Weaknesses:** {'; '.join(entry.weaknesses)}")
        st.markdown(f"**Recommended Use:** {entry.recommended_use}")

    st.markdown("---")
    st.markdown("<div class='section-header'>Model Artifact Paths</div>", unsafe_allow_html=True)
    path_rows = []
    for e in registry:
        path_rows.append(
            {
                "Model": e.display_name,
                "Local Path": e.local_path or "—",
                "Cache Path": e.cache_path or "—",
            }
        )
    st.dataframe(pd.DataFrame(path_rows), use_container_width=True, hide_index=True)


def render() -> None:
    st.title("Model Manager")
    st.markdown(
        "<p style='color:#64748B;font-size:0.95rem;'>Complete model registry — inspect all models, their metadata, status, and configuration. Switch prediction mode below.</p>",
        unsafe_allow_html=True,
    )

    _render_prediction_mode_section()

    registry = build_registry(PATHS)
    _render_model_table(registry)
    _render_model_details(registry)
