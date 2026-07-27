# Phase 10.6.5 — Label Mapping Audit

## Convention

Throughout the entire codebase:

| Index | Display Label | Quora `is_duplicate` |
|-------|---------------|---------------------|
| 0 | Non-Duplicate | 0 |
| 1 | Duplicate | 1 |

## Verification by Module

### transformer.py (DistilBERT)
```python
# Line 239-240:
prob_non_duplicate = float(probabilities[0].item())
prob_duplicate = float(probabilities[1].item())

# Line 285:
predicted_label = int(prob_duplicate >= self.metadata.decision_threshold)

# Line 294:
"prediction": "Duplicate" if predicted_label == 1 else "Non-Duplicate"
```
**Mapping: index 0 → non-duplicate, index 1 → duplicate. ✓**

### embeddings.py (Cross-Encoders)
```python
# Line 233 (cross-encoder binary):
prob_duplicate = float(scores[1])  # index 1 = duplicate

# Line 230 (cross-encoder NLI):
prob_duplicate = entail / denom  # entailment = duplicate

# Line 254:
pred_label = int(prob_duplicate >= threshold)
```
**Mapping: index 1 → duplicate (binary), entailment → duplicate (NLI). ✓**

### embeddings.py (Bi-Encoders)
```python
# Line 250:
prob_duplicate = 1.0 / (1.0 + np.exp(-steepness * (similarity - midpoint)))

# Line 254:
pred_label = int(prob_duplicate >= threshold)
```
**Mapping: sigmoid(similarity) → duplicate probability. ✓**

### week2.py (Classical ML)
```python
# Lines 149-151:
prob_duplicate = float(proba[1])  # sklearn predict_proba returns [p0, p1]
predicted_label = int(prob_duplicate >= 0.5)

# Line 172:
"prediction": "Duplicate" if predicted_label == 1 else "Non-Duplicate"
```
**Mapping: index 1 → duplicate. ✓**

### Training Verification

From `train_cross_encoder.py`:
```python
# Line 267: num_labels=2
# Line 406: probs[:, 1] is probability of class 1 (duplicate)
# Labels: 0 = non-duplicate, 1 = duplicate (from Quora dataset)
```
**Training labels match inference convention. ✓**

## Result

**No label inversion exists.** The mapping from raw class index to displayed
label is correct and consistent across all model types and backends.
