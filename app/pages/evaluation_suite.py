from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from duplicate_question_app.evaluation import (
    compare_models,
    generate_evaluation_report,
    generate_model_comparison_plots,
)


def render() -> None:
    st.title("Model Evaluation & Comparison")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Generate Confusion Matrix, ROC, PR Curve, Calibration Curve, "
        "Top 100 hardest failures, per-model comparison, FP/FN reports.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Single Model Evaluation", "Multi-Model Comparison"])

    with tab1:
        st.subheader("Single Model Evaluation")
        uploaded = st.file_uploader("Upload predictions CSV", type=["csv"])
        model_name = st.text_input("Model name", "Adaptive Ensemble V2")
        output_dir = st.text_input("Output directory", "evaluation_results")

        if uploaded and st.button("Generate Report"):
            with st.spinner("Generating evaluation report..."):
                try:
                    df = pd.read_csv(uploaded)
                    summary = generate_evaluation_report(df, Path(output_dir), model_name=model_name)
                    st.success("Report generated!")
                    st.json(summary)

                    for name, path in summary["plots"].items():
                        if Path(path).exists():
                            st.image(path, caption=name)
                except Exception as exc:
                    st.error(f"Evaluation failed: {exc}")

    with tab2:
        st.subheader("Multi-Model Comparison")
        st.info("Upload multiple CSVs, one per model, with same true_label column")

        uploaded_files = st.file_uploader("Upload model predictions", type=["csv"], accept_multiple_files=True)
        model_names = st.text_input("Model names (comma-separated)", "Model A, Model B, Model C")

        if uploaded_files and st.button("Compare Models"):
            try:
                names = [n.strip() for n in model_names.split(",")]
                predictions_dict = {}
                for name, file in zip(names, uploaded_files, strict=False):
                    predictions_dict[name] = pd.read_csv(file)

                comparison_df = compare_models(predictions_dict)
                st.dataframe(comparison_df, use_container_width=True)

                output_dir = Path("comparison_plots")
                plot_paths = generate_model_comparison_plots(predictions_dict, output_dir)
                for name, path in plot_paths.items():
                    if Path(path).exists():
                        st.image(path, caption=name)
            except Exception as exc:
                st.error(f"Comparison failed: {exc}")
