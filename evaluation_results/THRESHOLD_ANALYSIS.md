# Threshold Optimization Analysis

*Generated: 2026-07-27T23:08:39*

## Summary

For every working model, we performed a complete threshold sweep
from 0.00 to 1.00 (step = 0.01) computing Accuracy, Precision,
Recall, F1, MCC, Balanced Accuracy, Specificity, Sensitivity,
FPR, FNR, and Cost (FP+FN).

We identified 5 optimal thresholds per model:
- Best F1 Threshold (primary recommendation)
- Best Accuracy Threshold
- Best MCC Threshold
- Best Balanced Accuracy Threshold
- Lowest Cost Threshold

## DistilBERT (Week 3)

- **Current Threshold**: 0.50
- **Current F1**: 0.8967

### Optimal Thresholds

| Metric | Threshold | F1 | Accuracy | Precision | Recall | MCC |
|--------|-----------|----|----------|-----------|--------|-----|
| Best F1 | 0.81 | 0.9012 | 0.9258 | 0.8686 | 0.9364 | 0.8434 |
| Best Accuracy | 0.91 | 0.9011 | 0.9274 | 0.8873 | 0.9153 | 0.8440 |
| Best MCC | 0.91 | 0.9011 | 0.9274 | 0.8873 | 0.9153 | 0.8440 |
| Best Balanced Accuracy | 0.39 | 0.8966 | 0.9194 | 0.8359 | 0.9668 | 0.8370 |
| Lowest Cost | 0.91 | 0.9011 | 0.9274 | 0.8873 | 0.9153 | 0.8440 |

### Threshold Explanation

The optimal threshold (0.81) is higher than the current threshold (0.50). This indicates the model's positive class probabilities are underestimated — increasing the threshold improves precision without sacrificing too much recall.

- Precision: 0.8424 → 0.8686
- Recall: 0.9585 → 0.9364

### Cost & Error Analysis

- **Current**: FP=324, FN=75, Total=399
- **Optimal F1**: FP=256.0, FN=115.0, Total=371.0
- **Errors saved**: 28.0
- **Sensitivity (Recall)**: 0.9585 → 0.9364
- **Specificity**: 0.8985 → 0.9198

## Improved DistilBERT (Week 4)

- **Current Threshold**: 0.50
- **Current F1**: 0.9539

### Optimal Thresholds

| Metric | Threshold | F1 | Accuracy | Precision | Recall | MCC |
|--------|-----------|----|----------|-----------|--------|-----|
| Best F1 | 0.82 | 0.9559 | 0.9676 | 0.9410 | 0.9712 | 0.9306 |
| Best Accuracy | 0.82 | 0.9559 | 0.9676 | 0.9410 | 0.9712 | 0.9306 |
| Best MCC | 0.82 | 0.9559 | 0.9676 | 0.9410 | 0.9712 | 0.9306 |
| Best Balanced Accuracy | 0.60 | 0.9554 | 0.9672 | 0.9386 | 0.9729 | 0.9299 |
| Lowest Cost | 0.82 | 0.9559 | 0.9676 | 0.9410 | 0.9712 | 0.9306 |

### Threshold Explanation

The optimal threshold (0.82) is higher than the current threshold (0.50). This indicates the model's positive class probabilities are underestimated — increasing the threshold improves precision without sacrificing too much recall.

- Precision: 0.9356 → 0.9410
- Recall: 0.9729 → 0.9712

### Cost & Error Analysis

- **Current**: FP=121, FN=49, Total=170
- **Optimal F1**: FP=110.0, FN=52.0, Total=162.0
- **Errors saved**: 8.0
- **Sensitivity (Recall)**: 0.9729 → 0.9712
- **Specificity**: 0.9621 → 0.9655

## Cross-Encoder-Quora (Trained)

- **Current Threshold**: 0.10
- **Current F1**: 0.8536

### Optimal Thresholds

| Metric | Threshold | F1 | Accuracy | Precision | Recall | MCC |
|--------|-----------|----|----------|-----------|--------|-----|
| Best F1 | 0.52 | 0.8758 | 0.9066 | 0.8429 | 0.9115 | 0.8027 |
| Best Accuracy | 0.64 | 0.8750 | 0.9074 | 0.8541 | 0.8971 | 0.8022 |
| Best MCC | 0.56 | 0.8758 | 0.9070 | 0.8466 | 0.9070 | 0.8028 |
| Best Balanced Accuracy | 0.52 | 0.8758 | 0.9066 | 0.8429 | 0.9115 | 0.8027 |
| Lowest Cost | 0.64 | 0.8750 | 0.9074 | 0.8541 | 0.8971 | 0.8022 |

### Threshold Explanation

The optimal threshold (0.52) is higher than the current threshold (0.10). This indicates the model's positive class probabilities are underestimated — increasing the threshold improves precision without sacrificing too much recall.

- Precision: 0.7726 → 0.8429
- Recall: 0.9535 → 0.9115

### Cost & Error Analysis

- **Current**: FP=507, FN=84, Total=591
- **Optimal F1**: FP=307.0, FN=160.0, Total=467.0
- **Errors saved**: 124.0
- **Sensitivity (Recall)**: 0.9535 → 0.9115
- **Specificity**: 0.8412 → 0.9039

## MPNet-base-v2

- **Current Threshold**: 0.36
- **Current F1**: 0.7593

### Optimal Thresholds

| Metric | Threshold | F1 | Accuracy | Precision | Recall | MCC |
|--------|-----------|----|----------|-----------|--------|-----|
| Best F1 | 0.37 | 0.7605 | 0.8014 | 0.6739 | 0.8727 | 0.6102 |
| Best Accuracy | 0.52 | 0.7469 | 0.8138 | 0.7340 | 0.7604 | 0.6000 |
| Best MCC | 0.44 | 0.7602 | 0.8114 | 0.7032 | 0.8273 | 0.6119 |
| Best Balanced Accuracy | 0.37 | 0.7605 | 0.8014 | 0.6739 | 0.8727 | 0.6102 |
| Lowest Cost | 0.52 | 0.7469 | 0.8138 | 0.7340 | 0.7604 | 0.6000 |

### Threshold Explanation

The current threshold (0.36) is essentially optimal for MPNet-base-v2. F1 gain from retuning would be only 0.0012.

### Cost & Error Analysis

- **Current**: FP=786, FN=220, Total=1006
- **Optimal F1**: FP=763.0, FN=230.0, Total=993.0
- **Errors saved**: 13.0
- **Sensitivity (Recall)**: 0.8783 → 0.8727
- **Specificity**: 0.7538 → 0.7610

## BGE-base-en-v1.5

- **Current Threshold**: 0.30
- **Current F1**: 0.7290

### Optimal Thresholds

| Metric | Threshold | F1 | Accuracy | Precision | Recall | MCC |
|--------|-----------|----|----------|-----------|--------|-----|
| Best F1 | 0.29 | 0.7313 | 0.7610 | 0.6159 | 0.8998 | 0.5603 |
| Best Accuracy | 0.52 | 0.7022 | 0.7878 | 0.7124 | 0.6923 | 0.5376 |
| Best MCC | 0.29 | 0.7313 | 0.7610 | 0.6159 | 0.8998 | 0.5603 |
| Best Balanced Accuracy | 0.29 | 0.7313 | 0.7610 | 0.6159 | 0.8998 | 0.5603 |
| Lowest Cost | 0.52 | 0.7022 | 0.7878 | 0.7124 | 0.6923 | 0.5376 |

### Threshold Explanation

The current threshold (0.30) is essentially optimal for BGE-base-en-v1.5. F1 gain from retuning would be only 0.0023.

### Cost & Error Analysis

- **Current**: FP=993, FN=201, Total=1194
- **Optimal F1**: FP=1014.0, FN=181.0, Total=1195.0
- **Errors saved**: 0
- **Sensitivity (Recall)**: 0.8888 → 0.8998
- **Specificity**: 0.6890 → 0.6824

## E5-base-v2

- **Current Threshold**: 0.35
- **Current F1**: 0.5611

### Optimal Thresholds

| Metric | Threshold | F1 | Accuracy | Precision | Recall | MCC |
|--------|-----------|----|----------|-----------|--------|-----|
| Best F1 | 0.59 | 0.7068 | 0.7376 | 0.5928 | 0.8749 | 0.5150 |
| Best Accuracy | 0.62 | 0.6915 | 0.7628 | 0.6524 | 0.7355 | 0.5023 |
| Best MCC | 0.59 | 0.7068 | 0.7376 | 0.5928 | 0.8749 | 0.5150 |
| Best Balanced Accuracy | 0.60 | 0.7064 | 0.7500 | 0.6136 | 0.8323 | 0.5148 |
| Lowest Cost | 0.62 | 0.6915 | 0.7628 | 0.6524 | 0.7355 | 0.5023 |

### Threshold Explanation

The optimal threshold (0.59) is higher than the current threshold (0.35). This indicates the model's positive class probabilities are underestimated — increasing the threshold improves precision without sacrificing too much recall.

- Precision: 0.3899 → 0.5928
- Recall: 1.0000 → 0.8749

### Cost & Error Analysis

- **Current**: FP=2827, FN=0, Total=2827
- **Optimal F1**: FP=1086.0, FN=226.0, Total=1312.0
- **Errors saved**: 1515.0
- **Sensitivity (Recall)**: 1.0000 → 0.8749
- **Specificity**: 0.1146 → 0.6599

## E5-quora-finetuned

- **Current Threshold**: 0.40
- **Current F1**: 0.7323

### Optimal Thresholds

| Metric | Threshold | F1 | Accuracy | Precision | Recall | MCC |
|--------|-----------|----|----------|-----------|--------|-----|
| Best F1 | 0.63 | 0.7667 | 0.8098 | 0.6885 | 0.8650 | 0.6210 |
| Best Accuracy | 0.67 | 0.7628 | 0.8142 | 0.7081 | 0.8268 | 0.6166 |
| Best MCC | 0.63 | 0.7667 | 0.8098 | 0.6885 | 0.8650 | 0.6210 |
| Best Balanced Accuracy | 0.59 | 0.7663 | 0.8032 | 0.6712 | 0.8926 | 0.6204 |
| Lowest Cost | 0.67 | 0.7628 | 0.8142 | 0.7081 | 0.8268 | 0.6166 |

### Threshold Explanation

The optimal threshold (0.63) is higher than the current threshold (0.40). This indicates the model's positive class probabilities are underestimated — increasing the threshold improves precision without sacrificing too much recall.

- Precision: 0.5883 → 0.6885
- Recall: 0.9696 → 0.8650

### Cost & Error Analysis

- **Current**: FP=1226, FN=55, Total=1281
- **Optimal F1**: FP=707.0, FN=244.0, Total=951.0
- **Errors saved**: 330.0
- **Sensitivity (Recall)**: 0.9696 → 0.8650
- **Specificity**: 0.6160 → 0.7786
