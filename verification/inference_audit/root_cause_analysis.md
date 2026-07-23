# Root Cause Analysis — Complete

## Why Week 4 (Improved DistilBERT) Works

**Evidence:**
1. `models/week4_improved_model/` contains: `config.json` (664 B), `model.safetensors` (256 MB), `tokenizer.json` (695 KB), `tokenizer_config.json` (541 B)
2. `_inference/transformer.py:load_model_and_tokenizer()` → `resolve_model_selection()` → checks `week4_improved_model/` → returns `ModelDirectoryStatus(ready=True)`
3. `_load_hugging_face_artifacts()` calls `AutoModelForSequenceClassification.from_pretrained(week4_dir)` and `AutoTokenizer.from_pretrained(week4_dir)` — these succeed because all required files exist
4. `DuplicateQuestionInferenceService.predict_single()` normalizes, tokenizes (max_length=128), runs model with `torch.no_grad()`, applies softmax
5. Optional threshold from `threshold_analysis.csv` for optimal F1

**Root Cause of Success:**
- Complete artifact set (config.json + model.safetensors + tokenizer.json + tokenizer_config.json)
- Standard `DistilBertForSequenceClassification` architecture well-supported by transformers 4.x
- Dedicated, tested loader (`load_model_and_tokenizer()`)
- Handles the `transformers_version: "5.13.0"` warning gracefully

## Why Cross-Encoder-Quora (Trained) May Fail

**Evidence:**
1. `models/cross-encoder-quora/` contains: `config.json` (925 B), `model.safetensors` (704 MB), `tokenizer.json` (8.0 MB), `tokenizer_config.json` (538 B)
2. `config.json` has `"architectures": ["DebertaV2ForSequenceClassification"]` and `"transformers_version": "5.13.0"`
3. Loaded via `_models/embeddings.py:get_sentence_transformer_model()` → `CrossEncoder(local_path, device=device)`
4. `CrossEncoder.__init__()` internally calls `AutoModelForSequenceClassification.from_pretrained(local_path)`
5. The `DebertaV2ForSequenceClassification` architecture uses the `deberta-v2` model type which requires the `transformers` library to support DeBERTaV2 (available since transformers 4.x)

**Potential Failure Points:**
1. **transformers_version: "5.13.0"**: When `from_pretrained()` reads `config.json` and sees `transformers_version: "5.13.0"`, it may:
   - Issue a warning but proceed (most likely)
   - Refuse to load if version check is strict (unlikely but possible in some builds)
2. **DeBERTaV2 tokenizer**: The `DebertaV2Tokenizer` uses SentencePiece (`vocab_type: "spm"`). If `tokenizer.json` (8.0 MB) is corrupted or the SentencePiece model is missing from the JSON, loading will fail.
3. **Model size**: 704 MB is large for a DeBERTaV2-base model (typical is ~500 MB for deberta-v3-base). This may indicate additional weights or different architecture config.
4. **CrossEncoder wrapper compatibility**: `sentence-transformers.CrossEncoder` loads models by initializing `AutoModelForSequenceClassification` internally. For a `DebertaV2ForSequenceClassification`, this should work IF the transformers library handles this architecture correctly with the loaded config.

**Actual Loading Test (inferred):**
- With current transformers 4.x and sentence-transformers, the CrossEncoder wrapper should successfully load this model
- The `transformers_version: "5.13.0"` warning is non-fatal
- Predicted label/score may be shifted from expected (the 0.10 threshold in config suggests unusual output distribution)

**Root Cause of Uncertainty:**
No definitive evidence without actually running the loader. The artifacts are complete but the transformers_version mismatch introduces uncertainty about output quality.

## Why E5-base-v2 Fails (If It Does)

**Evidence:**
1. No local model directory at `models/e5_base_v2/` — all paths.yaml configs point to non-existent directories
2. `build_registry()` checks `huggingface_hub.scan_cache_dir()` for `intfloat/e5-base-v2` — cache depends on prior download
3. `get_sentence_transformer_model()` → `SentenceTransformer("intfloat/e5-base-v2", device=device)` downloads from HF hub on first call
4. LR head at `models/e5_base_v2_lr_head.pkl` exists (13 KB) but is NOT used by `predict_with_sentence_transformer()`

**Failure Point (if any):**
- **No internet access**: The model requires HF hub download. Without internet, `SentenceTransformer("intfloat/e5-base-v2")` raises `OSError: Can't load the model` because neither local directory nor HF cache exists.
- **Cache directory name mismatch**: Paths specifies `models/e5_base_v2/` but HF hub caches to `~/.cache/huggingface/hub/models--intfloat--e5-base-v2/`. The `_get_hf_cache_path()` function in `registry.py` handles this mapping, but the actual loading via `SentenceTransformer()` uses HF hub's own resolution.

**Root Cause:**
The model requires HuggingFace hub download. If internet is unavailable, inference fails. This is expected behavior for HF hub models, but the local directory paths in `paths.yaml` are misleading — they suggest local storage that doesn't exist.

## Why DeBERTa-v3 Cross-Encoder Fails (If It Does)

Same root cause as E5-base-v2:
1. No local directory at `models/deberta_v3_cross_encoder/`
2. Requires HF hub download of `cross-encoder/nli-deberta-v3-base`
3. Without internet, `CrossEncoder("cross-encoder/nli-deberta-v3-base")` fails with download error

**Additionally:**
- The DeBERTa NLI cross-encoder has a non-standard output format: 3 scores [contradiction, neutral, entailment]
- `predict_with_sentence_transformer()` has special handling: `prob_dup = entail / (contra + entail)`
- If sigmoid_params are not found for DeBERTa (they're NOT in config), it uses a generic calibration with `steepness=15.0, midpoint=0.50`
- The config actually doesn't list DeBERTa in `sigmoid_params` at all, so the default calibration is used

**Root Cause:**
Missing from `configs/inference.yaml:sigmoid_params` — DeBERTa uses generic default calibration (15.0, 0.50) instead of model-specific values.

## Why ARES Always Falls Back to Week 4

**Evidence from code (`src/ares/_engine.py:43-51`):**
```python
def _lazy_load(self) -> None:
    if self._loaded:
        return
    ...
    self._model_name = self._model_name or get_config("app").get("default_model", DEFAULT_MODEL)
    ...
    if is_week2_model(self._model_name):
        ... Week2InferenceService ...
    else:
        ... load_model_and_tokenizer(self._paths, model_version=self._model_name) ...
```

**And in `_inference/transformer.py`:**
```python
def load_model_and_tokenizer(paths, model_version=None):
    resolution = resolve_model_selection(paths)
    # resolve_model_selection() IGNORES model_version parameter!
    # It always checks: week4 dir first, then week3 dir as fallback
```

**Call stack:**
```
ARES.with_model("E5-quora-finetuned")      # sets self._model_name
ARES.predict(q1, q2)                        # calls _lazy_load()
  _lazy_load()
    is_week2_model("E5-quora-finetuned")    → False
    load_model_and_tokenizer(PATHS, model_version="E5-quora-finetuned")
      resolve_model_selection(PATHS)        → IGNORES model_version
        inspect_model_dir(week4_dir)        → week4_improved_model/ EXISTS
        return Resolution(selected="week4")
      _load_hugging_face_artifacts(week4_dir) → loads Week 4 DistilBERT
    DuplicateQuestionInferenceService(model=Week4DistilBERT, ...)
    ARES._bundle.service = Week4DistilBERT
    ARES.predict(q1, q2) → uses Week 4 always
```

**Root Cause Double Dispatch Problem:**

The ARES engine has TWO separate dispatch points that conflict:

1. **Model name resolution** in `ARES._lazy_load()`:
   - Checks `is_week2_model(self._model_name)` — if True, uses Week2InferenceService
   - Otherwise, delegates to `load_model_and_tokenizer()` which ignores the model name

2. **Model selection** in `_config/settings.py:resolve_model_selection()`:
   - Always checks Week 4 directory first
   - Falls back to Week 3 if Week 4 is missing
   - Does NOT accept a `model_version` parameter (it exists in the call signature of `load_model_and_tokenizer` but is never passed to `resolve_model_selection`)

**Result:** Any non-Week-2 model name passed to ARES results in loading Week 4 DistilBERT. Phase 2 models (BGE, E5, MPNet, DeBERTa, Cross-Encoder-Quora, E5-quora-finetuned) are ALL handled this way.

## Summary of Root Causes

| Issue | Root Cause | Severity |
|-------|-----------|----------|
| ARES always loads Week 4 | `resolve_model_selection()` ignores `model_version` parameter | HIGH |
| Phase 2 models unsupported by ARES | `ARES._lazy_load()` only handles Week 2 or Transformer; no Phase 2 path | HIGH |
| CE-Quora loading uncertain | `transformers_version: "5.13.0"` in config.json — not a valid public release | MEDIUM |
| E5/BGE/MPNet require internet | No local model directories; HF hub download required | MEDIUM |
| LR heads unused in production | `predict_with_sentence_transformer()` uses cosine similarity instead of trained LR heads | MEDIUM |
| Dual inference paths for ST | `embeddings.py` and `optimizer.py` use different sigmoid calibration params | MEDIUM |
| DeBERTa missing calibration | No sigmoid_params in config for DeBERTa; uses generic default | LOW |
| Cross-Encoder-Quora threshold 0.10 | Unusually low threshold suggests shifted output distribution | LOW |
