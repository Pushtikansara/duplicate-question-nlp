# Final Conclusion — Complete

## Answer to Every Question

---

### Question 1: Does Cross-Encoder-Quora (Trained) actually contain runnable inference artifacts?

**YES**, it contains runnable inference artifacts:
- `models/cross-encoder-quora/config.json` (925 B) — `DebertaV2ForSequenceClassification` architecture
- `models/cross-encoder-quora/model.safetensors` (704 MB) — trained weights
- `models/cross-encoder-quora/tokenizer.json` (8.0 MB) — DebertaV2 tokenizer
- `models/cross-encoder-quora/tokenizer_config.json` (538 B) — tokenizer configuration

**However**, the `config.json` specifies `transformers_version: "5.13.0"` which is NOT a valid public HuggingFace transformers release. The loading path is via `sentence-transformers.CrossEncoder(local_path)` which internally calls `AutoModelForSequenceClassification.from_pretrained()`. Whether this succeeds depends on:
- Whether transformers 4.x tolerates the version mismatch (likely yes, with a warning)
- Whether the DebertaV2 architecture loads correctly (likely yes)
- Whether the 704 MB safetensors file is intact (unknown without checksum verification)

**Conclusion: CAN run today — likely YES, but with version mismatch warnings. Output quality is unverified.**

---

### Question 2: How was Cross-Encoder-Quora (Trained) trained?

**UNKNOWN — no training script or training metadata found.**

Evidence:
- No training script exists in `scripts/`, `_training/`, or `notebooks/`
- No `training_args.bin` file in the model directory
- No `trainer_state.json` in the model directory
- The config.json only has architecture metadata, no training configuration
- The model directory contains ONLY inference artifacts (config, weights, tokenizer)

It is likely NOT a SentenceTransformers CrossEncoder (no `sentence_bert_config.json`, no `modules.json`, no `config_sentence_transformers.json`). The `CrossEncoder` wrapper from sentence-transformers is used to load it, but the underlying model is a vanilla `DebertaV2ForSequenceClassification`.

The most likely training method is:
- HuggingFace `Trainer` with `DebertaV2ForSequenceClassification`
- Trained on Quora duplicate question dataset
- Or a custom training loop with AutoModelForSequenceClassification

---

### Question 3: Exactly how should Cross-Encoder-Quora (Trained) be loaded?

**Current loading path (used by the project):**
```python
from sentence_transformers import CrossEncoder
model = CrossEncoder("models/cross-encoder-quora", device="cpu")
scores = model.predict([(q1, q2)], apply_softmax=True)
prob_dup = scores[0][1]  # binary: [non_dup_prob, dup_prob]
```

**Alternative direct loading path (more correct):**
```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
model = AutoModelForSequenceClassification.from_pretrained("models/cross-encoder-quora")
tokenizer = AutoTokenizer.from_pretrained("models/cross-encoder-quora")
# Then tokenize + forward + softmax manually
```

Both paths should work. The `CrossEncoder` wrapper is simpler for inference but adds an unnecessary abstraction layer since this is NOT a SentenceTransformer model.

---

### Question 4: Does DeBERTa-v3 Cross-Encoder contain runnable weights?

**NO — not on local disk.**

The model `cross-encoder/nli-deberta-v3-base` has never been downloaded to this project. There is no directory at `models/deberta_v3_cross_encoder/`. The only way to obtain weights is to download from HuggingFace Hub at runtime:
```python
CrossEncoder("cross-encoder/nli-deberta-v3-base", device="cpu")
```

If HuggingFace Hub is accessible, the weights will be downloaded and cached. The format is HuggingFace Transformers (PyTorch safetensors).

**Conclusion: Can run today — YES, but ONLY with HF Hub download. Not present on disk.**

---

### Question 5: Can DeBERTa-v3 Cross-Encoder run inside the current inference engine?

**YES — IF HF Hub is accessible.**

The inference path is:
1. `_models/embeddings.py:get_sentence_transformer_model("DeBERTa-v3 Cross-Encoder")`
2. → `CrossEncoder("cross-encoder/nli-deberta-v3-base", device=device)`
3. → `model.predict([(q1, q2)], apply_softmax=True)`
4. → `prob_dup = scores[2] / (scores[0] + scores[2])` (entail / (contra + entail))
5. → Decisions from `DecisionFusion.fuse()` combine with semantic assessment

**Limitation:** The current inference engine uses generic sigmoid calibration for DeBERTa (it's NOT listed in `configs/inference.yaml:sigmoid_params`). It only falls back to default `[15.0, 0.50]`.

**NO — cannot run inside `ARES._engine.py`** because ARES only supports Week 2 and Week 3/4 models. The ARES framework does not have a Phase 2 sentence-transformer inference path.

---

### Question 6: What exactly is E5-quora-finetuned?

E5-quora-finetuned is a **SentenceTransformer bi-encoder** (not a classifier, not a retriever standalone).

**Architecture:**
- Base model: `intfloat/e5-base-v2` (BERT-based)
- Training: `MultipleNegativesRankingLoss` on Quora dataset (73,920 samples, 5 epochs, batch_size=64, fp16)
- Output: 768-dim normalized embeddings with cosine similarity

**Module pipeline (from `modules.json`):**
1. Transformer (BertModel) → token embeddings
2. Pooling (mean pooling) → sentence embedding (768-dim)
3. Normalize → L2-normalized embedding

**Inference pipeline (from the code):**
```
emb1 = model.encode(q1, normalize_embeddings=True)  # 768-dim normalized vector
emb2 = model.encode(q2, normalize_embeddings=True)   # 768-dim normalized vector
similarity = np.dot(emb1, emb2)                        # cosine similarity [-1, 1]
prob = 1 / (1 + exp(-10.0 * (similarity - 0.73)))     # sigmoid calibration → [0, 1]
final = "duplicate" if prob >= 0.40 else "non-duplicate"  # threshold
```

**Best eval cosine_ap:** 0.7501 (epoch 3)

**Status:** It is a fine-tuned embedding model that requires cosine similarity + sigmoid calibration + threshold to produce a classification decision. It does NOT have a classification head built in.

---

### Question 7: Does E5-quora-finetuned already include similarity logic, decision threshold, classification pipeline, or only embeddings?

**Only embeddings are included in the model itself.**

The model file (`model.safetensors`, 418 MB) contains ONLY the transformer weights for generating embeddings. Everything else is external:

| Component | Location | Included in model? |
|-----------|----------|-------------------|
| Embedding generation | `model.safetensors` | ✅ YES (the model itself) |
| Normalization | `2_Normalize` module | ✅ YES (in modules.json pipeline) |
| Cosine similarity | `_models/embeddings.py` (code) | ❌ NO (applied at inference time) |
| Sigmoid calibration | `configs/inference.yaml` → params [10.0, 0.73] | ❌ NO (external config) |
| Decision threshold | `configs/inference.yaml` → 0.40 | ❌ NO (external config) |
| Classification head (LR) | `models/e5_base_v2_lr_head.pkl` | ❌ NOT used (cosine sim is used instead) |

---

### Question 8: Which models are currently supported by `load_model_and_tokenizer()`?

**`load_model_and_tokenizer()` in `_inference/transformer.py` supports exactly 2 models:**

| # | Display Name | Internal ID | Support |
|---|-------------|-------------|---------|
| 1 | `"Improved DistilBERT (Week 4)"` | `week4` | ✅ PRIMARY — tried first |
| 2 | `"DistilBERT (Week 3)"` | `week3` | ✅ FALLBACK — tried if Week 4 fails |

**The `model_version` parameter is effectively IGNORED.** The function delegates to `resolve_model_selection()` which:
1. Checks Week 4 directory → if exists, returns Week 4
2. Checks Week 3 directory → if exists, returns Week 3
3. Neither: raises `ModelArtifactsNotFoundError`

Passing any other model name (e.g., "E5-base-v2", "Cross-Encoder-Quora", "BGE-base-en-v1.5") results in loading Week 4 instead.

---

### Question 9: Why does the ARES demo always fall back to Week 4 Improved DistilBERT?

**Complete call stack showing the double dispatch:**

```
app/pages/ares_demo.py:render()
  st.session_state["selected_model"] = "E5-quora-finetuned"  # user's selection
  engine.run_demo(model_name="E5-quora-finetuned")
    ares/demo_engine.py:run_demo()
      ARES()
      # Phase 10.5.2 fix: engine.with_model(model_name)  ← sets self._model_name
      engine._lazy_load()

        === DISPATCH POINT 1: ARES._lazy_load() ===
        self._model_name = "E5-quora-finetuned"  (set by with_model)

        is_week2_model("E5-quora-finetuned")? → FALSE
          (check: "E5-quora-finetuned" not in ["TF-IDF + Logistic Regression (Week 2)",
                                                 "TF-IDF + Linear SVM (Week 2)"])

        → Falls through to ELSE branch:
        load_model_and_tokenizer(PATHS, model_version="E5-quora-finetuned")

          === DISPATCH POINT 2: resolve_model_selection() ===
          def resolve_model_selection(PATHS):
              # IGNORES model_version parameter entirely!
              week4_status = inspect_model_dir(PATHS.week4_model_dir)
              if week4_status.ready:
                  return Resolution(selected="week4", ...)
              week3_status = inspect_model_dir(PATHS.week3_model_dir)
              if week3_status.ready:
                  return Resolution(selected="week3", ...)
              raise ModelArtifactsNotFoundError(...)

          inspect_model_dir("models/week4_improved_model/")
            → config.json: EXISTS ✅
            → weight file: model.safetensors EXISTS ✅
            → has_tokenizer: TRUE ✅
            → ready: TRUE ✅

          return Resolution(selected="week4", selected_label="Improved DistilBERT (Week 4)")

        _load_hugging_face_artifacts("models/week4_improved_model/")
          AutoModelForSequenceClassification.from_pretrained("models/week4_improved_model")
          AutoTokenizer.from_pretrained("models/week4_improved_model")
          → Returns (model, tokenizer, metadata with model_label="Improved DistilBERT (Week 4)")

        DuplicateQuestionInferenceService(model=WEEK4_DISTILBERT, tokenizer=..., metadata=...)

      engine.predict(q1, q2)
        bundle.service.predict_single(q1, q2)
          → Uses Week 4 Improved DistilBERT regardless of what user selected
```

**Two specific code locations are responsible:**

1. `src/duplicate_question_app/_config/settings.py` — `resolve_model_selection()` does not accept or use a `model_version` parameter:
   ```python
   def resolve_model_selection(paths):
       # Always checks week4 first, then week3
       # model_version parameter from caller is silently dropped
   ```

2. `src/duplicate_question_app/_inference/transformer.py` — `load_model_and_tokenizer()` calls `resolve_model_selection()` without passing the `model_version`:
   ```python
   def load_model_and_tokenizer(paths, model_version=None):
       resolution = resolve_model_selection(paths)  # ← model_version NOT passed!
   ```

**Root Cause:** The `model_version` parameter is accepted by `load_model_and_tokenizer()` but NEVER forwarded to `resolve_model_selection()`, which always uses its own hardcoded Week-4-first logic.

---

### Question 10: Is there duplicate inference logic anywhere?

**YES — 5 separate inference implementations exist:**

| # | Implementation | File | Models Served | Calibration |
|---|---------------|------|---------------|-------------|
| 1 | **`DuplicateQuestionInferenceService.predict_single()`** | `_inference/transformer.py` | DistilBERT W3/W4 | Softmax (direct) |
| 2 | **`Week2InferenceService.predict_single()`** | `_models/week2.py` | TF-IDF LR/SVM | LR: predict_proba; SVM: sigmoid(decision_function) |
| 3 | **`predict_with_sentence_transformer()`** | `_models/embeddings.py` | BGE, E5, E5-ft, MPNet | Config-driven sigmoid params |
| 4 | **`CrossEncoder` path** (inside `predict_with_sentence_transformer()`) | `_models/embeddings.py` | DeBERTa CE, CE-Quora | NLI conversion or direct softmax |
| 5 | **`InferenceOptimizer.predict_single_optimized()`** | `_inference/optimizer.py` | All sentence-transformer models | Hardcoded sigmoid params (different values!) |

**Additionally:**
- **`get_ensemble_prediction()`** in `_ensemble/v1.py` calls ALL 5 implementations above (delegates per sub-model)
- **`ARES.predict()`** in `ares/_engine.py` is a wrapper that only supports implementations #1 and #2

**The duplicate between #3 and #5 is the most concerning:**
- Both serve the same sentence-transformer models
- Both apply sigmoid calibration
- But they use DIFFERENT calibration parameters (steepness/midpoint differ significantly)
- Path #3 is used by the Prediction Page (production)
- Path #5 is used by InferenceOptimizer (standalone/optimization)
- Same model + same input → DIFFERENT probability outputs

---

## Per-Model Verdict

| Model | Can Run Today? | How |
|-------|---------------|-----|
| TF-IDF + Logistic Regression (Week 2) | **YES** | `Week2InferenceService.predict_single()` via `_models/week2.py` |
| TF-IDF + Linear SVM (Week 2) | **YES** | `Week2InferenceService.predict_single()` with SVM dispatch |
| DistilBERT (Week 3) | **YES** | `DuplicateQuestionInferenceService.predict_single()` via `_inference/transformer.py` |
| Improved DistilBERT (Week 4) | **YES** (DEFAULT) | Same as Week 3 — first priority in `resolve_model_selection()` |
| BGE-base-en-v1.5 | **YES** (needs HF Hub) | `SentenceTransformer("BAAI/bge-base-en-v1.5")` via `_models/embeddings.py` |
| E5-base-v2 | **YES** (needs HF Hub) | `SentenceTransformer("intfloat/e5-base-v2")` via `_models/embeddings.py` |
| E5-quora-finetuned | **YES** | `SentenceTransformer("models/e5-quora-finetuned")` — complete on disk |
| MPNet-base-v2 | **YES** (needs HF Hub) | `SentenceTransformer("sentence-transformers/all-mpnet-base-v2")` via `_models/embeddings.py` |
| DeBERTa-v3 Cross-Encoder | **YES** (needs HF Hub) | `CrossEncoder("cross-encoder/nli-deberta-v3-base")` via `_models/embeddings.py` |
| Cross-Encoder-Quora (Trained) | **LIKELY YES** | `CrossEncoder("models/cross-encoder-quora")` — complete artifacts, version mismatch warning |
| Semantic Ensemble | **YES** (depends) | `_ensemble/v1.py:get_adaptive_ensemble_prediction()` — works if any sub-model works |

**Models that work WITHOUT any external download or change:**
1. TF-IDF + Logistic Regression (Week 2)
2. TF-IDF + Linear SVM (Week 2)
3. DistilBERT (Week 3)
4. Improved DistilBERT (Week 4) — **DEFAULT**
5. E5-quora-finetuned
6. Cross-Encoder-Quora (Trained) — likely, with version warning

**Models that require HuggingFace Hub download (first use only):**
7. BGE-base-en-v1.5
8. E5-base-v2
9. MPNet-base-v2
10. DeBERTa-v3 Cross-Encoder

**Models that work only inside the Prediction Page (NOT in ARES demo):**
- All models #5–11 are NOT supported by the ARES framework
- ARES only supports models #1–4

**Models whose LR/MLP heads are ignored in production:**
- E5-base-v2 (LR head exists at `e5_base_v2_lr_head.pkl` but not used)
- BGE-base-en-v1.5 (LR head exists at `bge_lr_head.pkl` but not used)
- MPNet-base-v2 (LR head exists at `all_mpnet_base_v2_lr_head.pkl` but not used)
- E5-base-v2 (MLP head exists at `e5_mlp_head.pt` but not used)
