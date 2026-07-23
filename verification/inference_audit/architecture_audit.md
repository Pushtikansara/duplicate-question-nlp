# Architecture Audit — Complete

## Overall Inference Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     STREAMLIT UI LAYER                               │
│                                                                      │
│  sidebar.py     pages/prediction.py    pages/ares_demo.py           │
│  _render_model_selector()   render()          render()              │
│      │                       │                   │                   │
│      ▼                       ▼                   ▼                   │
│  st.session_state     get_runtime_context()    DemoEngine           │
│  ["selected_model"]       │                   run_demo()            │
│                           ▼                                        │
│                    get_inference_service()                          │
└───────────────────────────────────┬──────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                    │
│                                                                      │
│  app/utils/constants.py     app/services/runtime.py                 │
│  get_model_prediction()     get_runtime_context()                   │
│  run_batch_prediction()     get_inference_service()                 │
│       │                          │                                  │
│       │                          ▼                                  │
│       │                   resolve_model_selection()                 │
│       │                   _config/settings.py                       │
│       │                          │                                  │
│       ▼                          ▼                                  │
│  Model dispatch (3 backends)                                        │
└───────────────────────────────────┬──────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ BACKEND 1       │    │ BACKEND 2           │    │ BACKEND 3           │
│ Week 2 ML       │    │ Transformer         │    │ SentenceTransformer │
│ joblib/sklearn  │    │ HF Transformers     │    │ & CrossEncoder      │
│                 │    │ PyTorch             │    │ PyTorch             │
│ _models/        │    │ _inference/         │    │ _models/            │
│ week2.py        │    │ transformer.py      │    │ embeddings.py       │
│ Week2Inference  │    │ DuplicateQuestion   │    │ predict_with_       │
│ Service         │    │ InferenceService    │    │ sentence_           │
│                 │    │                     │    │ transformer()       │
│ LR + SVM        │    │ DistilBERT W3/W4    │    │ BGE, E5, MPNet,    │
│                  │    │                     │    │ DeBERTa, CE-Quora  │
└─────────────────┘    └─────────────────────┘    └─────────────────────┘
                                                           │
                                                    ┌──────┴──────┐
                                                    ▼             ▼
                                           ┌──────────────┐ ┌──────────────┐
                                           │ Cosine Sim + │ │ CrossEncoder │
                                           │ Sigmoid Cal  │ │ NLI→Binary   │
                                           └──────────────┘ └──────────────┘
                                                           │
                                                    ┌──────┴──────┐
                                                    ▼             ▼
                                           ┌──────────────┐ ┌──────────────┐
                                           │ Semantic     │ │ Decision     │
                                           │ Intelligence │ │ Fusion       │
                                           │ Engine       │ │ (7 modes)    │
                                           └──────────────┘ └──────────────┘
```

## Model Routing Diagram

```
st.session_state["selected_model"]
         │
         ▼
is_week2_model() ? ──YES──→ Week2InferenceService (Loader 2)
         │
         NO
         │
         ▼
is_ensemble_model() ? ──YES──→ get_ensemble_prediction() (Loader 4)
         │                          └→ Runs all 10 sub-models
         NO
         │
         ▼
is_new_embedding_model() ? ──YES──→ predict_with_sentence_transformer() (Loader 3)
         │                              ├→ get_sentence_transformer_model()
         │                              ├→ Cosine similarity OR CrossEncoder
         │                              └→ Sigmoid calibration
         NO
         │
         ▼
Transformer path ────→ load_model_and_tokenizer() (Loader 1)
                           ├→ resolve_model_selection()
                           │    └→ Week 4 or Week 3 (ignores model name!)
                           ├→ DuplicateQuestionInferenceService
                           └→ predict_single()
```

## Semantic Intelligence Integration

```
After base prediction (any backend):
         │
         ▼
SemanticPipelineService.assess(q1, q2)
         │
         ▼
PerceptionPipeline.analyze(text)
  → Linguistic analysis (concepts, entities, relations, intents, context)
  → SemanticRepresentation
         │
         ▼
SemanticIntelligenceEngine.assess(rep_a, rep_b)
  → ConceptMatcher    (Jaccard overlap of concepts)
  → EntityMatcher     (Jaccard overlap of entities)
  → RelationMatcher   (relation signature overlap)
  → IntentMatcher     (summary comparison + shared actions)
  → ContextMatcher    (domain + key overlap + value agreement)
  → ConflictDetector  (opposite actions, domain mismatch, etc.)
  → ConfidenceFusion  (weighted average of 5 scores)
  → EvidenceBuilder   (structured evidence items)
  → DecisionSupport   (DUPLICATE/NOT_DUPLICATE/UNCERTAIN)
         │
         ▼
DecisionFusion.fuse(ce_score, semantic_assessment)
  → 7 fusion strategies
  → Weighted combination + conflict penalty
  → final_score, final_prediction
```

## ARES Framework Integration

```
ARES Demo Page
         │
         ▼
DemoEngine.run_demo()
  ├── PlanningEngine (Planner, Validator, Optimizer, Executor)
  ├── ARES.predict()  ←──── ONLY handles Week 2/3/4, NOT Phase 2
  ├── MemoryManager (store + retrieve results)
  ├── ReflectionEngine (trust scoring)
  └── OrchestrationEngine (agent coordination)
```

## Key Architecture Issues

### Issue 1: No Singleton Model Registry
Models are loaded on-demand through multiple independent paths:
- `get_inference_service()` in `runtime.py`
- `get_sentence_transformer_model()` in `embeddings.py` (with its own cache)
- `InferenceOptimizer` in `optimizer.py` (with separate cache)
- `ARES._lazy_load()` in `_engine.py` (with its own bundle)

These caches are NOT shared. Loading a model through one path and then through another creates two instances in memory.

### Issue 2: Service Object is None for Phase 2 Models
In `runtime.py:get_inference_service()`:
```python
if is_new_embedding_model(selected):
    metadata = _build_metadata(...)
    _model_cache[cache_lookup_key] = (None, metadata)  # ← service is None!
    return None, metadata
```

Then in `constants.py:get_model_prediction()`:
```python
service, metadata, _ = get_runtime_context()
# service might be None for Phase 2 models!
# But the code passes service to get_model_prediction() anyway
```

This works because `get_model_prediction()` has an `if/elif/else` chain that dispatches BEFORE using `service`. But if a new model type is added, `service` being `None` is a hidden trap.

### Issue 3: Config-Driven vs Hardcoded Model Lists
Model classification functions exist in two places:
1. `_config/settings.py`: `is_transformer_model()`, `is_sentence_transformer_model()`, etc. — driven by `configs/models.yaml`
2. `_models/week2.py`: `is_week2_model()` — driven by hardcoded string matching

The YAML config is the source of truth for model metadata, but Week 2 detection is hardcoded. If a new Week-2-like model is added to YAML, `is_week2_model()` won't recognize it.

### Issue 4: Model Manager Has No Backend Selection Logic
`build_registry()` in `_models/registry.py` catalogs all 11 models with metadata like `model_type`, `framework`, `source`, but:
- There is NO `backend` field in the registry
- There is NO `loader` field or loader selection mechanism
- The registry is display-only (used by sidebar and Model Manager page)
- The actual dispatch to loaders happens in `get_model_prediction()` via string-based `if/elif/else` chain

### Issue 5: No Fallback Strategy for Phase 2 Models in ARES
When ARES receives a Phase 2 model name, it silently falls back to Week 4 without:
- Logging a warning
- Notifying the caller
- Attempting to load the Phase 2 model through the correct path
- Returning an error

This makes it appear that ARES supports Phase 2 models when it actually doesn't.
