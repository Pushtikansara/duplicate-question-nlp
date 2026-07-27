from __future__ import annotations

import sys
from pathlib import Path

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


def _init_session_state() -> None:
    if "prediction_mode" not in st.session_state:
        st.session_state["prediction_mode"] = "fusion"


from app.pages import (
    render_adaptive_ensemble,
    render_advanced_calibration,
    render_advanced_explainability,
    render_agreement_dashboard,
    render_ares_dashboard,
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
    render_semantic_debugger,
)

st.set_page_config(
    page_title="DQD — Duplicate Question Detection",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()

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
    "Semantic Debugger": ("🐛 Semantic Debugger", render_semantic_debugger),
    "Dataset Information": ("📋 Dataset Info", render_dataset),
    "ARES Dashboard": ("🧠 ARES Dashboard", render_ares_dashboard),
}

_QUERY_PARAM_MODEL = "selected_model"


def _safe_render(render_fn, page_name: str) -> None:
    try:
        render_fn()
    except Exception as exc:
        import logging

        logging.getLogger("duplicate_question_app").error("Page '%s' failed: %s", page_name, exc, exc_info=True)
        st.error(f"**{page_name}** encountered an error and could not load.")
        st.info("Try selecting a different page or model from the sidebar.")


def _sync_model_from_query() -> None:
    query_params = st.query_params
    if _QUERY_PARAM_MODEL in query_params:
        model_from_query = query_params[_QUERY_PARAM_MODEL]
        if model_from_query != st.session_state.get("selected_model"):
            st.session_state["selected_model"] = model_from_query
            from app.utils.constants import _model_cache
            from duplicate_question_app._models.embeddings import clear_embedding_cache

            _model_cache.clear()
            clear_embedding_cache()


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Bootstrap: initialise the application context exactly once.
    #    This is the single place where AppPaths is created for the
    #    Streamlit process.  Every downstream consumer (sidebar, pages,
    #    services, ARES backends) receives the same paths object.
    # ------------------------------------------------------------------
    from app.context import ApplicationContext, initialize_context, render_startup_report
    from app.utils.constants import PROJECT_ROOT as _BOOT_ROOT

    if "app_context" not in st.session_state:
        from duplicate_question_app._config.settings import get_app_paths

        _paths = get_app_paths(_BOOT_ROOT)
        ctx: ApplicationContext = initialize_context(paths=_paths, validate=True)
        if ctx.has_errors():
            render_startup_report(ctx)

    # ------------------------------------------------------------------
    # 2. Session state defaults
    # ------------------------------------------------------------------
    _init_session_state()

    # ------------------------------------------------------------------
    # 3. Query parameter sync
    # ------------------------------------------------------------------
    _sync_model_from_query()

    # ------------------------------------------------------------------
    # 4. Sidebar navigation
    # ------------------------------------------------------------------
    page = sidebar_navigation()

    # ------------------------------------------------------------------
    # 5. Page rendering
    # ------------------------------------------------------------------
    if page in _ROUTE_RENDER_MAP:
        display_name, render_fn = _ROUTE_RENDER_MAP[page]
        _safe_render(render_fn, display_name)
    else:
        _safe_render(render_home, "🏠 Home")

    render_footer()


if __name__ == "__main__":
    main()
