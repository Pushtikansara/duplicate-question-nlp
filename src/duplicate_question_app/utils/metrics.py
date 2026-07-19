"""Shared calibration and evaluation metrics.

Provides canonical implementations of ECE, MCE, and Brier score
that multiple modules (evaluation, calibration, agreement dashboard)
rely on.  These are the primary definitions; callers in other packages
should delegate here to avoid drift.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def compute_ece(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error.

    Args:
        probs: Predicted probabilities (shape ``(n,)``).
        labels: Ground-truth binary labels (shape ``(n,)``).
        n_bins: Number of equal-width bins in [0, 1].

    Returns:
        ECE value (lower is better).  Returns 0.0 for empty input.
    """
    if len(probs) == 0:
        return 0.0
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        if i == n_bins - 1:
            mask = (probs >= bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
        if not mask.any():
            continue
        bin_conf = float(probs[mask].mean())
        bin_acc = float(labels[mask].mean())
        ece += abs(bin_acc - bin_conf) * int(mask.sum())
    return float(ece / len(probs)) if len(probs) > 0 else 0.0


def compute_mce(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Maximum Calibration Error.

    Args:
        probs: Predicted probabilities (shape ``(n,)``).
        labels: Ground-truth binary labels (shape ``(n,)``).
        n_bins: Number of equal-width bins in [0, 1].

    Returns:
        MCE value (lower is better).  Returns 0.0 for empty input.
    """
    if len(probs) == 0:
        return 0.0
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    max_error = 0.0
    for i in range(n_bins):
        mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        if i == n_bins - 1:
            mask = (probs >= bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
        if not mask.any():
            continue
        bin_conf = float(probs[mask].mean())
        bin_acc = float(labels[mask].mean())
        max_error = max(max_error, abs(bin_acc - bin_conf))
    return float(max_error)
