from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.data import get_dataset, get_dataset_summary


def render() -> None:
    st.title("Dataset Information")
    try:
        df = get_dataset()
        summary = get_dataset_summary()
    except Exception as exc:
        st.error(f"Dataset could not be loaded: {exc}")
        return
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{summary['rows']:,}")
    col2.metric("Duplicate", f"{summary['label_counts'].get(1, 0):,}")
    col3.metric("Non-Duplicate", f"{summary['label_counts'].get(0, 0):,}")
    col4.metric("Columns", len(summary["columns"]))
    tab_summary, tab_quality, tab_preview = st.tabs(["Summary", "Data Quality", "Preview"])
    with tab_summary:
        st.subheader("Columns")
        st.write(summary["columns"])
        label_counts = pd.Series(summary["label_counts"]).rename(index={0: "Non-Duplicate", 1: "Duplicate"})
        if not label_counts.empty:
            st.subheader("Class Distribution")
            st.bar_chart(label_counts)
    with tab_quality:
        st.subheader("Missing Values")
        missing_df = pd.DataFrame.from_dict(
            summary["missing_values"], orient="index", columns=["missing_count"]
        ).sort_values("missing_count", ascending=False)
        st.dataframe(missing_df, width="stretch")
    with tab_preview:
        st.subheader("Sample Records")
        st.dataframe(summary["preview"], width="stretch")
        if {"clean_q1", "clean_q2"}.issubset(df.columns):
            st.subheader("Cleaned Text Samples")
            st.dataframe(df[["clean_q1", "clean_q2"]].head(10), width="stretch")
