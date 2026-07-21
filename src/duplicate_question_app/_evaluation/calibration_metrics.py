from __future__ import annotations

import numpy as np

from duplicate_question_app._evaluation.metrics import compute_ece, compute_mce


def compute_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    return float(np.mean((y_prob - y_true) ** 2))


def compute_log_loss(y_true: np.ndarray, y_prob: np.ndarray, eps: float = 1e-15) -> float:
    y_prob = np.clip(y_prob, eps, 1 - eps)
    return float(-np.mean(y_true * np.log(y_prob) + (1 - y_true) * np.log(1 - y_prob)))


def compute_reliability_diagram(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> dict:
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bin_boundaries[:-1] + bin_boundaries[1:]) / 2
    bin_accuracies = []
    bin_confidences = []
    bin_counts = []
    for i in range(n_bins):
        mask = (y_prob >= bin_boundaries[i]) & (y_prob < bin_boundaries[i + 1])
        if i == n_bins - 1:
            mask = (y_prob >= bin_boundaries[i]) & (y_prob <= bin_boundaries[i + 1])
        count = int(mask.sum())
        bin_counts.append(count)
        if count > 0:
            bin_accuracies.append(float(y_true[mask].mean()))
            bin_confidences.append(float(y_prob[mask].mean()))
        else:
            bin_accuracies.append(0.0)
            bin_confidences.append(0.0)
    return {
        "bin_centers": bin_centers.tolist(),
        "bin_accuracies": bin_accuracies,
        "bin_confidences": bin_confidences,
        "bin_counts": bin_counts,
        "ece": compute_ece(y_prob, y_true, n_bins),
        "mce": compute_mce(y_prob, y_true, n_bins),
    }


def compute_confidence_histogram(y_prob: np.ndarray, n_bins: int = 20) -> dict:
    hist, edges = np.histogram(y_prob, bins=n_bins, range=(0, 1))
    return {
        "counts": hist.tolist(),
        "edges": edges.tolist(),
    }
