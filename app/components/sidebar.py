"""Professional sidebar navigation for the DQD application.

Provides a single, unified navigation with:
- Visible group headers (Core, Linguistic Analysis, etc.)
- Consistent emoji icons for every page
- Reliable radio navigation
- Centralized page routing
"""

from __future__ import annotations

import streamlit as st

from app.services.runtime import get_model_resolution, get_runtime_context
from app.utils.constants import PATHS, _model_cache
from duplicate_question_app._config.settings import MODEL_CHOICES
from duplicate_question_app._models.embeddings import clear_embedding_cache
from duplicate_question_app._models.week2 import check_week2_artifacts

# ---------------------------------------------------------------------------
# Navigation definition — single source of truth
# Maps display name (with icon) → route key
# ---------------------------------------------------------------------------

ROUTE_MAP: dict[str, str] = {
    # Core
    "\U0001f3e0 Home": "Landing Page",
    "\U0001f3af Prediction": "Prediction Page",
    "\U0001f4ca Batch CSV": "Batch CSV Prediction",
    "\U0001f4c9 Performance": "Performance Dashboard",
    # Linguistic Analysis
    "\U0001f9ea Entity Detection": "Entity Detection",
    "\U0001f9ea Intent Detection": "Intent Detection",
    "\U0001f9ea Negation Detection": "Negation Detection",
    "\U0001f9ea Contradiction Detection": "Contradiction Detection",
    "\U0001f9ea Lexical Penalty": "Lexical Penalty",
    # Advanced
    "\U0001f504 Adaptive Ensemble": "Adaptive Ensemble V2",
    "\u2699\ufe0f Calibration": "Advanced Calibration",
    "\U0001f4a1 Explainability": "Advanced Explainability",
    "\U0001f4cb Agreement Dashboard": "Agreement Dashboard",
    "\U0001f52c Hard Example Mining": "Hard Example Mining",
    # Information
    "\U0001f517 Model Manager": "Model Manager",
    "\U0001f4ca Dataset Info": "Dataset Information",
}


def get_route_map() -> dict[str, str]:
    """Return the centralized route map for use by _entry.py."""
    return ROUTE_MAP


def _render_group_label(label: str) -> None:
    """Render a visual group header in the sidebar."""
    st.sidebar.markdown(
        f"<div style='font-size:0.7rem;font-weight:600;text-transform:uppercase;"
        f"letter-spacing:0.08em;color:#64748B;margin:0.75rem 0 0.15rem 0;'>{label}</div>",
        unsafe_allow_html=True,
    )


def sidebar_navigation() -> str:
    """Render the complete sidebar and return the selected page route key."""
    # --- App Title ---
    st.sidebar.markdown(
        """
        <div style="padding:0.5rem 0 0.25rem 0;">
            <div style="font-size:1.1rem;font-weight:700;color:#0F172A;">
                \U0001f52c DQD
            </div>
            <div style="font-size:0.75rem;color:#64748B;margin-top:-0.15rem;">
                Duplicate Question Detection
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Navigation with visible groups ---
    nav_groups: list[tuple[str, list[str]]] = [
        ("Core", ["\U0001f3e0 Home", "\U0001f3af Prediction", "\U0001f4ca Batch CSV", "\U0001f4c9 Performance"]),
        (
            "Linguistic Analysis",
            [
                "\U0001f9ea Entity Detection",
                "\U0001f9ea Intent Detection",
                "\U0001f9ea Negation Detection",
                "\U0001f9ea Contradiction Detection",
                "\U0001f9ea Lexical Penalty",
            ],
        ),
        (
            "Advanced",
            [
                "\U0001f504 Adaptive Ensemble",
                "\u2699\ufe0f Calibration",
                "\U0001f4a1 Explainability",
                "\U0001f4cb Agreement Dashboard",
                "\U0001f52c Hard Example Mining",
            ],
        ),
        ("Information", ["\U0001f517 Model Manager", "\U0001f4ca Dataset Info"]),
    ]

    # Build flat list preserving group order
    flat_pages: list[str] = []
    for _group_name, pages in nav_groups:
        for page in pages:
            flat_pages.append(page)

    # Current page state
    current = st.session_state.get("current_page", "\U0001f3e0 Home")
    if current not in flat_pages:
        current = "\U0001f3e0 Home"

    default_idx = flat_pages.index(current) if current in flat_pages else 0

    # Render group headers above the radio for visual hierarchy
    for group_name, _pages in nav_groups:
        _render_group_label(group_name)

    # Use radio for reliable navigation (label_visibility=collapsed since headers above)
    selected = st.sidebar.radio(
        "Navigate",
        flat_pages,
        index=default_idx,
        key="nav_radio",
        label_visibility="collapsed",
    )

    if selected != current:
        st.session_state["current_page"] = selected

    # --- Model Selector ---
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='font-size:0.7rem;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.08em;color:#64748B;margin:0.5rem 0 0.25rem 0;'>Model</div>",
        unsafe_allow_html=True,
    )

    prev_model = st.session_state.get("selected_model", None)
    st.sidebar.selectbox(
        "Select model",
        MODEL_CHOICES,
        index=MODEL_CHOICES.index(prev_model) if prev_model in MODEL_CHOICES else 3,
        key="selected_model_widget",
        label_visibility="collapsed",
        on_change=lambda: (
            st.session_state.update(selected_model=st.session_state.selected_model_widget),
            _model_cache.clear(),
            clear_embedding_cache(),
            None,
        ),
    )

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "Improved DistilBERT (Week 4)"

    # --- Active Model Status ---
    resolution = get_model_resolution()
    model_name = st.session_state["selected_model"]
    try:
        _, metadata, _ = get_runtime_context()
        if isinstance(metadata, dict):
            active_label = metadata.get("model_label", model_name)[:30]
        elif metadata:
            active_label = metadata.model_label[:30]
        else:
            active_label = model_name[:30]
    except Exception:
        active_label = model_name[:30]

    st.sidebar.caption(f"Active: **{active_label}**")

    # --- Model Availability Status ---
    week2_ready = all(check_week2_artifacts(PATHS).values())
    st.sidebar.caption(
        f"W2: {'✅' if week2_ready else '❌'}  "
        f"W3: {'✅' if resolution.week3.ready else '❌'}  "
        f"W4: {'✅' if resolution.week4.ready else '❌'}"
    )

    return ROUTE_MAP.get(selected, "Landing Page")
