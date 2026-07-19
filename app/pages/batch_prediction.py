from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.runtime import get_runtime_context
from app.utils.constants import _detect_question_columns, run_batch_prediction
from duplicate_question_app.visuals import create_batch_summary_figure


def render() -> None:
    st.title("Batch CSV Prediction")
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    try:
        service, metadata, _ = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return

    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        decision_threshold = metadata.get("decision_threshold", 0.5)
    elif metadata:
        model_label = metadata.model_label
        decision_threshold = metadata.decision_threshold
    else:
        model_label = selected_model
        decision_threshold = 0.5

    st.caption(f"Batch inference uses **{model_label}** with threshold **{decision_threshold:.2f}**.")

    template_df = pd.DataFrame(
        {
            "q1": ["How do I learn Python?", "What is the capital of France?"],
            "q2": ["How can I learn Python programming?", "Which city is the largest in France?"],
        }
    )
    st.download_button(
        "Download CSV Template",
        data=template_df.to_csv(index=False).encode("utf-8"),
        file_name="duplicate_question_template.csv",
        mime="text/csv",
    )

    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is None:
        st.info("Upload a CSV file with `q1/q2`, `question1/question2`, or `sentence1/sentence2` columns.")
        return

    try:
        batch_df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Unable to read the uploaded CSV: {exc}")
        return

    column_pair = _detect_question_columns(batch_df)
    if column_pair is None:
        st.error("Could not find valid question columns in the uploaded CSV.")
        return

    question1_column, question2_column = column_pair
    prepared_df = batch_df.copy()
    prepared_df[question1_column] = prepared_df[question1_column].fillna("").astype(str).str.strip()
    prepared_df[question2_column] = prepared_df[question2_column].fillna("").astype(str).str.strip()
    valid_mask = prepared_df[question1_column].ne("") & prepared_df[question2_column].ne("")

    col1, col2, col3 = st.columns(3)
    col1.metric("Uploaded Rows", f"{len(batch_df):,}")
    col2.metric("Valid Rows", f"{int(valid_mask.sum()):,}")
    col3.metric("Skipped Rows", f"{int((~valid_mask).sum()):,}")

    if (~valid_mask).any():
        st.warning("Rows with empty question text will be skipped.")
    st.subheader("Preview")
    st.dataframe(batch_df.head(10), use_container_width=True)

    if st.button("Run Batch Prediction", use_container_width=True):
        if not valid_mask.any():
            st.error("No valid rows found.")
            return
        try:
            question_pairs = list(
                zip(
                    prepared_df.loc[valid_mask, question1_column],
                    prepared_df.loc[valid_mask, question2_column],
                    strict=False,
                )
            )
            with st.spinner(f"Processing {len(question_pairs)} pairs with {model_label}..."):
                valid_results_df = run_batch_prediction(service, selected_model, question_pairs)
        except Exception as exc:
            st.error(f"Batch prediction failed: {exc}")
            return

        merged_results = batch_df.copy()
        merged_results["batch_status"] = "Skipped: empty question text"
        valid_index = prepared_df.index[valid_mask]
        merged_results.loc[valid_index, "batch_status"] = "Predicted"
        for column in valid_results_df.columns:
            merged_results[column] = pd.NA
            merged_results.loc[valid_index, column] = (
                valid_results_df[column].to_numpy()
                if hasattr(valid_results_df[column], "to_numpy")
                else valid_results_df[column].values
            )

        st.success(f"Generated predictions for {len(merged_results):,} question pairs.")
        st.dataframe(merged_results, use_container_width=True)
        summary_figure = create_batch_summary_figure(merged_results[merged_results["batch_status"] == "Predicted"])
        st.pyplot(summary_figure, clear_figure=True)
        st.download_button(
            "Download Prediction Results",
            data=merged_results.to_csv(index=False).encode("utf-8"),
            file_name="duplicate_question_predictions.csv",
            mime="text/csv",
        )
