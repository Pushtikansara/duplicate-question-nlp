"""Streamlit application entry point — professional NLP product UI.

Features:
- Single, unified navigation via sidebar
- Professional footer with consistent branding
- Graceful error handling per-page
- Fallback to landing page on unknown routes
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — ensure the project root is on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import streamlit as st

from app.components.footer import render_footer
from app.components.helpers import inject_styles
from app.components.sidebar import sidebar_navigation
from app.pages import (
    render_adaptive_ensemble,
    render_advanced_calibration,
    render_advanced_explainability,
    render_agreement_dashboard,
    render_batch_prediction,
    render_contradiction_detection,
    render_dataset,
    render_entity_detection,
    render_error_explorer,
    render_home,
    render_intent_detection,
    render_lexical_penalty,
    render_model_manager,
    render_negation_detection,
    render_performance,
    render_prediction,
)

st.set_page_config(
    page_title="DQD — Duplicate Question Detection",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()


# Build route → render function map (single source of truth in sidebar defines display names)
_ROUTE_RENDER_MAP: dict[str, tuple[str, object]] = {
    "Landing Page": ("🏠 Home", render_home),
    "Prediction Page": ("🎯 Prediction", render_prediction),
    "Batch CSV Prediction": ("📊 Batch CSV", render_batch_prediction),
    "Performance Dashboard": ("📉 Performance", render_performance),
    "Entity Detection": ("🧪 Entity Detection", render_entity_detection),
    "Intent Detection": ("🧪 Intent Detection", render_intent_detection),
    "Negation Detection": ("🧪 Negation Detection", render_negation_detection),
    "Contradiction Detection": ("🧪 Contradiction Detection", render_contradiction_detection),
    "Lexical Penalty": ("🧪 Lexical Penalty", render_lexical_penalty),
    "Adaptive Ensemble V2": ("🔄 Adaptive Ensemble", render_adaptive_ensemble),
    "Advanced Calibration": ("⚙️ Calibration", render_advanced_calibration),
    "Advanced Explainability": ("💡 Explainability", render_advanced_explainability),
    "Agreement Dashboard": ("📋 Agreement Dashboard", render_agreement_dashboard),
    "Hard Example Mining": ("🔬 Hard Example Mining", render_error_explorer),
    "Model Manager": ("🔗 Model Manager", render_model_manager),
    "Dataset Information": ("📋 Dataset Info", render_dataset),
}


def _safe_render(render_fn, page_name: str) -> None:
    """Render a page with graceful error handling."""
    try:
        render_fn()
    except Exception:
        st.error(f"**{page_name}** encountered an error.")
        with st.expander("Error Details", expanded=False):
            st.code(traceback.format_exc(), language="python")


def main() -> None:
    """Main application entry point."""
    page = sidebar_navigation()

    if page in _ROUTE_RENDER_MAP:
        display_name, render_fn = _ROUTE_RENDER_MAP[page]
        # Pages manage their own titles via st.title()
        _safe_render(render_fn, display_name)
    else:
        _safe_render(render_home, "🏠 Home")

    render_footer()


if __name__ == "__main__":
    main()
