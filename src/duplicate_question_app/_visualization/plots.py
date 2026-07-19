from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
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
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.axis("off")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 6)

    # Define pipeline stages with detailed descriptions
    stages = [
        {
            "week": "Week 1",
            "title": "Data Collection & Cleaning",
            "desc": "Raw Quora question pairs\nDeduplication & cleaning\nEDA & preprocessing",
            "color": "#3B82F6",
            "icon": "📊",
        },
        {
            "week": "Week 2",
            "title": "Classical Baselines",
            "desc": "TF-IDF (1,2)-gram features\nWord2Vec / Sentence-BERT\nLR & SVM classifiers",
            "color": "#8B5CF6",
            "icon": "🔬",
        },
        {
            "week": "Week 3",
            "title": "DistilBERT Fine-Tuning",
            "desc": "Transformer pair encoding\nSequence classification head\nThreshold=0.50 baseline",
            "color": "#EC4899",
            "icon": "🧠",
        },
        {
            "week": "Week 4",
            "title": "Performance Improvement",
            "desc": "Threshold tuning (best F1)\nClass weight balancing\nError analysis & ablation",
            "color": "#F59E0B",
            "icon": "⚡",
        },
        {
            "week": "Week 5",
            "title": "Deployment & Dashboard",
            "desc": "Streamlit interactive app\nModel selection (4 models)\nBatch inference & visuals",
            "color": "#10B981",
            "icon": "🚀",
        },
    ]

    n_stages = len(stages)
    box_w = 2.5
    box_h = 3.2
    gap = (16 - n_stages * box_w) / (n_stages + 1)

    for i, stage in enumerate(stages):
        x_center = gap + i * (box_w + gap) + box_w / 2

        # Draw main box with rounded corners
        rect_bg = FancyBboxPatch(
            (x_center - box_w / 2, 1.2), box_w, box_h,
            boxstyle="round,pad=0.08,rounding_size=0.2",
            facecolor="#F8FAFC", edgecolor=stage["color"],
            linewidth=2.5, zorder=2,
        )
        ax.add_patch(rect_bg)

        # Top accent bar with rounded top corners
        accent = FancyBboxPatch(
            (x_center - box_w / 2, 1.2 + box_h - 0.55), box_w, 0.55,
            boxstyle="round,pad=0.08,rounding_size=0.2",
            facecolor=stage["color"], alpha=0.15, zorder=3,
            linewidth=0,
        )
        ax.add_patch(accent)

        # Week label (top left corner of box)
        ax.text(
            x_center - box_w / 2 + 0.15, 1.2 + box_h - 0.4,
            stage["week"],
            fontsize=9, fontweight="bold",
            color=stage["color"], ha="left", va="center", zorder=4,
        )

        # Icon
        ax.text(
            x_center + box_w / 2 - 0.25, 1.2 + box_h - 0.4,
            stage["icon"], fontsize=14, ha="center", va="center", zorder=4,
        )

        # Title
        ax.text(
            x_center, 1.2 + box_h - 0.95,
            stage["title"],
            fontsize=10, fontweight="bold",
            color="#1E293B", ha="center", va="center", zorder=4,
        )

        # Description
        ax.text(
            x_center, 1.2 + box_h / 2 - 0.2,
            stage["desc"],
            fontsize=8.5, color="#475569",
            ha="center", va="center", zorder=4,
            linespacing=1.5,
        )

        # Arrow to next stage
        if i < n_stages - 1:
            next_x = gap + (i + 1) * (box_w + gap) + box_w / 2
            ax.annotate(
                "",
                xy=(next_x - box_w / 2 - 0.15, 2.8),
                xytext=(x_center + box_w / 2 + 0.15, 2.8),
                arrowprops={
                    "arrowstyle": "->",
                    "lw": 2.5,
                    "color": "#94A3B8",
                    "connectionstyle": "arc3,rad=0",
                },
                zorder=1,
            )

    # Title at the top
    ax.text(
        8, 5.6, "NLP Pipeline — Duplicate Question Detection",
        fontsize=14, fontweight="bold", color="#0F172A",
        ha="center", va="center",
    )

    # Subtitle
    ax.text(
        8, 5.15, "From raw data collection to production-grade deployment across 5 weekly iterations",
        fontsize=9, color="#64748B", ha="center", va="center",
    )

    # Bottom metrics summary
    metrics_info = (
        "📦 400k+ question pairs  |  🔤 4 model architectures  |  🎯 Best F1: 0.8996 (Week 4)  |  ⚡ Live inference in browser"
    )
    ax.text(
        8, 0.5, metrics_info,
        fontsize=8.5, color="#64748B", ha="center", va="center",
        style="italic",
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
