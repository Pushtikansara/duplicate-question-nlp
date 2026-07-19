from __future__ import annotations

import streamlit as st

from app.services.runtime import get_model_resolution, get_runtime_context
from app.utils.constants import PATHS, _model_cache
from duplicate_question_app.config import MODEL_CHOICES
from duplicate_question_app.week2_inference import check_week2_artifacts


def sidebar_navigation() -> str:
    st.sidebar.title("🔬 DQD System")
    st.sidebar.markdown(
        "<div style='margin:-0.5rem 0 0.5rem 0;color:#64748B;font-size:0.78rem;'>Duplicate Question Detection</div>",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("### 📌 Main")
    main_pages = ["⏎ Home", "Prediction Page", "Batch CSV Prediction", "Model Comparison", "Performance Dashboard"]
    st.sidebar.markdown("### 🔬 Research")
    research_pages = [
        "Research: Model Agreement",
        "Research: Decision Trace",
        "Research: Calibration",
        "Research: Error Explorer",
    ]
    st.sidebar.markdown("### 🧪 Phase 3: False Positive Reduction")
    phase3_pages = [
        "Entity Detection",
        "Intent Detection",
        "Negation Detection",
        "Contradiction Detection",
        "Lexical Penalty",
        "Adaptive Ensemble V2",
        "Advanced Calibration",
        "Error Logger",
        "Agreement Dashboard",
        "Advanced Explainability",
        "Performance Optimizer",
        "Evaluation Suite",
        "Hard Test Generator",
    ]
    st.sidebar.markdown("### 🛠️ Developer")
    dev_pages = [
        "Model Manager",
        "Project Overview",
        "Dataset Information",
        "Pipeline",
        "Model Info",
        "Error Analysis",
        "Explainability",
    ]

    all_pages = main_pages + research_pages + phase3_pages + dev_pages

    default_page = st.session_state.get("current_page", "⏎ Home")
    default_idx = all_pages.index(default_page) if default_page in all_pages else 0

    selected = st.sidebar.radio("Navigate", all_pages, index=default_idx, key="nav", label_visibility="collapsed")
    st.session_state["current_page"] = selected

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 Model")
    prev_model = st.session_state.get("selected_model", None)
    model_sel = st.sidebar.selectbox(
        "Select model",
        MODEL_CHOICES,
        index=MODEL_CHOICES.index(prev_model) if prev_model in MODEL_CHOICES else 3,
        key="selected_model_widget",
        label_visibility="collapsed",
    )

    if model_sel != prev_model:
        st.session_state["selected_model"] = model_sel
        _model_cache.clear()
        import duplicate_question_app.embedding_models as em

        em._sentence_transformer_cache.clear()
        st.rerun()

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "Improved DistilBERT (Week 4)"

    resolution = get_model_resolution()
    model_name = st.session_state["selected_model"]
    try:
        _, metadata, _ = get_runtime_context()
        if isinstance(metadata, dict):
            st.sidebar.caption(f"Active: {metadata.get('model_label', model_name)[:30]}")
        elif metadata:
            st.sidebar.caption(f"Active: {metadata.model_label[:30]}")
        else:
            st.sidebar.caption(f"Active: {model_name[:30]}")
    except Exception:
        st.sidebar.caption(f"Active: {model_name[:30]}")

    week2_ready = all(check_week2_artifacts(PATHS).values())
    st.sidebar.caption(
        f"W2: {'✅' if week2_ready else '❌'}  W3: {'✅' if resolution.week3.ready else '❌'}  W4: {'✅' if resolution.week4.ready else '❌'}"
    )

    page_map: dict[str, str] = {
        "⏎ Home": "Landing Page",
        "Prediction Page": "Prediction Page",
        "Batch CSV Prediction": "Batch CSV Prediction",
        "Model Comparison": "Model Comparison",
        "Performance Dashboard": "Performance Dashboard",
        "Research: Model Agreement": "Research: Model Agreement",
        "Research: Decision Trace": "Research: Decision Trace",
        "Research: Calibration": "Research: Calibration",
        "Research: Error Explorer": "Research: Error Explorer",
        "Entity Detection": "Entity Detection",
        "Intent Detection": "Intent Detection",
        "Negation Detection": "Negation Detection",
        "Contradiction Detection": "Contradiction Detection",
        "Lexical Penalty": "Lexical Penalty",
        "Adaptive Ensemble V2": "Adaptive Ensemble V2",
        "Advanced Calibration": "Advanced Calibration",
        "Error Logger": "Error Logger",
        "Agreement Dashboard": "Agreement Dashboard",
        "Advanced Explainability": "Advanced Explainability",
        "Performance Optimizer": "Performance Optimizer",
        "Evaluation Suite": "Evaluation Suite",
        "Hard Test Generator": "Hard Test Generator",
        "Model Manager": "Model Manager",
        "Project Overview": "Project Overview",
        "Dataset Information": "Dataset Information",
        "Pipeline": "NLP Pipeline Visualization",
        "Model Info": "Model Information",
        "Error Analysis": "Error Analysis",
        "Explainability": "Explainability",
    }
    return page_map.get(selected, "Landing Page")
