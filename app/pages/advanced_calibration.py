from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from duplicate_question_app._calibration.v1 import calibrate_model_prediction
from duplicate_question_app._calibration.v2 import (
    CalibrationMethod,
    calibrate_predictions,
    get_calibration_curve_data,
)
from duplicate_question_app._config.settings import MODEL_CHOICES


def render() -> None:
    st.title("Advanced Confidence Calibration")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Calibrate model confidences using Temperature Scaling, Platt Scaling, and Isotonic Regression. "
        "Evaluate with ECE, MCE, Brier Score, and calibration curves.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Interactive Demo", "Batch Calibration", "Calibration Curves"])

    with tab1:
        st.subheader("Interactive Calibration Demo")
        with st.form("cal_v2_form"):
            model = st.selectbox("Select model", [m for m in MODEL_CHOICES if m != "Semantic Ensemble"])
            method = st.selectbox("Calibration method", [m.value for m in CalibrationMethod])
            raw_prob = st.slider("Raw probability", 0.0, 1.0, 0.7, 0.01)
            cal_submitted = st.form_submit_button("Calibrate", use_container_width=True)

        if cal_submitted:
            try:
                with st.spinner("Calibrating..."):
                    calibrated = calibrate_model_prediction(model, raw_prob)
                delta = calibrated - raw_prob
                col1, col2, col3 = st.columns(3)
                col1.metric("Raw Probability", f"{raw_prob:.2%}")
                col2.metric("Calibrated", f"{calibrated:.2%}", delta=f"{delta:+.2%}")
                col3.metric("Method", method.title())
            except Exception as exc:
                st.error(f"Calibration failed: {exc}")

    with tab2:
        st.subheader("Batch Calibration from Predictions")
        st.info("Upload a CSV with columns: true_label, prob_duplicate")
        uploaded = st.file_uploader("Upload predictions CSV", type=["csv"])

        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                if "true_label" in df.columns and "prob_duplicate" in df.columns:
                    y_true = df["true_label"].values
                    y_prob = df["prob_duplicate"].values

                    results = {}
                    for method in [CalibrationMethod.TEMPERATURE, CalibrationMethod.PLATT, CalibrationMethod.ISOTONIC]:
                        result = calibrate_predictions(y_prob, y_true, method)
                        results[method.value] = {
                            "ece_before": result.metrics_before.ece,
                            "ece_after": result.metrics_after.ece,
                            "brier_before": result.metrics_before.brier_score,
                            "brier_after": result.metrics_after.brier_score,
                            "params": result.parameters,
                        }

                    st.dataframe(pd.DataFrame(results).T, width="stretch")

                    best = min(results.items(), key=lambda x: x[1]["ece_after"])
                    st.success(f"Best method: {best[0]} (ECE: {best[1]['ece_after']:.4f})")
                else:
                    st.error("CSV must contain 'true_label' and 'prob_duplicate' columns")
            except Exception as exc:
                st.error(f"Batch calibration failed: {exc}")

    with tab3:
        st.subheader("Calibration Curve (Reliability Diagram)")
        st.info("Upload predictions to generate calibration curve")

        uploaded = st.file_uploader("Upload for calibration curve", type=["csv"], key="cal_curve")
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                if "true_label" in df.columns and "prob_duplicate" in df.columns:
                    y_true = df["true_label"].values
                    y_prob = df["prob_duplicate"].values

                    curve_data = get_calibration_curve_data(y_prob, y_true)

                    fig, ax = plt.subplots(figsize=(6, 5))
                    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect")
                    ax.plot(curve_data["bin_centers"], curve_data["bin_accuracies"], "o-", linewidth=2, markersize=8)
                    ax.set_xlabel("Mean Predicted Probability")
                    ax.set_ylabel("Fraction of Positives")
                    ax.set_title("Calibration Curve")
                    ax.legend()
                    ax.grid(alpha=0.3)
                    st.pyplot(fig, clear_figure=True)
            except Exception as exc:
                st.error(f"Curve generation failed: {exc}")
