# ARES Confidence Calibration

## Overview

Calibration metrics measure how well a model's predicted probabilities
reflect true outcome frequencies. A perfectly calibrated model has ECE=0,
meaning predictions at confidence level p are correct exactly p% of the time.

## Key Metrics

### ECE (Expected Calibration Error)

Weighted average of the absolute difference between accuracy and confidence
across bins. Computed via `compute_ece()` in `metrics.py`.

```
ECE = sum(n_i * |acc_i - conf_i|) / N
```

Lower is better. ECE < 0.05 is generally considered well-calibrated.

### MCE (Maximum Calibration Error)

Maximum absolute difference between accuracy and confidence across all bins.
Identifies the worst-calibrated region of the probability spectrum.

```
MCE = max(|acc_i - conf_i|)
```

### Brier Score

Mean squared error between predicted probabilities and binary outcomes.
Range [0, 1]; 0 is perfect.

```
Brier = mean((y_prob - y_true)^2)
```

### Log Loss

Negative log-likelihood of the true labels under the predicted probabilities.
Range [0, inf); 0 is perfect.

```
LogLoss = -mean(y_true * log(y_prob) + (1 - y_true) * log(1 - y_prob))
```

## Reliability Diagram

`compute_reliability_diagram()` bins predicted probabilities into `n_bins=10`
equal-width bins and computes per-bin accuracy and confidence. Returns:

- `bin_centers`: midpoints of each bin
- `bin_accuracies`: observed accuracy within each bin
- `bin_confidences`: mean predicted probability within each bin
- `bin_counts`: number of samples per bin
- `ece`: Expected Calibration Error
- `mce`: Maximum Calibration Error

A well-calibrated model has accuracy approximately equal to confidence for
all bins (data points lie near the diagonal).

## Confidence Histogram

`compute_confidence_histogram()` distributes predicted probabilities into
`n_bins=20` bins, returning histogram counts and edge values. A healthy
model shows a bimodal distribution with peaks near 0 and 1.

## Calibration Comparison Across Configurations

The calibration report and calibration_comparison.png figure allow comparing
ECE and reliability diagrams across all 5 benchmark configurations. Key
patterns to observe:

- **Baseline (CrossEncoder)**: typically lowest ECE due to conservative
  probability estimates.
- **Config D (Full ARES)**: may show higher ECE if added modules introduce
  overconfidence without commensurate accuracy gains.
- **Config B (+Reasoning)**: reasoning chain confidence scores can inflate
  overall probability estimates.

### Example Calibration Values

| Config | ECE | MCE | Brier |
|---|---|---|---|
| Baseline (CrossEncoder) | 0.398 | 0.481 | 0.412 |
| Config A (+Semantic) | 0.424 | 0.574 | 0.436 |
| Config B (+Reasoning) | 0.438 | 0.669 | 0.447 |
| Config C (+MADE) | 0.444 | 0.666 | 0.453 |
| Config D (Full ARES) | 0.451 | 0.676 | 0.458 |

## Usage

```python
import numpy as np
from duplicate_question_app._evaluation import (
    compute_reliability_diagram,
    compute_confidence_histogram,
    compute_brier_score,
    compute_log_loss,
)

y_true = np.array([1, 0, 1, 0, 1])
y_prob = np.array([0.9, 0.1, 0.8, 0.2, 0.7])

rd = compute_reliability_diagram(y_true, y_prob)
hist = compute_confidence_histogram(y_prob)
brier = compute_brier_score(y_true, y_prob)
logloss = compute_log_loss(y_true, y_prob)

print(f"ECE: {rd['ece']:.4f}, MCE: {rd['mce']:.4f}, Brier: {brier:.4f}")
```
