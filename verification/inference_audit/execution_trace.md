# Execution Trace — Complete

## All Prediction Execution Paths

### Path 1: Prediction Page (Streamlit UI)
**Entry:** `app/pages/prediction.py:render()`
**Flow:**
```
1. st.session_state["selected_model"]  (from sidebar)
2. get_runtime_context()                (app/services/runtime.py)
   ├── is_week2_model(selected)?        (_models/week2.py)
   │   └── YES → Week2InferenceService  (returns service, metadata)
   ├── is_ensemble_model(selected)?     (_config/settings.py)
   │   └── YES → return (None, metadata)
   ├── is_new_embedding_model(selected)? (_config/settings.py)
   │   └── YES → return (None, metadata)  [NO SERVICE LOADED]
   └── ELSE → load_model_and_tokenizer() → DuplicateQuestionInferenceService
3. service, metadata, _ = result
4. get_model_prediction(service, selected_model, q1, q2)
   ├── is_week2_model? → service.predict_single(q1, q2, selected_model)
   ├── is_ensemble_model? → get_ensemble_prediction(q1, q2)
   │   └── _ensemble/v1.py: get_adaptive_ensemble_prediction()
   │       └── Runs ALL 10 sub-models (see Path 6)
   ├── is_new_embedding_model? → predict_with_sentence_transformer(selected_model, q1, q2)
   │   ├── get_sentence_transformer_model(selected_model)  (Loader 3)
   │   └── Cosine similarity + sigmoid calibration
   └── ELSE → service.predict_single(q1, q2) [Transformer path]
5. SemanticPipelineService.assess(q1, q2)  (if mode != "cross_encoder_only")
   ├── PerceptionPipeline (via linguistic analysis)
   ├── SemanticIntelligenceEngine.assess()
   │   ├── ConceptMatcher
   │   ├── EntityMatcher
   │   ├── RelationMatcher
   │   ├── IntentMatcher
   │   ├── ContextMatcher
   │   ├── ConflictDetector
   │   ├── ConfidenceFusion
   │   ├── EvidenceBuilder
   │   └── DecisionSupport
   └── Returns SemanticAssessment
6. DecisionFusion.fuse(ce_score, semantic_assessment)
   └── Weighted fusion + conflict penalty → final_score, final_prediction
```

**Key observation:** For Phase 2 embedding models (BGE, E5, MPNet, E5-quora-finetuned), `is_new_embedding_model()` returns True, which causes `get_inference_service()` in `runtime.py` to return `(None, metadata)` — NO inference service is loaded. Then `get_model_prediction()` in `constants.py` dispatches to `predict_with_sentence_transformer()` which handles its own model loading. This is correct but means the service object from `get_runtime_context()` is `None` for Phase 2 models.

---

### Path 2: ARES Demo (Streamlit UI)
**Entry:** `app/pages/ares_demo.py:render()`
**Flow:**
```
1. st.session_state["selected_model"] (from sidebar)
2. DemoEngine.run_demo(
       model_name=selected_model, ...)
   │
   ├── ARES()                         (ares/_engine.py)
   │   └── _lazy_load()
   │       ├── is_week2_model(model_name)?
   │       │   └── YES → Week2InferenceService
   │       ├── ELSE → load_model_and_tokenizer() → DuplicateQuestionInferenceService
   │       │   └── resolve_model_selection() → tries Week 4 first, falls back to Week 3
   │       └── model_name parameter IGNORED for transformer path!
   │           ↑ FALLS BACK TO WEEK 4 DEFAULT ALWAYS
   └── ARES.predict(q1, q2) → PredictionResult
```

**Root Cause of "Always Week 4":** In `ARES._lazy_load()`, the `_model_name` is set via `with_model()` but `_lazy_load()` does:
```python
self._model_name = self._model_name or get_config("app").get("default_model", DEFAULT_MODEL)
```
If `_model_name` is set (via `with_model("E5-quora-finetuned")`), it should use that. BUT:
- `load_model_and_tokenizer()` only handles `week4` or `week3` internal_ids
- It does NOT handle any Phase 2 model names
- When called with an unknown model name, `resolve_model_selection()` in `settings.py` just checks Week 4 directory → finds it → returns Week 4 as resolution
- So even if ARES passes "E5-quora-finetuned", `load_model_and_tokenizer()` will load Week 4

**Double dispatch problem:**
```
DemoEngine.run_demo()
  → ARES.with_model(selected_model)
  → ARES._lazy_load()
    → load_model_and_tokenizer(PATHS, model_version=selected_model)
      → resolve_model_selection(PATHS)
        → checks week4_improved_model/ → EXISTS → returns week4
        → selected model is IGNORED in resolve_model_selection()
```

---

### Path 3: API (FastAPI)
**Entry:** `src/ares/api/routers/ares_demo.py`
**Flow:**
```
POST /api/v1/ares/chat
  → ChatRequest(question1, question2, model_name, ...)
  → DemoEngine.run_demo(model_name=req.model_name, ...)
  → Same as Path 2 above
```

---

### Path 4: CLI
**Entry:** `src/duplicate_question_app/cli.py`
**Note:** Not fully inspected but likely follows the same `get_model_prediction()` pattern.

---

### Path 5: Batch CSV Prediction (Streamlit UI)
**Entry:** `app/pages/batch_csv.py`
**Flow:**
```
1. Upload CSV with question pairs
2. st.session_state["selected_model"]
3. run_batch_prediction(service, selected_model, question_pairs)
4. Same dispatch logic as Path 1 but with batch-specific optimizations
5. For Phase 2 models: predict_batch_sentence_transformer()
   with vectorized encoding + cosine similarity
6. Results returned as DataFrame
```

---

### Path 6: Ensemble Prediction
**Entry:** `_ensemble/v1.py:get_adaptive_ensemble_prediction()`
**Flow:**
```
1. For each sub-model in ALL 10 models:
   ├── Week 2 LR: Week2InferenceService.predict_single(q1, q2, "week2_lr")
   ├── Week 2 SVM: Week2InferenceService.predict_single(q1, q2, "week2_svm")
   ├── Week 3: DuplicateQuestionInferenceService.predict_single(q1, q2)
   ├── Week 4: DuplicateQuestionInferenceService.predict_single(q1, q2)
   ├── BGE: SentenceTransformer("BAAI/bge-base-en-v1.5").encode()
   │     → cosine similarity → sigmoid calibration
   ├── E5: SentenceTransformer("intfloat/e5-base-v2").encode()
   │     → cosine similarity → sigmoid calibration
   ├── E5-ft: SentenceTransformer(local).encode()
   │     → cosine similarity → sigmoid calibration (auto-upgraded)
   ├── MPNet: SentenceTransformer("sentence-transformers/all-mpnet-base-v2").encode()
   │     → cosine similarity → sigmoid calibration
   ├── DeBERTa CE: CrossEncoder("cross-encoder/nli-deberta-v3-base")
   │     → model.predict() → NLI 3-class → binary conversion
   └── CE-Quora: CrossEncoder(local)
         → model.predict() → binary score
2. Compute adaptive weights based on features (10 rules)
3. Weighted probability average
4. Return ensemble prediction
```

---

### Path 7: Model Manager Page
**Entry:** `app/pages/model_manager.py`
**Flow:**
```
1. build_registry(PATHS)         (_models/registry.py)
   ├── check_week2_artifacts()   checks joblib files
   ├── resolve_model_selection() checks Week 3/4 directories
   ├── HF cache check for BGE/E5/MPNet/DeBERTa (huggingface_hub.scan_cache_dir)
   ├── Local disk check for e5-quora-finetuned, cross-encoder-quora
   └── Returns 11 ModelRegistryEntry objects
2. Display model metadata in UI
3. No inference happens here
```

---

## Complete Call Stack: "Improved DistilBERT (Week 4)" Default

When ARES demo runs with default sidebar selection:

```
app/pages/ares_demo.py:render()
  engine.run_demo(model_name="Improved DistilBERT (Week 4)")
    ares/demo_engine.py:run_demo()
      ARES()
      engine.with_model("Improved DistilBERT (Week 4)")
      engine._lazy_load()
        ares/_engine.py:_lazy_load()
          is_week2_model("Improved DistilBERT (Week 4)") → False
          load_model_and_tokenizer(PATHS, model_version="Improved DistilBERT (Week 4)")
            _inference/transformer.py:load_model_and_tokenizer()
              resolve_model_selection(PATHS)
                _config/settings.py:resolve_model_selection()
                  inspect_model_dir(week4_model_dir) → READY
                  return Resolution(selected="week4", ...)
              model, tokenizer, metadata = load_hugging_face_artifacts(week4_dir)
                AutoModelForSequenceClassification.from_pretrained(week4_dir)
                AutoTokenizer.from_pretrained(week4_dir)
            DuplicateQuestionInferenceService(model, tokenizer, metadata)
          engine._bundle = _ModelBundle(service=DuplicateQuestionInferenceService)
      engine.predict(q1, q2)
        bundle.service.predict_single(q1, q2)
```
