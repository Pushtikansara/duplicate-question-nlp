from __future__ import annotations

import streamlit as st

from app.components.metric_cards import metric_card_row
from app.services.data import get_week4_metrics, get_week4_plot_paths, get_week4_threshold_df, get_week4_ablation_df, get_week4_predictions_df


def render() -> None:
    st.title("Explainability and Results")
    week4_plots = get_week4_plot_paths()
    week4_threshold_df = get_week4_threshold_df()
    week4_ablation = get_week4_ablation_df()
    week4_predictions = get_week4_predictions_df()
    week4_metrics = get_week4_metrics()

    if not week4_plots and week4_threshold_df.empty and week4_ablation.empty and week4_predictions.empty:
        st.info("Week 4 exported artifacts are not fully available yet.")
        return

    tab_overview, tab_threshold, tab_ablation, tab_predictions, tab_visuals = st.tabs(["Overview", "Threshold Tuning", "Ablation", "Predictions", "Visuals"])
    with tab_overview:
        if week4_metrics:
            metric_card_row(week4_metrics)
        st.write("Week 4 focuses on threshold tuning, handling class imbalance, and deeper error analysis.")
        col1, col2, col3 = st.columns(3)
        col1.metric("Plots Found", len(week4_plots))
        col2.metric("Threshold Rows", f"{len(week4_threshold_df):,}")
        col3.metric("Prediction Rows", f"{len(week4_predictions):,}")
    with tab_threshold:
        if week4_threshold_df.empty:
            st.info("Threshold analysis is not available.")
        else:
            if {"Threshold", "F1"}.issubset(week4_threshold_df.columns):
                best_f1 = float(week4_threshold_df["F1"].max())
                best_threshold = float(week4_threshold_df.loc[week4_threshold_df["F1"] == best_f1, "Threshold"].astype(float).max())
                col1, col2 = st.columns(2)
                col1.metric("Selected Threshold", f"{best_threshold:.2f}")
                col2.metric("Best F1", f"{best_f1:.3f}")
            st.dataframe(week4_threshold_df, use_container_width=True)
    with tab_ablation:
        if week4_ablation.empty:
            st.info("Ablation study table is not available.")
        else:
            st.dataframe(week4_ablation, use_container_width=True)
    with tab_predictions:
        if week4_predictions.empty:
            st.info("Week 4 prediction export is not available.")
        else:
            st.dataframe(week4_predictions.head(25), use_container_width=True)
    with tab_visuals:
        if not week4_plots:
            st.info("No exported Week 4 visuals were found.")
        else:
            for plot_path in week4_plots:
                st.image(str(plot_path), caption=plot_path.name, use_container_width=True)
