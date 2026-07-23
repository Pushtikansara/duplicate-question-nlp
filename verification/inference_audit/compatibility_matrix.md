# Compatibility Matrix — Complete

## Legend
| Column | Meaning |
|--------|---------|
| Current Loader | The loader used for this model today |
| Correct Loader | The loader that should be used based on model format |
| Can Run Today | Whether inference works right now without changes |
| Needs New Loader | A new loader must be written |
| Needs Retraining | Model must be retrained |
| Needs Conversion | Format must be converted (e.g., to ONNX) |
| Needs Threshold | Optimal decision threshold is missing |
| Needs Metadata | Model metadata is incomplete |

## Matrix

| Model | Architecture | Current Loader | Correct Loader | Can Run Today | Needs New Loader | Needs Retraining | Needs Conversion | Needs Threshold | Needs Metadata |
|-------|-------------|----------------|----------------|---------------|-----------------|------------------|-----------------|-----------------|----------------|
| TF-IDF + Logistic Regression (Week 2) | sklearn LR | `Week2InferenceService.joblib` | Same | **YES** | NO | NO | NO | NO (0.5) | NO |
| TF-IDF + Linear SVM (Week 2) | sklearn SVM | `Week2InferenceService.joblib` | Same | **YES** | NO | NO | NO | NO (0.5) | NO |
| DistilBERT (Week 3) | DistilBertForSeqClass | `DuplicateQuestionInferenceService` | Same | **YES** | NO | NO | NO | NO (default 0.5) | YES¹ |
| Improved DistilBERT (Week 4) | DistilBertForSeqClass | `DuplicateQuestionInferenceService` | Same | **YES** ✅ DEFAULT | NO | NO | NO | YES² (0.5 file on disk) | NO |
| BGE-base-en-v1.5 | bi-encoder (ST) | `SentenceTransformer` + cos_sim + sigmoid | Same | **YES** (needs HF hub) | NO | NO | NO | YES³ (0.30 in config) | NO |
| E5-base-v2 | bi-encoder (ST) | `SentenceTransformer` + cos_sim + sigmoid | Same | **YES** (needs HF hub) | NO | NO | NO | YES³ (0.35 in config) | NO |
| E5-quora-finetuned | bi-encoder (ST) | `SentenceTransformer` + cos_sim + sigmoid | Same | **YES** | NO | NO | NO | YES³ (0.40 in config) | NO |
| MPNet-base-v2 | bi-encoder (ST) | `SentenceTransformer` + cos_sim + sigmoid | Same | **YES** (needs HF hub) | NO | NO | NO | YES³ (0.36 in config) | NO |
| DeBERTa-v3 Cross-Encoder | CrossEncoder (NLI) | `CrossEncoder` + NLI conversion | `CrossEncoder` | **YES** (needs HF hub) | NO | NO | NO | NO (default 0.5) | NO |
| Cross-Encoder-Quora (Trained) | DebertaV2ForSeqClass | `CrossEncoder` wrapper via `SentenceTransformer` | `AutoModelForSequenceClassification`⁴ | **UNKNOWN** | NO | NO | NO | YES⁵ (0.10 in config) | YES⁶ |
| Semantic Ensemble | Custom ensemble | `_ensemble/v1.py` or `v2.py` | Same | **YES** (depends) | NO | NO | NO | N/A | N/A |

## Notes

**¹ DistilBERT (Week 3) metadata:** Missing `special_tokens_map.json`. Also uses `transformers_version: "5.13.0"` in config.json, which is not a valid public release.

**² Improved DistilBERT (Week 4) threshold:** The threshold file (`threshold_analysis.csv`) is expected to be loaded by `load_week4_threshold_analysis()` in `_resolve_threshold()`. If this file is missing or the function fails (it was not directly verified in this audit), the fallback is the default 0.5 threshold from config.

**³ Bi-encoder thresholds:** Per-model thresholds are defined in `configs/inference.yaml` and loaded by `_get_threshold()` in `_models/embeddings.py`. These are applied AFTER sigmoid calibration, not at the raw cosine similarity level. The threshold and sigmoid parameters together form the complete inference pipeline.

**⁴ Cross-Encoder-Quora correct loader:** Although the current code uses `CrossEncoder` from `sentence_transformers`, the model is actually a raw `DebertaV2ForSequenceClassification` without any SentenceTransformer metadata (no `modules.json`, no `config_sentence_transformers.json`). It may be more correct to load it via `AutoModelForSequenceClassification.from_pretrained()` directly. However, `CrossEncoder` internally uses `AutoModelForSequenceClassification`, so both approaches should work IF the model is compatible with the installed transformers version.

**⁵ Cross-Encoder-Quora threshold:** Config specifies 0.10, which is unusually low. This suggests the model's output distribution is significantly shifted (possibly due to the transformers_version mismatch or the training regime).

**⁶ Cross-Encoder-Quora metadata:** The `transformers_version: "5.13.0"` in `config.json` is the primary metadata concern. The `tokenizer.json` is 8.0 MB (DebertaV2Tokenizer with SentencePiece), which is larger than the standard BERT tokenizer and may have compatibility issues.

## Cross-Cutting Issues

### Issue A: transformers_version: "5.13.0"
All locally-saved models (Week 3, Week 4, E5-quora-finetuned, Cross-Encoder-Quora) have `transformers_version: "5.13.0"` in their config.json. The public HuggingFace transformers library has NEVER released a version 5.x. The latest release is ~4.49.x.

**Impact on loading:**
- `from_pretrained()` may issue warnings but typically still loads the model
- Some architecture assumptions may differ between 4.x and the custom 5.13.0
- This is the most likely cause of any loading failures

### Issue B: LR Heads Not Integrated in Production
The trained LR heads (`e5_base_v2_lr_head.pkl`, etc.) represent a more expressive classification approach (learned bilinear similarity) than the deployed cosine similarity + sigmoid calibration. These heads are NOT used during production inference — only cosine similarity is used.

### Issue C: Dual Inference Paths for SentenceTransformers
There are TWO separate implementations for sentence-transformer inference:
1. `_models/embeddings.py:predict_with_sentence_transformer()` — used by Prediction Page
2. `_inference/optimizer.py:InferenceOptimizer.predict_single_optimized()` — standalone optimized path

Both have DIFFERENT sigmoid calibration parameters:
- Path 1: From `configs/inference.yaml` → `sigmoid_params` section
- Path 2: Hardcoded in `_calibrate_prob()` (steepness=18/14/14/15, midpoint=0.72/0.60/0.58/0.50)

This means the same model can produce DIFFERENT probabilities depending on which inference path is used.

### Issue D: ARES Does Not Support Phase 2 Models
The `ARES._lazy_load()` in `ares/_engine.py` can only load:
- Week 2 models (via `is_week2_model()` → `Week2InferenceService`)
- Week 3/4 transformers (via `load_model_and_tokenizer()` → `DuplicateQuestionInferenceService`)

It CANNOT load BGE, E5, MPNet, DeBERTa, Cross-Encoder-Quora, E5-quora-finetuned, or the Semantic Ensemble. When called with any Phase 2 model name, `load_model_and_tokenizer()` falls through to `resolve_model_selection()` which ignores the model_name parameter and returns Week 4.
