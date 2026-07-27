from __future__ import annotations

import pandas as pd
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
from duplicate_question_app._inference.cache import get_cache
from duplicate_question_app._profiling import get_profiler
from duplicate_question_app._visualization.plots import create_confusion_matrix_figure, create_roc_curve_figure


def _render_live_performance() -> None:
    st.subheader("Live Pipeline Profiling")
    profiler = get_profiler()
    report = profiler.get_report()

    if not report:
        st.info("No profiling data collected yet. Make some predictions first.")
        return

    report_df = pd.DataFrame(report)
    st.dataframe(
        report_df,
        width="stretch",
        hide_index=True,
        column_config={
            "name": "Component",
            "call_count": "Calls",
            "total_ms": st.column_config.NumberColumn("Total (ms)", format="%.1f"),
            "avg_ms": st.column_config.NumberColumn("Avg (ms)", format="%.2f"),
            "min_ms": st.column_config.NumberColumn("Min (ms)", format="%.2f"),
            "max_ms": st.column_config.NumberColumn("Max (ms)", format="%.2f"),
        },
    )

    col1, col2 = st.columns(2)
    with col1:
        chart_df = report_df.set_index("name")[["avg_ms", "max_ms"]]
        st.subheader("Average & Max Latency by Component (ms)")
        st.bar_chart(chart_df)
    with col2:
        count_df = report_df.set_index("name")[["call_count"]]
        st.subheader("Call Count by Component")
        st.bar_chart(count_df)


def _render_cache_performance() -> None:
    st.subheader("Cache Performance")
    cache = get_cache()
    stats = cache.stats()

    cache_rows = []
    for name, stat in stats.items():
        cache_rows.append(
            {
                "Cache": name.replace("_", " ").title(),
                "Size": stat.size,
                "Max Size": stat.max_size if stat.max_size > 0 else -1,
                "Hits": stat.hits,
                "Misses": stat.misses,
                "Hit Rate": f"{stat.hit_rate:.1%}",
                "Evictions": stat.evictions,
            }
        )

    if cache_rows:
        st.dataframe(pd.DataFrame(cache_rows), width="stretch", hide_index=True)
    else:
        st.info("No cache statistics available.")

    if st.button("Reset Profiler", type="secondary"):
        profiler = get_profiler()
        profiler.reset()
        st.rerun()

    if st.button("Clear All Caches", type="secondary"):
        cache.clear_all()
        st.rerun()


def _render_semantic_intelligence_performance() -> None:
    st.subheader("Semantic Intelligence Performance")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Semantic Intelligence Engine performance statistics. "
        "Real profiling measurements from the pipeline are displayed below.</p>",
        unsafe_allow_html=True,
    )

    profiler = get_profiler()
    report = profiler.get_report()

    sie_rows = [
        s
        for s in report
        if any(
            k in s["name"].lower()
            for k in ["semantic", "concept", "entity", "intent", "relation", "conflict", "fusion"]
        )
    ]
    if sie_rows:
        st.markdown("**Semantic Intelligence Timing Breakdown**")
        sie_df = pd.DataFrame(sie_rows)
        st.dataframe(sie_df, width="stretch", hide_index=True)
        if not sie_df.empty:
            timing_chart = sie_df.set_index("name")[["avg_ms", "max_ms"]]
            st.bar_chart(timing_chart)
    else:
        st.info("No semantic intelligence profiling data collected yet. Run predictions to see measurements.")


def render() -> None:
    st.title("Performance Dashboard")
    week3_metrics = get_transformer_metrics()
    week4_metrics = get_week4_metrics()

    tabs = st.tabs(
        ["Week 4 (Improved)", "Week 3 (Baseline)", "Comparison", "Semantic Intelligence", "Live Profiling", "Cache"]
    )

    with tabs[0]:
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
                    st.dataframe(threshold_df, width="stretch")
            week4_ablation = get_week4_ablation_df()
            if not week4_ablation.empty:
                with st.expander("Ablation Study", expanded=True):
                    st.dataframe(week4_ablation, width="stretch")

    with tabs[1]:
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
                st.dataframe(comparison_df, width="stretch")
                if "Method" in comparison_df.columns:
                    chart_cols = [
                        col for col in ["Accuracy", "Precision", "Recall", "F1 Score"] if col in comparison_df.columns
                    ]
                    if chart_cols:
                        st.bar_chart(comparison_df.set_index("Method")[chart_cols])
            else:
                st.info("Week 2 vs Week 3 comparison not available.")

    with tabs[2]:
        comparison_df = build_model_comparison_table()
        st.dataframe(format_model_comparison_for_display(comparison_df), width="stretch", hide_index=True)
        chart_df = comparison_df.set_index("Model")[["Accuracy", "Precision", "Recall", "F1 Score"]].dropna(
            axis=1, how="all"
        )
        if not chart_df.empty:
            st.bar_chart(chart_df)

    with tabs[3]:
        _render_semantic_intelligence_performance()

    with tabs[4]:
        _render_live_performance()

    with tabs[5]:
        _render_cache_performance()
