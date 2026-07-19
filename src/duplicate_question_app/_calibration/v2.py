"""Confidence Calibration — implements Temperature Scaling, Platt Scaling, and Isotonic Regression.

Evaluates calibration using:
- Expected Calibration Error (ECE)
- Maximum Calibration Error (MCE)
- Brier Score
- Calibration Curves (reliability diagrams)
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

# Try to import sklearn
try:
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


class CalibrationMethod(Enum):
    NONE = "none"
    TEMPERATURE = "temperature"
    PLATT = "platt"
    ISOTONIC = "isotonic"


@dataclass
class CalibrationMetrics:
    """Calibration evaluation metrics."""

    ece: float  # Expected Calibration Error
    mce: float  # Maximum Calibration Error
    brier_score: float  # Brier Score
    nll: float  # Negative Log Likelihood
    n_samples: int
    n_bins: int = 10

    def to_dict(self) -> dict[str, Any]:
        return {
            "ece": self.ece,
            "mce": self.mce,
            "brier_score": self.brier_score,
            "nll": self.nll,
            "n_samples": self.n_samples,
            "n_bins": self.n_bins,
        }


@dataclass
class CalibrationResult:
    """Result of calibrating a set of predictions."""

    method: CalibrationMethod
    calibrated_probs: np.ndarray
    metrics_before: CalibrationMetrics
    metrics_after: CalibrationMetrics
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method.value,
            "calibrated_probs": self.calibrated_probs.tolist(),
            "metrics_before": self.metrics_before.to_dict(),
            "metrics_after": self.metrics_after.to_dict(),
            "parameters": self.parameters,
        }


def compute_ece(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Compute Expected Calibration Error."""
    if len(probs) == 0:
        return 0.0

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        if i == n_bins - 1:
            # Include right edge for last bin
            mask = (probs >= bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])

        if not mask.any():
            continue

        bin_conf = probs[mask].mean()
        bin_acc = labels[mask].mean()
        ece += np.abs(bin_acc - bin_conf) * mask.sum()

    return float(ece / len(probs)) if len(probs) > 0 else 0.0


def compute_mce(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Compute Maximum Calibration Error."""
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

        bin_conf = probs[mask].mean()
        bin_acc = labels[mask].mean()
        error = np.abs(bin_acc - bin_conf)
        max_error = max(max_error, error)

    return float(max_error)


def compute_brier_score(probs: np.ndarray, labels: np.ndarray) -> float:
    """Compute Brier Score (mean squared error)."""
    if len(probs) == 0:
        return 0.0
    return float(np.mean((probs - labels) ** 2))


def compute_nll(probs: np.ndarray, labels: np.ndarray) -> float:
    """Compute Negative Log Likelihood."""
    if len(probs) == 0:
        return 0.0
    eps = 1e-15
    probs_clipped = np.clip(probs, eps, 1.0 - eps)
    return float(-np.mean(labels * np.log(probs_clipped) + (1 - labels) * np.log(1 - probs_clipped)))


def evaluate_calibration(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10,
) -> CalibrationMetrics:
    """Evaluate calibration metrics for a set of predictions."""
    return CalibrationMetrics(
        ece=compute_ece(probs, labels, n_bins),
        mce=compute_mce(probs, labels, n_bins),
        brier_score=compute_brier_score(probs, labels),
        nll=compute_nll(probs, labels),
        n_samples=len(probs),
        n_bins=n_bins,
    )


def temperature_scale(probs: np.ndarray, temperature: float) -> np.ndarray:
    """Apply temperature scaling to probabilities.

    Temperature > 1.0 makes distribution more uniform (less confident).
    Temperature < 1.0 makes it more peaked (more confident).
    """
    # Convert probs to logits
    eps = 1e-8
    probs_clipped = np.clip(probs, eps, 1.0 - eps)
    logits = np.log(probs_clipped / (1.0 - probs_clipped))

    # Scale logits
    scaled_logits = logits / temperature

    # Convert back to probabilities
    return 1.0 / (1.0 + np.exp(-scaled_logits))


def find_optimal_temperature(
    probs: np.ndarray,
    labels: np.ndarray,
    temp_range: tuple[float, float] = (0.1, 5.0),
    n_steps: int = 100,
) -> float:
    """Find optimal temperature by minimizing NLL on validation set."""
    best_temp = 1.0
    best_nll = float("inf")

    for temp in np.linspace(temp_range[0], temp_range[1], n_steps):
        calibrated = temperature_scale(probs, temp)
        nll = compute_nll(calibrated, labels)
        if nll < best_nll:
            best_nll = nll
            best_temp = temp

    return best_temp


def platt_scale(
    probs: np.ndarray,
    labels: np.ndarray,
) -> tuple[Callable[[np.ndarray], np.ndarray], dict[str, float]]:
    """Fit Platt scaling (logistic regression on logits)."""
    if not _SKLEARN_AVAILABLE:
        # Fallback: simple sigmoid with learned parameters
        # Fit a,b in sigmoid(a * logit + b)
        eps = 1e-8
        probs_clipped = np.clip(probs, eps, 1.0 - eps)
        logits = np.log(probs_clipped / (1.0 - probs_clipped))

        # Simple grid search for a, b
        best_a, best_b = 1.0, 0.0
        best_nll = float("inf")

        for a in np.linspace(0.5, 2.0, 31):
            for b in np.linspace(-1.0, 1.0, 41):
                calibrated = 1.0 / (1.0 + np.exp(-(a * logits + b)))
                nll = compute_nll(calibrated, labels)
                if nll < best_nll:
                    best_nll = nll
                    best_a, best_b = a, b

        def transform(p: np.ndarray) -> np.ndarray:
            eps = 1e-8
            p_clipped = np.clip(p, eps, 1.0 - eps)
            logits_p = np.log(p_clipped / (1.0 - p_clipped))
            return 1.0 / (1.0 + np.exp(-(best_a * logits_p + best_b)))

        return transform, {"a": best_a, "b": best_b}

    # Use sklearn LogisticRegression
    eps = 1e-8
    probs_clipped = np.clip(probs, eps, 1.0 - eps)
    logits = np.log(probs_clipped / (1.0 - probs_clipped)).reshape(-1, 1)

    lr = LogisticRegression(solver="lbfgs", max_iter=1000)
    lr.fit(logits, labels)

    def transform(p: np.ndarray) -> np.ndarray:
        eps = 1e-8
        p_clipped = np.clip(p, eps, 1.0 - eps)
        logits_p = np.log(p_clipped / (1.0 - p_clipped)).reshape(-1, 1)
        return lr.predict_proba(logits_p)[:, 1]

    return transform, {"coef": float(lr.coef_[0][0]), "intercept": float(lr.intercept_[0])}


def isotonic_regression(
    probs: np.ndarray,
    labels: np.ndarray,
) -> tuple[Callable[[np.ndarray], np.ndarray], dict[str, Any]]:
    """Fit Isotonic Regression for calibration."""
    if not _SKLEARN_AVAILABLE:
        # Fallback: simple binning-based calibration
        n_bins = min(20, len(probs))
        bin_edges = np.percentile(probs, np.linspace(0, 100, n_bins + 1))
        bin_edges[0] = 0.0
        bin_edges[-1] = 1.0

        bin_probs = []
        bin_centers = []

        for i in range(n_bins):
            mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
            if i == n_bins - 1:
                mask = (probs >= bin_edges[i]) & (probs <= bin_edges[i + 1])
            if mask.any():
                bin_probs.append(labels[mask].mean())
                bin_centers.append(probs[mask].mean())
            else:
                bin_probs.append(bin_centers[-1] if bin_centers else 0.5)
                bin_centers.append((bin_edges[i] + bin_edges[i + 1]) / 2)

        # Ensure monotonicity
        bin_probs = np.array(bin_probs)
        for i in range(1, len(bin_probs)):
            if bin_probs[i] < bin_probs[i - 1]:
                bin_probs[i] = bin_probs[i - 1]

        def transform(p: np.ndarray) -> np.ndarray:
            return np.interp(p, bin_centers, bin_probs)

        return transform, {"bin_centers": bin_centers, "bin_probs": bin_probs.tolist()}

    # Use sklearn IsotonicRegression
    ir = IsotonicRegression(out_of_bounds="clip", increasing=True)
    ir.fit_transform(probs, labels)

    def transform(p: np.ndarray) -> np.ndarray:
        return ir.predict(p)

    return transform, {
        "thresholds": ir.X_thresholds_.tolist() if hasattr(ir, "X_thresholds_") else [],
        "y_thresholds": ir.y_thresholds_.tolist() if hasattr(ir, "y_thresholds_") else [],
    }


def calibrate_predictions(
    probs: np.ndarray,
    labels: np.ndarray,
    method: CalibrationMethod = CalibrationMethod.TEMPERATURE,
    val_split: float = 0.2,
    random_state: int = 42,
) -> CalibrationResult:
    """Calibrate predictions using specified method.

    Args:
        probs: Predicted probabilities (0-1)
        labels: True labels (0 or 1)
        method: Calibration method to use
        val_split: Fraction of data to use for fitting calibration
        random_state: Random seed for reproducibility

    Returns:
        CalibrationResult with calibrated probabilities and metrics
    """
    # Evaluate before calibration
    metrics_before = evaluate_calibration(probs, labels)

    if method == CalibrationMethod.NONE:
        return CalibrationResult(
            method=method,
            calibrated_probs=probs,
            metrics_before=metrics_before,
            metrics_after=metrics_before,
            parameters={},
        )

    # Split data for calibration fitting
    if len(probs) > 100:
        probs_train, probs_val, labels_train, labels_val = train_test_split(
            probs, labels, test_size=val_split, random_state=random_state, stratify=labels
        )
    else:
        probs_train, _probs_val = probs, probs
        labels_train, _labels_val = labels, labels

    # Fit calibration on training set
    if method == CalibrationMethod.TEMPERATURE:
        temp = find_optimal_temperature(probs_train, labels_train)

        def transform(p):
            return temperature_scale(p, temp)

        parameters = {"temperature": float(temp)}

    elif method == CalibrationMethod.PLATT:
        transform, params = platt_scale(probs_train, labels_train)
        parameters = params

    elif method == CalibrationMethod.ISOTONIC:
        transform, params = isotonic_regression(probs_train, labels_train)
        parameters = params

    else:
        raise ValueError(f"Unknown calibration method: {method}")

    # Apply to full set (or validation set for evaluation)
    calibrated_probs = transform(probs)

    # Evaluate after calibration
    metrics_after = evaluate_calibration(calibrated_probs, labels)

    return CalibrationResult(
        method=method,
        calibrated_probs=calibrated_probs,
        metrics_before=metrics_before,
        metrics_after=metrics_after,
        parameters=parameters,
    )


def select_best_calibration(
    probs: np.ndarray,
    labels: np.ndarray,
    methods: list[CalibrationMethod] | None = None,
) -> CalibrationResult:
    """Try multiple calibration methods and return the best one (by ECE)."""
    if methods is None:
        methods = [
            CalibrationMethod.NONE,
            CalibrationMethod.TEMPERATURE,
            CalibrationMethod.PLATT,
            CalibrationMethod.ISOTONIC,
        ]

    best_result = None
    best_ece = float("inf")

    for method in methods:
        try:
            result = calibrate_predictions(probs, labels, method)
            if result.metrics_after.ece < best_ece:
                best_ece = result.metrics_after.ece
                best_result = result
        except Exception:
            continue

    return best_result or calibrate_predictions(probs, labels, CalibrationMethod.NONE)


def get_calibration_curve_data(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10,
) -> dict[str, np.ndarray]:
    """Get data for calibration curve (reliability diagram) plotting."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_centers = []
    bin_accuracies = []
    bin_confidences = []
    bin_counts = []

    for i in range(n_bins):
        mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        if i == n_bins - 1:
            mask = (probs >= bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])

        if mask.any():
            bin_centers.append((bin_boundaries[i] + bin_boundaries[i + 1]) / 2)
            bin_accuracies.append(labels[mask].mean())
            bin_confidences.append(probs[mask].mean())
            bin_counts.append(mask.sum())
        else:
            bin_centers.append((bin_boundaries[i] + bin_boundaries[i + 1]) / 2)
            bin_accuracies.append(np.nan)
            bin_confidences.append(np.nan)
            bin_counts.append(0)

    return {
        "bin_centers": np.array(bin_centers),
        "bin_accuracies": np.array(bin_accuracies),
        "bin_confidences": np.array(bin_confidences),
        "bin_counts": np.array(bin_counts),
        "bin_boundaries": bin_boundaries,
    }


def save_calibration_params(model_name: str, result: CalibrationResult, path: Path) -> None:
    """Save calibration parameters to file."""
    data = {
        "model_name": model_name,
        "method": result.method.value,
        "parameters": result.parameters,
        "metrics_before": result.metrics_before.to_dict(),
        "metrics_after": result.metrics_after.to_dict(),
    }
    path.write_text(json.dumps(data, indent=2))


def load_calibration_params(path: Path) -> dict[str, Any] | None:
    """Load calibration parameters from file."""
    if not path.exists():
        return None
    return json.loads(path.read_text())
