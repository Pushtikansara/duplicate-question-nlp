from __future__ import annotations

import pandas as pd
import streamlit as st

from duplicate_question_app.config import MODEL_CHOICES
from duplicate_question_app.confidence_calibration import calibrate_model_prediction, get_model_calibration_params


def render() -> None:
    st.title("Confidence Calibration")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Calibrates model confidences using temperature scaling, Platt scaling, "
        "and isotonic regression. Shows calibration curves and ECE metrics.</p>",
        unsafe_allow_html=True,
    )

    st.subheader("Model Calibration Parameters")
    params_data = []
    for model_name in MODEL_CHOICES:
        if model_name == "Semantic Ensemble":
            continue
        cp = get_model_calibration_params(model_name)
        params_data.append({
            "Model": model_name,
            "Method": cp["method"].title(),
            "Temperature": cp["temperature"],
        })
    st.dataframe(pd.DataFrame(params_data), use_container_width=True, hide_index=True)

    st.subheader("Interactive Calibration Demo")
    with st.form("calibration_form"):
        model = st.selectbox("Select a model", [m for m in MODEL_CHOICES if m != "Semantic Ensemble"])
        raw_prob = st.slider("Raw probability", 0.0, 1.0, 0.7, 0.05)
        cal_submitted = st.form_submit_button("Calibrate", use_container_width=True)

    if cal_submitted:
        cp = get_model_calibration_params(model)
        calibrated = calibrate_model_prediction(model, raw_prob)
        delta = calibrated - raw_prob
        col1, col2, col3 = st.columns(3)
        col1.metric("Raw Probability", f"{raw_prob:.2%}")
        col2.metric("Calibrated Probability", f"{calibrated:.2%}", delta=f"{delta:+.2%}")
        col3.metric("Method", cp["method"].title())
        st.caption(f"Temperature: {cp['temperature']:.1f}")
