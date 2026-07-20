from __future__ import annotations

import streamlit as st

from app.components.metric_cards import metric_card_row
from app.services.builder import build_model_comparison_table, format_model_comparison_for_display
from app.services.data import (
    get_transformer_metrics,
    get_week2_vs_week3,
    get_week4_ablation_df,
    get_week4_metrics,
    get_week4_threshold_df,
)
from duplicate_question_app._visualization.plots import create_confusion_matrix_figure, create_roc_curve_figure


def render() -> None:
    st.title("Performance Dashboard")
    week3_metrics = get_transformer_metrics()
    week4_metrics = get_week4_metrics()

    tab_week4, tab_week3, tab_compare = st.tabs(["Week 4 (Improved)", "Week 3 (Baseline)", "Comparison"])

    with tab_week4:
        if not week4_metrics:
            st.info("Week 4 prediction artifacts are not available.")
        else:
            metric_card_row(week4_metrics)
            cm_col, roc_col = st.columns(2)
            with cm_col:
                st.subheader("Confusion Matrix")
                st.pyplot(create_confusion_matrix_figure(week4_metrics["confusion_matrix"]), clear_figure=True)
            with roc_col:
                st.subheader("ROC Curve")
                roc_curve_data = week4_metrics.get("roc_curve")
                roc_auc = week4_metrics.get("roc_auc")
                if roc_curve_data and roc_auc is not None:
                    st.pyplot(
                        create_roc_curve_figure(roc_curve_data["fpr"], roc_curve_data["tpr"], roc_auc),
                        clear_figure=True,
                    )
                else:
                    st.info("ROC data is not available.")
            threshold_df = get_week4_threshold_df()
            if not threshold_df.empty and {"Threshold", "F1"}.issubset(threshold_df.columns):
                best_f1 = float(threshold_df["F1"].max())
                best_threshold = float(threshold_df.loc[threshold_df["F1"] == best_f1, "Threshold"].astype(float).max())
                col1, col2 = st.columns(2)
                col1.metric("Best Threshold", f"{best_threshold:.2f}")
                col2.metric("Best F1 (tuning)", f"{best_f1:.3f}")
                with st.expander("Threshold Tuning Table"):
                    st.dataframe(threshold_df, use_container_width=True)
            week4_ablation = get_week4_ablation_df()
            if not week4_ablation.empty:
                with st.expander("Ablation Study", expanded=True):
                    st.dataframe(week4_ablation, use_container_width=True)

    with tab_week3:
        if not week3_metrics:
            st.warning("Week 3 prediction artifacts are missing.")
        else:
            metric_card_row(week3_metrics)
            cm_col, roc_col = st.columns(2)
            with cm_col:
                st.subheader("Confusion Matrix")
                st.pyplot(create_confusion_matrix_figure(week3_metrics["confusion_matrix"]), clear_figure=True)
            with roc_col:
                st.subheader("ROC Curve")
                roc_curve_data = week3_metrics.get("roc_curve")
                roc_auc = week3_metrics.get("roc_auc")
                if roc_curve_data and roc_auc is not None:
                    st.pyplot(
                        create_roc_curve_figure(roc_curve_data["fpr"], roc_curve_data["tpr"], roc_auc),
                        clear_figure=True,
                    )
                else:
                    st.info("ROC data is not available.")
            comparison_df = get_week2_vs_week3()
            st.subheader("Week 2 vs Week 3 Comparison")
            if not comparison_df.empty:
                st.dataframe(comparison_df, use_container_width=True)
                if "Method" in comparison_df.columns:
                    chart_cols = [
                        col for col in ["Accuracy", "Precision", "Recall", "F1 Score"] if col in comparison_df.columns
                    ]
                    if chart_cols:
                        st.bar_chart(comparison_df.set_index("Method")[chart_cols])
            else:
                st.info("Week 2 vs Week 3 comparison not available.")

    with tab_compare:
        comparison_df = build_model_comparison_table()
        st.dataframe(format_model_comparison_for_display(comparison_df), use_container_width=True, hide_index=True)
        chart_df = comparison_df.set_index("Model")[["Accuracy", "Precision", "Recall", "F1 Score"]].dropna(
            axis=1, how="all"
        )
        if not chart_df.empty:
            st.bar_chart(chart_df)
