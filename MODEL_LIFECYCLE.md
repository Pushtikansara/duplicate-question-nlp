# Model Lifecycle

*Updated: 2026-07-27*

This document defines the lifecycle stage of every registered model in the system.

---

## Tiers

| Tier | Criteria | Access in UI |
|------|----------|-------------|
| **Production** | F1 > 0.87, working, validated, fast inference | Shown first in selector |
| **Research** | F1 > 0.70, working, useful for benchmarks | Shown below production |
| **Experimental** | Working but flawed (wrong task, too slow, needs retraining) | Shown below research |
| **Legacy** | Broken or superseded models kept for reference | Shown last |

---

## Production (3 Models)

### Improved DistilBERT (Week 4) — ⭐ Default
- **F1**: 0.9539 | **Accuracy**: 0.9660 | **Latency**: 2.67ms
- **Parameters**: 66.9M | **Architecture**: DistilBERT
- **Backend**: Transformer | **Source**: Local
- **Status**: ✅ Ready
- **Best for**: General-purpose duplicate detection — the default production model

### DistilBERT (Week 3)
- **F1**: 0.8967 | **Accuracy**: 0.9202 | **Latency**: 2.58ms
- **Parameters**: 66.9M | **Architecture**: DistilBERT
- **Backend**: Transformer | **Source**: Local
- **Status**: ✅ Ready
- **Best for**: When Week 4 is too aggressive; conservative fallback

### Cross-Encoder-Quora (Trained)
- **F1**: 0.8758 | **Accuracy**: 0.9066 | **Latency**: 2.86ms
- **Parameters**: 184M | **Architecture**: Cross-Encoder
- **Backend**: Cross-Encoder | **Source**: Local
- **Threshold**: 0.52 (updated in Phase 11.2)
- **Status**: ✅ Ready
- **Best for**: Accuracy-critical predictions with joint encoding

---

## Research (3 Models)

### MPNet-base-v2
- **F1**: 0.7605 | **Accuracy**: 0.8014 | **Latency**: 2.43ms
- **Parameters**: 110M | **Source**: HuggingFace (auto-download)
- **Status**: ✅ Available (cached)
- **Note**: Best calibration among bi-encoders (ECE=0.013)
- **Limitation**: Auto-downloads from HuggingFace; no local copy

### E5-quora-finetuned
- **F1**: 0.7667 | **Accuracy**: 0.8098 | **Latency**: 2.38ms
- **Parameters**: 118M | **Source**: Local (fine-tuned)
- **Threshold**: 0.63 (updated in Phase 11.2)
- **Status**: ✅ Ready
- **Limitation**: Slightly over-confident (ECE=0.055 before calibration)

### BGE-base-en-v1.5
- **F1**: 0.7313 | **Accuracy**: 0.7610 | **Latency**: 2.31ms
- **Parameters**: 110M | **Source**: HuggingFace (auto-download)
- **Status**: ✅ Available (cached)
- **Note**: Fastest inference among bi-encoders
- **Limitation**: Over-predicts duplicates on similar topics; auto-download from HF

---

## Experimental (3 Models)

### E5-base-v2
- **F1**: 0.7068 | **Accuracy**: 0.7376 | **Latency**: 2.39ms
- **Parameters**: 118M | **Source**: HuggingFace (auto-download)
- **Threshold**: 0.59 (updated in Phase 11.2 — was 0.35 causing 92.7% positive rate)
- **Status**: ⚠️ Needs retraining
- **Issues**: Raw ECE before calibration was 0.163 (worst of all models); sigmoid midpoint (0.82) is far from optimal threshold (0.59)

### DeBERTa-v3 Cross-Encoder
- **F1**: 0.6287 | **Accuracy**: 0.6010 | **Latency**: 2.99ms
- **Parameters**: 184M | **Source**: HuggingFace (auto-download)
- **Status**: ⚠️ Wrong task
- **Issues**: NLI model used for duplicate detection; severe miscalibration (ECE=0.372)

### Semantic Ensemble
- **F1**: N/A | **Latency**: ~30s per pair
- **Source**: Built-in (uses all models)
- **Status**: ⚠️ Too slow
- **Issues**: ~30s inference time due to LRU cache thrashing (MAX_CACHED_MODELS=3)
- **Recommendation**: Requires increasing `MAX_CACHED_MODELS` or changing caching strategy

---

## Legacy (2 Models)

### TF-IDF + Logistic Regression (Week 2)
- **F1**: N/A (broken) | **Backend**: Classical ML
- **Status**: ❌ Broken — TF-IDF vectorizer dimension mismatch (5K vs 10K features)
- **Kept for**: Reference and comparison; would need retraining to fix

### TF-IDF + Linear SVM (Week 2)
- **F1**: N/A (broken) | **Backend**: Classical ML
- **Status**: ❌ Broken — same dimension mismatch
- **Kept for**: Reference and comparison
