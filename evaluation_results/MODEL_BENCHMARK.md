# Model Benchmark — Phase 11.1

**Date:** 2026-07-25
**Dataset:** Quora validation split (40,429 pairs, subsampled to 5,000 for evaluation)
**Duplicate rate:** 36.9%
**Methodology:** Each model evaluated on identical 5,000-pair subset with its configured threshold per `configs/inference.yaml`. No prediction logic changed. Evidence collection only.

---

## Results Summary

| Rank | Model | Backend | F1 | Accuracy | ROC-AUC | PR-AUC | MCC | ECE | Latency | Status |
|------|-------|---------|----|----------|---------|--------|-----|-----|---------|--------|
| 1 | **Improved DistilBERT (Week 4)** | transformer | **0.9539** | **0.9660** | **0.9915** | **0.9838** | **0.9274** | 0.0303 | 2.67ms | ✅ |
| 2 | DistilBERT (Week 3) | transformer | 0.8967 | 0.9202 | 0.9765 | 0.9533 | 0.8367 | 0.0563 | 2.58ms | ✅ |
| 3 | Cross-Encoder-Quora (Trained) | cross-encoder | 0.8536 | 0.8818 | 0.9639 | 0.9293 | 0.7681 | 0.0577 | 2.86ms | ✅ |
| 4 | MPNet-base-v2 | bi-encoder | 0.7593 | 0.7988 | 0.8950 | 0.7852 | 0.6081 | **0.0132** | 2.43ms | ✅ |
| 5 | E5-quora-finetuned | bi-encoder | 0.7323 | 0.7438 | 0.8907 | 0.7726 | 0.5732 | 0.1317 | 2.38ms | ✅ |
| 6 | BGE-base-en-v1.5 | bi-encoder | 0.7290 | 0.7612 | 0.8733 | 0.7588 | 0.5556 | 0.0227 | 2.31ms | ✅ |
| 7 | DeBERTa-v3 Cross-Encoder | cross-encoder | 0.6287 | 0.6010 | 0.6506 | 0.4640 | 0.3684 | 0.3722 | 2.99ms | ❌ |
| 8 | E5-base-v2 | bi-encoder | 0.5611 | 0.4346 | 0.8439 | 0.7028 | 0.2114 | 0.2242 | 2.39ms | ⚠️ |
| — | TF-IDF + Logistic Regression | classical-ml | **ERROR** | **ERROR** | — | — | — | — | — | ❌ |
| — | TF-IDF + Linear SVM | classical-ml | **ERROR** | **ERROR** | — | — | — | — | — | ❌ |
| — | Semantic Ensemble | ensemble | **TIMEOUT** | **TIMEOUT** | — | — | — | — | ~30s | ⚠️ |

---

## Analysis by Backend

### Transformers (DistilBERT) — 🏆 Top Performers

**Improved DistilBERT (Week 4)** is the clear winner by all metrics:
- F1=0.9539, Accuracy=0.9660, ROC-AUC=0.9915
- FP=121 (2.4%), FN=49 (1.0%)
- Excellent calibration (ECE=0.0303)
- Fast inference (2.67ms/pair on CPU)
- Loads quickly (0.09s after first load)

**DistilBERT (Week 3)** is strong but significantly behind:
- F1=0.8967, Accuracy=0.9202
- 2.7× more false positives than Week 4 (324 vs 121)
- Good calibration (ECE=0.0563)

**Gap between Week 3 and Week 4 confirms the Week 4 improvements work:**
- Threshold tuning? Not captured in config (both use 0.50)
- Class weighting during training
- Error analysis-informed improvements

### Cross-Encoders — Mixed Results

**Cross-Encoder-Quora (Trained)** performs well (F1=0.8536) despite the suspiciously low threshold (0.10). The model produces very low probabilities for non-duplicates, so the 0.10 threshold is less problematic than expected. Still third-best overall.

**DeBERTa-v3 NLI Cross-Encoder** performs poorly (F1=0.6287). Using entailment ratio for duplicate detection is not effective:
- ECE=0.3722 — severely miscalibrated (most extreme among all models)
- ROC-AUC=0.6506 — barely better than random
- The NLI→duplicate mapping produces high-confidence wrong predictions

### Bi-Encoders — Useful for Feature Extraction

**MPNet-base-v2** is the best bi-encoder:
- F1=0.7593, Accuracy=0.7988
- **Best calibration of any model** (ECE=0.0132)
- Good ROC-AUC (0.8950)
- Most reliable probability estimates

**E5-base-v2 is broken at current threshold:**
- F1=0.5611, Accuracy=0.4346 (below random!)
- Threshold of 0.35 is far below the sigmoid midpoint (0.82)
- Result: 56.5% false positive rate
- The model predicts 92.7% of pairs as duplicate

**E5-quora-finetuned** improves over base E5:
- F1=0.7323 (vs 0.5611) — significant improvement from fine-tuning
- But still high FP rate (24.5%) from threshold at 0.40
- Recall is excellent (0.9696)

**BGE-base-en-v1.5** — balanced performance:
- F1=0.7290, good calibration (ECE=0.0227)
- Second-best calibrated model
- Reasonable trade-off

### Classical ML — Broken

Both Week 2 models (Logistic Regression, Linear SVM) are **non-functional**.
The TF-IDF vectorizer produces 5,000 features but the models expect 10,000.
This is a training/inference artifact mismatch that prevents any prediction.

### Ensemble — Too Slow for Batch Evaluation

The Semantic Ensemble could not be evaluated at scale. Each prediction:
- Loads all 8 sub-models (caching only 3, causing LRU thrashing)
- Takes ~30s per pair on CPU
- Only usable in single-pair production (not batch)

Partial results on n=19: 18/19 correct (1 false positive).

---

## Calibration Analysis

Best to worst ECE (lower is better):

| Model | ECE | Interpretation |
|-------|-----|----------------|
| MPNet-base-v2 | **0.0132** | Near-perfect calibration |
| BGE-base-en-v1.5 | **0.0227** | Very good |
| Improved DistilBERT (Week 4) | **0.0303** | Good |
| DistilBERT (Week 3) | **0.0563** | Moderate |
| Cross-Encoder-Quora (Trained) | **0.0577** | Moderate |
| E5-quora-finetuned | **0.1317** | Poor — too confident |
| E5-base-v2 | **0.2242** | Very poor |
| DeBERTa-v3 Cross-Encoder | **0.3722** | **Severe miscalibration** |

---

## Threshold Assessment

Most models have reasonable per-model thresholds EXCEPT:

- **E5-base-v2 (0.35):** The sigmoid midpoint is 0.82 with steepness=8.0. At threshold 0.35, the model classifies everything as duplicate. Optimal threshold would be ~0.8.
- **DeBERTa NLI (0.50):** Uses the default threshold, but this model's probability distribution is entirely different (entailment ratio). No per-model threshold is set.
- **Week 4 DistilBERT (0.50):** The notebook performed threshold tuning, but the tuned value was never captured in the config.
- **Cross-Encoder-Quora (0.10):** Works in practice but this value seems accidental rather than tuned. The training script found the optimal threshold via grid search, but the result was never saved.

---

## Recommendations

### Primary Production Model
**Keep: Improved DistilBERT (Week 4)**
- Best F1 (0.9539), best accuracy (0.9660)
- Low error rate (3.4% combined)
- Fast inference (2.7ms/pair)
- Locally cached, no external dependencies

### Secondary / Backup
**Keep: Cross-Encoder-Quora (Trained)**
- F1=0.8536, third-best overall
- Different architecture provides diversity
- Useful for ensemble or second opinion

### Best Bi-Encoder
**Keep: MPNet-base-v2** (Benchmark Only)
- Best bi-encoder calibration (ECE=0.0132)
- Best bi-encoder F1 (0.7593)
- Useful as feature extractor, not primary

### Remove
- **TF-IDF + Logistic Regression (Week 2)** — broken
- **TF-IDF + Linear SVM (Week 2)** — broken

### Retrain or Retune
- **E5-base-v2** — needs appropriate threshold or sigmoid recalibration

### Research Only
- **DeBERTa-v3 Cross-Encoder (NLI)** — wrong task for this model
- **Semantic Ensemble** — impractical in current form (cache thrashing)

---

## Visualizations

### ROC Curves
See `ROC_CURVES/` directory.
To generate: run `tools/plot_roc_curves.py` (not yet created).

### PR Curves
See `PR_CURVES/` directory.
To generate: run `tools/plot_pr_curves.py` (not yet created).

### Confusion Matrices
See `CONFUSION_MATRICES/confusion_matrices.txt` for all 11 models.
