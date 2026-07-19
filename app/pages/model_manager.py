from __future__ import annotations

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app.model_registry import build_registry, find_registry_entry


def render() -> None:
    st.title("Model Manager")
    st.markdown(
        "<p style='color:#64748B;font-size:0.95rem;'>Complete model registry — inspect all 9 models, their metadata, status, and configuration.</p>",
        unsafe_allow_html=True,
    )

    registry = build_registry(PATHS)

    st.markdown("<div class='section-header'>All Models</div>", unsafe_allow_html=True)
    rows = []
    for e in registry:
        rows.append(
            {
                "Model": e.display_name,
                "Type": e.model_type.replace("-", " ").title(),
                "Framework": e.framework.upper(),
                "Source": e.source.title(),
                "Device": e.device.upper(),
                "Size": f"{e.size_mb:.0f} MB" if e.size_mb else "N/A",
                "Params": e.parameters,
                "Status": (
                    "✅ Ready"
                    if e.has_artifacts or e.source == "built-in"
                    else "⚠️ Auto-download"
                    if e.source == "huggingface"
                    else "❌ Missing"
                ),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("<div class='section-header'>Model Details</div>", unsafe_allow_html=True)
    selected = st.selectbox("Select a model for details", [e.display_name for e in registry], key="model_mgr_select")
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
            st.markdown(f"**Cache Path:** `{entry.cache_path or 'N/A'}`")
            st.markdown(f"**Status:** {entry.load_status}")
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
