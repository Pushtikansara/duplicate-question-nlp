# Phase 10.6.5 — Prediction Audit Report

## Execution Path Traced

```
User Input
  ↓
UI (Streamlit: app/pages/prediction.py)
  ↓
get_model_prediction() (app/utils/constants.py:87)
  ↓
Model Routing (is_week2 / is_ensemble / is_new_embedding / transformer)
  ↓
Prediction Path (per model type):
  ├── Week 2: Week2InferenceService.predict_single() (src/.../_models/week2.py:136)
  ├── DistilBERT: DuplicateQuestionInferenceService.predict_single() (src/.../_inference/transformer.py:242)
  ├── Embedding/Cross-Encoder: predict_with_sentence_transformer() (src/.../_models/embeddings.py:205)
  └── Ensemble: get_ensemble_prediction() (src/.../_models/embeddings.py:354)
  ↓
Text Normalization (src/.../_preprocessing/text.py:861)
  ↓
Model Forward Pass → Raw Logits → Softmax → Predicted Class → Label Mapping
  ↓
Semantic Assessment (SemanticPipelineService.assess)
  ↓
Decision Fusion (DecisionFusion.fuse)
  ↓
Final Result
```

## Critical Bugs Found & Fixed

### Bug 1: Missing identical-text shortcut for embedding/cross-encoder models
- **File**: `src/duplicate_question_app/_models/embeddings.py`
- **Impact**: Identical questions (e.g., "what is ai" vs "what is ai") relied on model inference
  instead of the guaranteed-Duplicate shortcut that the DistilBERT path already had.
- **Fix**: Added `if q1_norm == q2_norm: return Duplicate with 100% confidence` at line 217
  and batched identical-pair handling in `predict_batch_sentence_transformer`.

### Bug 2: Silent model fallback in `get_inference_service()`
- **File**: `app/services/runtime.py`
- **Impact**: If a user selected "Cross-Encoder-Quora (Trained)" and it failed to load,
  the system silently fell back to the default DistilBERT model, making the user
  believe they were using their selected model when they were not.
- **Fix**: Removed the nested try/except fallback. Now raises a clear error
  with the specific model name and failure reason.

### Bug 3: Fusion override of base prediction without notification
- **File**: `app/utils/constants.py`
- **Impact**: The DecisionFusion could silently change "Duplicate" to "Non-Duplicate"
  (or vice versa) without the user knowing. This was the root cause of the
  "what is ai" vs "what is ai" showing Non-Duplicate when conflict penalties
  from semantic assessment reduced the fused score below threshold.
- **Fix**: Added `prediction_overridden`, `base_prediction`, `override_reason`,
  and `override_confidence_delta` fields to result. Displayed as a warning
  in the prediction page UI.

### Bug 4: Missing abbreviation "BDA" → "Big Data Analytics"
- **File**: `src/duplicate_question_app/_preprocessing/text.py`
- **Impact**: Case "what is bda" would not expand, preventing match with
  "what is big data analytics".
- **Fix**: Added `BDA: Big Data Analytics` to abbreviations dictionary.

## Label Mapping Verification

All model paths use the same label convention:
- `predicted_label = 0` → display `"Non-Duplicate"`
- `predicted_label = 1` → display `"Duplicate"`

This is consistent with Quora dataset labels where `is_duplicate=0` means
non-duplicate and `is_duplicate=1` means duplicate.

Cross-referenced against:
- Training: `src/.../tools/train_cross_encoder.py` (line 267: `num_labels=2`,
  line 406: `probs[:, 1]` is duplicate class)
- Inference: `src/.../_models/embeddings.py` (line 233: `scores[1]` = duplicate prob)
- Inference: `src/.../_inference/transformer.py` (line 283-284: `probabilities[1]` = duplicate)

**Label mapping is CORRECT** — no inversion exists.
