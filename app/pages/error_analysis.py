from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.data import get_week3_analysis_frame, get_week4_predictions_df


def render() -> None:
    st.title("Error Analysis")
    week4_df = get_week4_predictions_df()
    week3_df = get_week3_analysis_frame()

    tabs = []
    if not week4_df.empty:
        tabs.append("Week 4")
    tabs.append("Week 3")
    tab_objects = st.tabs(tabs)

    def render_error_frame(title: str, df: pd.DataFrame, label_columns: tuple[str, str]) -> None:
        label_true, label_pred = label_columns
        working = df.copy()
        if "error_type" not in working.columns and {label_true, label_pred}.issubset(working.columns):
            working["error_type"] = "Correct"
            working.loc[(working[label_true] == 0) & (working[label_pred] == 1), "error_type"] = "False Positive"
            working.loc[(working[label_true] == 1) & (working[label_pred] == 0), "error_type"] = "False Negative"
        if "error_type" in working.columns:
            normalized_error = working["error_type"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
            normalized_error = normalized_error.mask(
                normalized_error.str.contains("False Positive", na=False), "False Positive"
            )
            normalized_error = normalized_error.mask(
                normalized_error.str.contains("False Negative", na=False), "False Negative"
            )
            normalized_error = normalized_error.mask(normalized_error.str.contains("Correct", na=False), "Correct")
            working["error_type"] = normalized_error
        if "confidence" not in working.columns and {"prob_duplicate", "prob_non_duplicate"}.issubset(working.columns):
            working["confidence"] = working[["prob_duplicate", "prob_non_duplicate"]].max(axis=1)
        if title == "Week 4":
            if "q1" not in working.columns and "question1" in working.columns:
                working["q1"] = working["question1"]
            if "q2" not in working.columns and "question2" in working.columns:
                working["q2"] = working["question2"]
            if "actual_class_name" not in working.columns and label_true in working.columns:
                working["actual_class_name"] = working[label_true].map({0: "Non-Duplicate", 1: "Duplicate"})
            if "predicted_class_name" not in working.columns and label_pred in working.columns:
                working["predicted_class_name"] = working[label_pred].map({0: "Non-Duplicate", 1: "Duplicate"})
        if working.empty or "error_type" not in working.columns:
            st.warning("Prediction artifacts are required for error analysis.")
            return
        error_df = working[working["error_type"] != "Correct"].copy()
        fp_df = working[working["error_type"] == "False Positive"].copy()
        fn_df = working[working["error_type"] == "False Negative"].copy()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Errors", f"{len(error_df):,}")
        col2.metric("False Positives", f"{len(fp_df):,}")
        col3.metric("False Negatives", f"{len(fn_df):,}")
        st.bar_chart(working["error_type"].value_counts())
        if not error_df.empty and "confidence" in error_df.columns:
            st.subheader("Most Confident Errors")
            display_cols = [
                col
                for col in [
                    "q1",
                    "q2",
                    "actual_class_name",
                    "predicted_class_name",
                    "confidence",
                    "prob_duplicate",
                    "error_type",
                ]
                if col in error_df.columns
            ]
            top_errors = error_df.nlargest(min(10, len(error_df)), "confidence")[display_cols]
            st.dataframe(top_errors, use_container_width=True)
        tab1, tab2 = st.tabs(["False Positives", "False Negatives"])
        with tab1:
            cols = [col for col in ["q1", "q2", "prob_duplicate", "confidence"] if col in fp_df.columns]
            st.dataframe(fp_df[cols].head(10), use_container_width=True)
        with tab2:
            cols = [col for col in ["q1", "q2", "prob_duplicate", "confidence"] if col in fn_df.columns]
            st.dataframe(fn_df[cols].head(10), use_container_width=True)

    tab_index = 0
    if not week4_df.empty:
        with tab_objects[tab_index]:
            render_error_frame("Week 4", week4_df, ("true_label", "pred_label"))
        tab_index += 1
    with tab_objects[tab_index]:
        render_error_frame("Week 3", week3_df, ("true_label", "predicted_label"))
