from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def plot_latency_breakdown(
    latency_data: dict[str, float],
    save_path: Path,
    title: str = "Latency Breakdown by Module",
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    modules = list(latency_data.keys())
    values = list(latency_data.values())
    colors = plt.cm.Set2(np.linspace(0, 1, len(modules)))
    bars = ax.barh(modules, values, color=colors)
    for bar, v in zip(bars, values, strict=True):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2, f"{v:.2f}ms", va="center", fontsize=9)
    ax.set_xlabel("Latency (ms)")
    ax.set_title(title)
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_module_contribution(
    contribution_data: list[dict[str, Any]],
    save_path: Path,
    title: str = "Module Contribution (F1 Delta)",
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    modules = [d["module"] for d in contribution_data]
    deltas = [d.get("f1_delta", 0.0) for d in contribution_data]
    colors = ["#22C55E" if d >= 0 else "#EF4444" for d in deltas]
    bars = ax.barh(modules, deltas, color=colors)
    for bar, v in zip(bars, deltas, strict=True):
        ax.text(
            bar.get_width() + 0.001 if v >= 0 else bar.get_width() - 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{v:+.4f}",
            va="center",
            fontsize=9,
            ha="left" if v >= 0 else "right",
        )
    ax.axvline(0, color="black", linewidth=0.5)
    ax.set_xlabel("F1 Delta (positive = module improves performance)")
    ax.set_title(title)
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_ablation_comparison(
    ablation_df: pd.DataFrame,
    save_path: Path,
    title: str = "Ablation Study Comparison",
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    metrics = ["f1", "accuracy", "roc_auc"]
    x = np.arange(len(metrics))
    width = 0.12
    for i, (_, row) in enumerate(ablation_df.iterrows()):
        values = [row.get(m, 0.0) for m in metrics]
        offset = (i - len(ablation_df) / 2 + 0.5) * width
        ax.bar(x + offset, values, width, label=row.get("Config", row.get("module", f"cfg_{i}")))
    ax.set_xticks(x)
    ax.set_xticklabels([m.upper() for m in metrics])
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_routing_distribution(
    routing_metrics: dict[str, Any],
    save_path: Path,
    title: str = "Routing Pipeline Selection Distribution",
) -> None:
    selections = routing_metrics.get("pipeline_selections", {})
    if not selections:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No routing data", ha="center", va="center", fontsize=14)
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = list(selections.keys())
    values = list(selections.values())
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_agent_agreement_heatmap(
    agreement_matrix: dict[str, dict[str, float]],
    save_path: Path,
    title: str = "Agent Agreement Heatmap",
) -> None:
    if not agreement_matrix:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No agreement data", ha="center", va="center", fontsize=14)
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
        return
    agents = list(agreement_matrix.keys())
    matrix = np.array([[agreement_matrix[a].get(b, 0.0) for b in agents] for a in agents])
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(matrix, annot=True, fmt=".2f", cmap="YlOrRd", xticklabels=agents, yticklabels=agents, ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
