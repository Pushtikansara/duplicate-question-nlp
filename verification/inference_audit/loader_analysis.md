# Loader Analysis — Complete

## Loader Inventory

### Loader 1: `load_model_and_tokenizer()` — `_inference/transformer.py`
**Purpose:** Loads HuggingFace transformer models (DistilBERT Week 3/4)
**Backend:** `AutoModelForSequenceClassification.from_pretrained()` + `AutoTokenizer.from_pretrained()`
**Device:** CPU (hardcoded `_resolve_device()` returns "cpu")
**Supported models:**
- `"Improved DistilBERT (Week 4)"` (internal_id: `week4`)
- `"DistilBERT (Week 3)"` (internal_id: `week3`)
**Fallback chain:** Try Week 4 first → If fails, try Week 3 → If both fail, raise `ModelArtifactsNotFoundError`
**Threshold:** Week 4 loads best F1 threshold from `threshold_analysis.csv`; Week 3 uses default 0.5
**Tokenization:** `AutoTokenizer` with `padding=True, truncation=True, max_length=128, return_tensors="pt"`
**Normalization:** `normalize_question(text, expand_abbrevs=False)` — no abbreviation expansion
**Error handling:**
- `ModelArtifactsNotFoundError` (recoverable) — model directory doesn't exist or has no weight files
- `ModelLoadError` (unrecoverable) — directory exists but artifacts are corrupted/incompatible

### Loader 2: `Week2InferenceService` — `_models/week2.py`
**Purpose:** Loads scikit-learn classical ML models
**Backend:** `joblib.load()` for TF-IDF vectorizer + LogisticRegression + LinearSVC
**Device:** CPU
**Supported models:**
- `"TF-IDF + Logistic Regression (Week 2)"`
- `"TF-IDF + Linear SVM (Week 2)"`
**Selection:** `Week2InferenceService.predict_single(q1, q2, model_name)` dispatches to LR or SVM
**Features:** `hstack([tfidf(q1), tfidf(q2)])` — concatenated TF-IDF vectors
**SVM probability:** `1/(1+exp(-decision_function(x)))` — sigmoid scaling (LinearSVC has no native predict_proba)
**Normalization:** `normalize_question(text, expand_abbrevs=False)` — no abbreviation expansion

### Loader 3: `get_sentence_transformer_model()` — `_models/embeddings.py`
**Purpose:** Loads Phase 2 sentence-transformer models (bi-encoders and cross-encoders)
**Backend:** `SentenceTransformer()` or `CrossEncoder()` from `sentence-transformers`
**Device:** Auto-detected (CUDA if available, else CPU)
**Supported models:**
- `"BGE-base-en-v1.5"` → `SentenceTransformer("BAAI/bge-base-en-v1.5", device=...)`
- `"E5-base-v2"` → `SentenceTransformer("intfloat/e5-base-v2", device=...)`
- `"E5-quora-finetuned"` → `SentenceTransformer(local_path, device=...)`
- `"MPNet-base-v2"` → `SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device=...)`
- `"DeBERTa-v3 Cross-Encoder"` → `CrossEncoder("cross-encoder/nli-deberta-v3-base", device=...)`
- `"Cross-Encoder-Quora (Trained)"` → `CrossEncoder(local_path, device=...)`
**Caching:** Global `_sentence_transformer_cache` dict in `embeddings.py`
**Hub name resolution:** Via `configs/models.yaml` → `hub_names` section
**Auto-upgrade:** `resolve_best_available_e5_model()` auto-upgrades E5 to fine-tuned variant if local
**Error handling:** `FileNotFoundError` if local paths missing; HF download errors for hub models
**Special handling:**
- E5 models add `"query: "` or `"passage: "` prefixes for asymmetric retrieval
- Cross-encoders for DeBERTa apply NLI 3-class → binary conversion
- Fine-tuned cross-encoder (Cross-Encoder-Quora) is loaded as raw DeBERTa via `CrossEncoder` wrapper

### Loader 4: `get_ensemble_prediction()` — `_models/embeddings.py` → `_ensemble/v1.py`
**Purpose:** Runs all available models and combines results with adaptive weighting
**Backend:** Loader 1 + Loader 2 + Loader 3 (all three above)
**Supported models:** All 10 sub-models (ensemble meta-model)
**Caching:** Results cached per pair

### Loader 5: `ARES._lazy_load()` — `ares/_engine.py`
**Purpose:** ARES framework model loader
**Backend:** Delegates to Loader 1 (transformer) or Loader 2 (Week 2) based on `is_week2_model()`
**Supported models:**
- Week 2 models via `Week2InferenceService`
- Week 3/4 models via `DuplicateQuestionInferenceService`
**Note:** ARES does NOT support Phase 2 models (BGE, E5, MPNet, DeBERTa, CE-Quora, E5-quora-finetuned). It only handles Week 2 (classical ML) and Week 3/4 (DistilBERT transformer).

### Loader 6: `InferenceOptimizer` — `_inference/optimizer.py`
**Purpose:** Optimized inference with caching and batching (separate code path)
**Backend:** `SentenceTransformer` or `CrossEncoder` from `sentence-transformers`
**Supported models:** Same as Loader 3 + calibration for E5/BGE/MPNet
**Calibration:** Model-specific sigmoid parameters (steepness/midpoint) — different values than Loader 3!
**Note:** This is a SEPARATE inference path from Loader 3. Calibration values differ (see Backend Analysis).

## Loader-to-Model Mapping

| Model | Loader | Backend | Can Load Today? |
|-------|--------|---------|-----------------|
| TF-IDF + Logistic Regression (Week 2) | Loader 2 | joblib | YES |
| TF-IDF + Linear SVM (Week 2) | Loader 2 | joblib | YES |
| DistilBERT (Week 3) | Loader 1 | HF Transformers | YES |
| Improved DistilBERT (Week 4) | Loader 1 | HF Transformers | YES |
| BGE-base-en-v1.5 | Loader 3 | SentenceTransformer | YES (needs HF download) |
| E5-base-v2 | Loader 3 | SentenceTransformer | YES (needs HF download) |
| E5-quora-finetuned | Loader 3 | SentenceTransformer | YES (local disk) |
| MPNet-base-v2 | Loader 3 | SentenceTransformer | YES (needs HF download) |
| DeBERTa-v3 Cross-Encoder | Loader 3 | CrossEncoder | YES (needs HF download) |
| Cross-Encoder-Quora (Trained) | Loader 3 | CrossEncoder (wrapper) | UNKNOWN (transformers_version issue) |
| Semantic Ensemble | Loader 4 | Custom ensemble | YES (depends on sub-models) |

## Missing Loaders

- **No ONNX runtime loader** — no ONNX models, no ONNX Runtime dependency
- **No TorchScript loader** — no TorchScript models
- **No vLLM / TGI / Triton loader** — no production inference server integration
- **No separate LR head loader** — LR heads are loaded manually in `_training/classifier_head.py` but NOT integrated into `get_model_prediction()` in `constants.py` — they are NEVER used during live inference on the prediction page

## Critical Finding: LR Heads Are Never Used In Production Inference

The LR heads (`e5_base_v2_lr_head.pkl`, `bge_lr_head.pkl`, `all_mpnet_base_v2_lr_head.pkl`) and the MLP head (`e5_mlp_head.pt`) exist on disk and have trained weights, but they are NOT integrated into the live inference pipeline:

1. `get_model_prediction()` in `app/utils/constants.py` calls `predict_with_sentence_transformer()` for Phase 2 models
2. `predict_with_sentence_transformer()` uses cosine similarity + sigmoid calibration — NOT the LR heads
3. The LR heads are only used in `_training/classifier_head.py` and potentially in notebooks

The LR heads represent a more expressive learned bilinear similarity (`[emb1, emb2, |emb1-emb2|, emb1*emb2]` → LogisticRegression) that would likely outperform cosine similarity, but the production inference path doesn't use them.
