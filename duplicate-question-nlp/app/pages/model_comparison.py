from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.metric_cards import safe_metric
from app.services.builder import build_model_comparison_table, format_model_comparison_for_display


def render() -> None:
    st.title("Model Comparison")
    st.write("Side-by-side comparison across all models: Week 2 classical baselines, Week 3/4 transformers, and Phase 2 embedding models.")

    comparison_df = build_model_comparison_table()
    display_df = format_model_comparison_for_display(comparison_df)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    metric_columns = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"]
    chart_df = comparison_df.set_index("Model")[metric_columns].dropna(axis=1, how="all")
    if not chart_df.empty:
        st.subheader("Metric Comparison")
        st.bar_chart(chart_df)

    week4_row = comparison_df[comparison_df["Model"] == "Improved DistilBERT (Week 4)"]
    week3_row = comparison_df[comparison_df["Model"] == "DistilBERT (Week 3)"]
    if not week4_row.empty and not week3_row.empty:
        wk4_f1 = week4_row.iloc[0]["F1 Score"]
        wk3_f1 = week3_row.iloc[0]["F1 Score"]
        wk4_acc = week4_row.iloc[0]["Accuracy"]
        wk3_acc = week3_row.iloc[0]["Accuracy"]
        col1, col2 = st.columns(2)
        if not pd.isna(wk4_f1) and not pd.isna(wk3_f1):
            col1.metric("Week 4 F1", safe_metric(wk4_f1), delta=f"{wk4_f1 - wk3_f1:+.2%}")
        if not pd.isna(wk4_acc) and not pd.isna(wk3_acc):
            col2.metric("Week 4 Accuracy", safe_metric(wk4_acc), delta=f"{wk4_acc - wk3_acc:+.2%}")

    st.subheader("Model Details")
    detail_data = {
        "Model": comparison_df["Model"].tolist(),
        "Type": ["Classical ML", "Classical ML", "Transformer", "Transformer", "Bi-Encoder", "Bi-Encoder", "Bi-Encoder", "Cross-Encoder", "Ensemble"],
        "Parameters": ["~10K features", "~10K features", "66.9M", "66.9M", "110M", "118M", "110M", "184M", "Varies"],
    }
    st.dataframe(pd.DataFrame(detail_data), use_container_width=True, hide_index=True)
