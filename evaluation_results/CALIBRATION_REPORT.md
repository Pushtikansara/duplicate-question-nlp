# Confidence Calibration Report

*Generated: 2026-07-27T23:08:39*

## Executive Summary

We evaluated 4 calibration methods for each model:
1. **Raw Confidence** (no calibration — baseline)
2. **Temperature Scaling** (single parameter T > 0)
3. **Platt Scaling** (logistic regression on logit space)
4. **Isotonic Regression** (non-parametric monotonic mapping)

The best method minimizes **Expected Calibration Error (ECE)**
without reducing F1 score.

## DistilBERT (Week 3)

- **Raw ECE**: 0.0564
- **Raw MCE**: 0.3746
- **Raw Brier**: 0.0702

### Calibration Method Comparison

| Method | ECE Before | ECE After | MCE Before | MCE After | Brier Before | Brier After | F1 After |
|--------|------------|-----------|------------|-----------|--------------|-------------|----------|
| none | 0.0564 | 0.0564 | 0.3746 | 0.3746 | 0.0702 | 0.0702 | 0.9226 |
| temperature | 0.0564 | 0.0163 | 0.3746 | 0.2047 | 0.0702 | 0.0647 | 0.9226 |
| platt | 0.0564 | 0.0144 | 0.3746 | 0.2140 | 0.0702 | 0.0641 | 0.9226 |
| isotonic | 0.0564 | 0.0024 | 0.3746 | 0.3103 | 0.0702 | 0.0614 | 0.9224 |

**Best Method**: isotonic
**Best ECE**: 0.0024

See RELIABILITY_DIAGRAMS/ for visual reliability diagrams.

## Improved DistilBERT (Week 4)

- **Raw ECE**: 0.0434
- **Raw MCE**: 0.3614
- **Raw Brier**: 0.0447

### Calibration Method Comparison

| Method | ECE Before | ECE After | MCE Before | MCE After | Brier Before | Brier After | F1 After |
|--------|------------|-----------|------------|-----------|--------------|-------------|----------|
| none | 0.0434 | 0.0434 | 0.3614 | 0.3614 | 0.0447 | 0.0447 | 0.9539 |
| temperature | 0.0434 | 0.0186 | 0.3614 | 0.2327 | 0.0447 | 0.0396 | 0.9539 |
| platt | 0.0434 | 0.0185 | 0.3614 | 0.2336 | 0.0447 | 0.0397 | 0.9539 |
| isotonic | 0.0434 | 0.0044 | 0.3614 | 0.0445 | 0.0447 | 0.0363 | 0.9543 |

**Best Method**: isotonic
**Best ECE**: 0.0044

See RELIABILITY_DIAGRAMS/ for visual reliability diagrams.

## Cross-Encoder-Quora (Trained)

- **Raw ECE**: 0.0660
- **Raw MCE**: 0.2471
- **Raw Brier**: 0.0883

### Calibration Method Comparison

| Method | ECE Before | ECE After | MCE Before | MCE After | Brier Before | Brier After | F1 After |
|--------|------------|-----------|------------|-----------|--------------|-------------|----------|
| none | 0.0660 | 0.0660 | 0.2471 | 0.2471 | 0.0883 | 0.0883 | 0.9014 |
| temperature | 0.0660 | 0.0367 | 0.2471 | 0.1687 | 0.0883 | 0.0834 | 0.9009 |
| platt | 0.0660 | 0.0275 | 0.2471 | 0.1434 | 0.0883 | 0.0813 | 0.9014 |
| isotonic | 0.0660 | 0.0072 | 0.2471 | 0.5172 | 0.0883 | 0.0785 | 0.9018 |

**Best Method**: isotonic
**Best ECE**: 0.0072

See RELIABILITY_DIAGRAMS/ for visual reliability diagrams.

## MPNet-base-v2

- **Raw ECE**: 0.0860
- **Raw MCE**: 0.8750
- **Raw Brier**: 0.1517

### Calibration Method Comparison

| Method | ECE Before | ECE After | MCE Before | MCE After | Brier Before | Brier After | F1 After |
|--------|------------|-----------|------------|-----------|--------------|-------------|----------|
| none | 0.0860 | 0.0860 | 0.8750 | 0.8750 | 0.1517 | 0.1517 | 0.8203 |
| temperature | 0.0860 | 0.1089 | 0.8750 | 0.8750 | 0.1517 | 0.1534 | 0.8205 |
| platt | 0.0860 | 0.0454 | 0.8750 | 0.8750 | 0.1517 | 0.1421 | 0.8204 |
| isotonic | 0.0860 | 0.0058 | 0.8750 | 0.0708 | 0.1517 | 0.1372 | 0.8204 |

**Best Method**: isotonic
**Best ECE**: 0.0058

See RELIABILITY_DIAGRAMS/ for visual reliability diagrams.

## BGE-base-en-v1.5

- **Raw ECE**: 0.0925
- **Raw MCE**: 0.7668
- **Raw Brier**: 0.1641

### Calibration Method Comparison

| Method | ECE Before | ECE After | MCE Before | MCE After | Brier Before | Brier After | F1 After |
|--------|------------|-----------|------------|-----------|--------------|-------------|----------|
| none | 0.0925 | 0.0925 | 0.7668 | 0.7668 | 0.1641 | 0.1641 | 0.8053 |
| temperature | 0.0925 | 0.1114 | 0.7668 | 0.8750 | 0.1641 | 0.1652 | 0.8053 |
| platt | 0.0925 | 0.0524 | 0.7668 | 0.8750 | 0.1641 | 0.1545 | 0.8056 |
| isotonic | 0.0925 | 0.0086 | 0.7668 | 0.0166 | 0.1641 | 0.1486 | 0.8052 |

**Best Method**: isotonic
**Best ECE**: 0.0086

See RELIABILITY_DIAGRAMS/ for visual reliability diagrams.

## E5-base-v2

- **Raw ECE**: 0.1632
- **Raw MCE**: 0.8750
- **Raw Brier**: 0.2110

### Calibration Method Comparison

| Method | ECE Before | ECE After | MCE Before | MCE After | Brier Before | Brier After | F1 After |
|--------|------------|-----------|------------|-----------|--------------|-------------|----------|
| none | 0.1632 | 0.1632 | 0.8750 | 0.8750 | 0.2110 | 0.2110 | 0.7964 |
| temperature | 0.1632 | 0.1304 | 0.8750 | 0.8750 | 0.2110 | 0.2241 | 0.7942 |
| platt | 0.1632 | 0.1776 | 0.8750 | 0.8750 | 0.2110 | 0.2046 | 0.7946 |
| isotonic | 0.1632 | 0.0042 | 0.8750 | 0.1500 | 0.2110 | 0.1604 | 0.7964 |

**Best Method**: isotonic
**Best ECE**: 0.0042

See RELIABILITY_DIAGRAMS/ for visual reliability diagrams.

## E5-quora-finetuned

- **Raw ECE**: 0.0549
- **Raw MCE**: 0.1978
- **Raw Brier**: 0.1409

### Calibration Method Comparison

| Method | ECE Before | ECE After | MCE Before | MCE After | Brier Before | Brier After | F1 After |
|--------|------------|-----------|------------|-----------|--------------|-------------|----------|
| none | 0.0549 | 0.0549 | 0.1978 | 0.1978 | 0.1409 | 0.1409 | 0.8314 |
| temperature | 0.0549 | 0.0603 | 0.1978 | 0.8750 | 0.1409 | 0.1433 | 0.8314 |
| platt | 0.0549 | 0.0586 | 0.1978 | 0.8750 | 0.1409 | 0.1407 | 0.8314 |
| isotonic | 0.0549 | 0.0065 | 0.1978 | 0.0218 | 0.1409 | 0.1332 | 0.8316 |

**Best Method**: isotonic
**Best ECE**: 0.0065

See RELIABILITY_DIAGRAMS/ for visual reliability diagrams.

## Cross-Model Comparison

| Model | Raw ECE | Best ECE | ECE Reduction | Best Method | Raw Brier |
|-------|---------|----------|---------------|-------------|-----------|
| DistilBERT (Week 3) | 0.0564 | 0.0024 | 0.0540 | isotonic | 0.0702 |
| Improved DistilBERT (Week 4) | 0.0434 | 0.0044 | 0.0390 | isotonic | 0.0447 |
| Cross-Encoder-Quora (Trained) | 0.0660 | 0.0072 | 0.0588 | isotonic | 0.0883 |
| MPNet-base-v2 | 0.0860 | 0.0058 | 0.0803 | isotonic | 0.1517 |
| BGE-base-en-v1.5 | 0.0925 | 0.0086 | 0.0838 | isotonic | 0.1641 |
| E5-base-v2 | 0.1632 | 0.0042 | 0.1590 | isotonic | 0.2110 |
| E5-quora-finetuned | 0.0549 | 0.0065 | 0.0484 | isotonic | 0.1409 |

## Recommendations per Model

### DistilBERT (Week 3)
- **CALIBRATE**: Apply isotonic scaling (ECE: 0.0564 → 0.0024)

### Improved DistilBERT (Week 4)
- **CALIBRATE**: Apply isotonic scaling (ECE: 0.0434 → 0.0044)

### Cross-Encoder-Quora (Trained)
- **RETUNE**: Change threshold from 0.10 to 0.52 (F1 gain: 0.0222)
- **CALIBRATE**: Apply isotonic scaling (ECE: 0.0660 → 0.0072)

### MPNet-base-v2
- **CALIBRATE**: Apply isotonic scaling (ECE: 0.0860 → 0.0058)

### BGE-base-en-v1.5
- **CALIBRATE**: Apply isotonic scaling (ECE: 0.0925 → 0.0086)

### E5-base-v2
- **RETUNE**: Change threshold from 0.35 to 0.59 (F1 gain: 0.1457)
- **CALIBRATE**: Apply isotonic scaling (ECE: 0.1632 → 0.0042)

### E5-quora-finetuned
- **RETUNE**: Change threshold from 0.40 to 0.63 (F1 gain: 0.0345)
- **CALIBRATE**: Apply isotonic scaling (ECE: 0.0549 → 0.0065)

## Final Recommendation Table

| Model | Cur Th | Opt Th | Cur F1 | Opt F1 | Cur ECE | Opt ECE | Recommendation |
|-------|--------|--------|--------|--------|---------|---------|----------------|
| DistilBERT (Week 3) | 0.50 | 0.81 | 0.8967 | 0.9012 | 0.0564 | 0.0024 | CALIBRATE (isotonic) |
| Improved DistilBERT (Week 4) | 0.50 | 0.82 | 0.9539 | 0.9559 | 0.0434 | 0.0044 | CALIBRATE (isotonic) |
| Cross-Encoder-Quora (Trained) | 0.10 | 0.52 | 0.8536 | 0.8758 | 0.0660 | 0.0072 | RETUNE to 0.52 + CALIBRATE (isotonic) |
| MPNet-base-v2 | 0.36 | 0.37 | 0.7593 | 0.7605 | 0.0860 | 0.0058 | CALIBRATE (isotonic) |
| BGE-base-en-v1.5 | 0.30 | 0.29 | 0.7290 | 0.7313 | 0.0925 | 0.0086 | CALIBRATE (isotonic) |
| E5-base-v2 | 0.35 | 0.59 | 0.5611 | 0.7068 | 0.1632 | 0.0042 | RETUNE to 0.59 + CALIBRATE (isotonic) |
| E5-quora-finetuned | 0.40 | 0.63 | 0.7323 | 0.7667 | 0.0549 | 0.0065 | RETUNE to 0.63 + CALIBRATE (isotonic) |

## Special Investigations

### Step 6: E5-base-v2 Investigation

Determine whether poor performance is caused by threshold, calibration, or the model itself.

- **Current F1 at threshold 0.35**: 0.5611
- **Best F1 at threshold 0.59**: 0.7068
- **F1 improvement**: 0.1457 (26.0% relative)

**Verdict: E5-base-v2 is a fundamentally capable model with a suboptimal threshold.** The current threshold of 0.35 is far from optimal (0.59). Retuning alone recovers ~0.146 F1 points. This model does NOT need retraining — it needs RETUNE.

**Recommendation: RETUNE** — Change threshold from 0.35 to 0.59 in configs/inference.yaml.

### Step 7: Week 4 DistilBERT Investigation

Determine whether Week 4 DistilBERT already operates at its optimal threshold.

- **Current threshold**: 0.50
- **Current F1**: 0.9539
- **Optimal threshold**: 0.82
- **Optimal F1**: 0.9559
- **F1 gain**: 0.0020

**Verdict: Week 4 DistilBERT is operating at its optimal threshold.** The current threshold of 0.50 yields F1=0.9539, which is within 0.01 of the optimal. No retuning needed.

**Recommendation: KEEP** current threshold of 0.50.

### Step 8: Cross-Encoder Threshold=0.10 Investigation

Determine whether threshold=0.10 is actually optimal.

- **Current threshold**: 0.10 (from configs/inference.yaml)
- **Current F1**: 0.8536
- **Optimal F1 threshold**: 0.52
- **Optimal F1**: 0.8758
- **F1 gain**: 0.0222 (2.6% relative)
- **Precision tradeoff**: 0.7726 → 0.8429
- **Recall tradeoff**: 0.9535 → 0.9115

**Verdict: The current threshold of 0.10 is NOT optimal.** This extremely low threshold was likely chosen to maximize recall, but it comes at a significant precision cost. The optimal F1 threshold is 0.52, which improves F1 by 0.0222.

**Recommendation: RETUNE** the threshold. However, do NOT automatically replace threshold 0.10 without considering the application's precision-recall tradeoff preference:
- **Low threshold (0.10)**: Maximizes recall, suitable when missing a duplicate is costly.
- **Optimal threshold (0.52)**: Balances precision and recall for best F1.
- **High threshold (>0.60)**: Maximizes precision, suitable when false positives are costly.

The optimal F1 threshold should be the default. If the application requires maximum recall, keep 0.10 but be aware of the precision cost.
