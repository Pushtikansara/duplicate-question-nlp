from __future__ import annotations

import streamlit as st

from app.components.footer import render_footer
from app.components.helpers import inject_styles
from app.components.sidebar import sidebar_navigation
from app.pages import (
    render_home,
    render_overview,
    render_dataset,
    render_pipeline,
    render_models,
    render_prediction,
    render_batch_prediction,
    render_model_comparison,
    render_performance,
    render_error_analysis,
    render_explainability,
    render_model_agreement,
    render_calibration,
    render_error_explorer,
    render_entity_detection,
    render_intent_detection,
    render_negation_detection,
    render_contradiction_detection,
    render_lexical_penalty,
    render_adaptive_ensemble,
    render_advanced_calibration,
    render_error_logger,
    render_agreement_dashboard,
    render_advanced_explainability,
    render_performance_optimizer,
    render_evaluation_suite,
    render_hard_test_generator,
    render_model_manager,
)

st.set_page_config(
    page_title="Duplicate Question Detection",
    page_icon="NLP",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()


def main() -> None:
    page = sidebar_navigation()

    route_map = {
        "Landing Page": render_home,
        "Model Manager": render_model_manager,
        "Research: Model Agreement": render_model_agreement,
        "Research: Decision Trace": render_model_agreement,
        "Research: Calibration": render_calibration,
        "Research: Error Explorer": render_error_explorer,
        "Entity Detection": render_entity_detection,
        "Intent Detection": render_intent_detection,
        "Negation Detection": render_negation_detection,
        "Contradiction Detection": render_contradiction_detection,
        "Lexical Penalty": render_lexical_penalty,
        "Adaptive Ensemble V2": render_adaptive_ensemble,
        "Advanced Calibration": render_advanced_calibration,
        "Error Logger": render_error_logger,
        "Agreement Dashboard": render_agreement_dashboard,
        "Advanced Explainability": render_advanced_explainability,
        "Performance Optimizer": render_performance_optimizer,
        "Evaluation Suite": render_evaluation_suite,
        "Hard Test Generator": render_hard_test_generator,
        "Project Overview": render_overview,
        "Dataset Information": render_dataset,
        "NLP Pipeline Visualization": render_pipeline,
        "Model Information": render_models,
        "Model Comparison": render_model_comparison,
        "Prediction Page": render_prediction,
        "Batch CSV Prediction": render_batch_prediction,
        "Performance Dashboard": render_performance,
        "Error Analysis": render_error_analysis,
        "Explainability": render_explainability,
    }

    render_fn = route_map.get(page, render_home)
    render_fn()
    render_footer()


if __name__ == "__main__":
    main()
