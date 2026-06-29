from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def create_probability_figure(prob_duplicate: float, threshold: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 2.8))
    categories = ["Non-Duplicate", "Duplicate"]
    values = [1.0 - prob_duplicate, prob_duplicate]
    colors = ["#64748B", "#2563EB"]
    bars = ax.barh(categories, values, color=colors)

    for bar, value in zip(bars, values):
        ax.text(value + 0.02, bar.get_y() + bar.get_height() / 2, f"{value:.2%}", va="center")

    ax.axvline(threshold, color="#DC2626", linestyle="--", linewidth=2, label=f"Threshold = {threshold:.2f}")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Probability")
    ax.set_title("Prediction Probability")
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


def create_confusion_matrix_figure(conf_matrix: np.ndarray) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    sns.heatmap(
        conf_matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Non-Duplicate", "Duplicate"],
        yticklabels=["Non-Duplicate", "Duplicate"],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    fig.tight_layout()
    return fig


def create_roc_curve_figure(fpr: np.ndarray, tpr: np.ndarray, roc_auc: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.plot(fpr, tpr, color="#2563EB", linewidth=2, label=f"ROC-AUC = {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="#94A3B8", linewidth=1.5)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


def create_pipeline_figure() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis("off")

    steps = [
        ("Week 1", "Collect + clean\nQuora question pairs"),
        ("Week 2", "TF-IDF / Word2Vec /\nSentence-BERT baselines"),
        ("Week 3", "DistilBERT fine-tuning\nfor pair classification"),
        ("Week 4", "Threshold tuning +\nerror analysis + weighting"),
        ("Week 5", "Streamlit app +\ndashboard + batch inference"),
    ]
    x_positions = np.linspace(0.1, 0.9, len(steps))

    for index, ((title, text), x_pos) in enumerate(zip(steps, x_positions)):
        ax.text(
            x_pos,
            0.55,
            f"{title}\n\n{text}",
            ha="center",
            va="center",
            fontsize=10,
            bbox={
                "boxstyle": "round,pad=0.6",
                "facecolor": "#EFF6FF" if index < len(steps) - 1 else "#DBEAFE",
                "edgecolor": "#2563EB",
                "linewidth": 1.5,
            },
        )
        if index < len(steps) - 1:
            ax.annotate(
                "",
                xy=(x_positions[index + 1] - 0.08, 0.55),
                xytext=(x_pos + 0.08, 0.55),
                arrowprops={"arrowstyle": "->", "lw": 2, "color": "#1D4ED8"},
            )

    fig.tight_layout()
    return fig


def create_batch_summary_figure(results_df: pd.DataFrame) -> plt.Figure:
    counts = results_df["prediction"].value_counts().reindex(["Duplicate", "Non-Duplicate"], fill_value=0)
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ax.bar(counts.index, counts.values, color=["#2563EB", "#64748B"])
    ax.set_ylabel("Count")
    ax.set_title("Batch Prediction Summary")
    for index, value in enumerate(counts.values):
        ax.text(index, value + max(counts.max() * 0.02, 0.1), str(int(value)), ha="center")
    fig.tight_layout()
    return fig
