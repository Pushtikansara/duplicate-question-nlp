from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def safe_metric(value: Any, percent: bool = True, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if percent:
        return f"{float(value):.{decimals}%}"
    return f"{float(value):.{decimals}f}"


def metric_card_row(metrics: dict[str, Any]) -> None:
    accuracy = metrics.get("accuracy")
    precision = metrics.get("precision")
    recall = metrics.get("recall")
    f1 = metrics.get("f1")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Accuracy", safe_metric(accuracy))
    col2.metric("Precision", safe_metric(precision))
    col3.metric("Recall", safe_metric(recall))
    col4.metric("F1 Score", safe_metric(f1))
