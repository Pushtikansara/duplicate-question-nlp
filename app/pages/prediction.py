from __future__ import annotations

import time

import streamlit as st

from app.services.runtime import get_runtime_context
from app.utils.constants import get_model_prediction
from duplicate_question_app._visualization.plots import create_probability_figure


def render() -> None:
    st.title("Prediction Page")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Run live inference on individual question pairs with the selected model.</p>",
        unsafe_allow_html=True,
    )
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    try:
        service, metadata, _ = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return

    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        decision_threshold = metadata.get("decision_threshold", 0.5)
        device = metadata.get("device", "cpu")
    elif metadata:
        model_label = metadata.model_label
        decision_threshold = metadata.decision_threshold
        device = metadata.device
    else:
        model_label = selected_model
        decision_threshold = 0.5
        device = "cpu"

    st.caption(
        f"Running live inference with **{model_label}** on **{device}**. Decision threshold: **{decision_threshold:.2f}**."
    )

    with st.form("single_prediction_form"):
        question1 = st.text_area("Question 1", placeholder="Enter the first question", height=120)
        question2 = st.text_area("Question 2", placeholder="Enter the second question", height=120)
        submitted = st.form_submit_button("Predict Duplicate Status", use_container_width=True)

    if submitted:
        if not question1.strip() or not question2.strip():
            st.error("Both question fields are required.")
            return

        with st.spinner(f"Running inference with {model_label}..."):
            try:
                start_time = time.time()
                result = get_model_prediction(service, selected_model, question1, question2)
                result["inference_time"] = time.time() - start_time
            except Exception as exc:
                st.error(f"Prediction failed: {exc}")
                return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Prediction", result["prediction"])
        col2.metric("Confidence", f"{result['confidence']:.2%}")
        col3.metric("Probability (Duplicate)", f"{result['prob_duplicate']:.2%}")
        col4.metric("Threshold", f"{result['threshold']:.2f}")

        st.caption(f"Model: **{result['model_label']}** | ⏱️ Inference time: {result['inference_time'] * 1000:.1f} ms")

        if result.get("reason"):
            st.info(f"ℹ️ {result['reason']}")

        if result.get("feature_breakdown"):
            with st.expander("Model Contributions (Ensemble)"):
                for model_name, contrib in result["feature_breakdown"].items():
                    st.write(f"- **{model_name}**: duplicate probability = {contrib.get('prob_dup', 0):.4f}")

        st.success(f"Model decision: **{result['prediction']}** using **{result['model_label']}**.")
        probability_figure = create_probability_figure(
            prob_duplicate=float(result["prob_duplicate"]), threshold=float(result["threshold"])
        )
        st.pyplot(probability_figure, clear_figure=True)
