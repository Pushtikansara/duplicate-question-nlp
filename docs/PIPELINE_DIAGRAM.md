# ARES Pipeline Architecture

```
User Input (q1, q2)
    │
    ├──► Preprocessing ──────────────────────────────► normalize_question()
    │       │ (abbreviation expansion, typo fix)
    │       └─ cached in preprocessing_cache
    │
    ├──► Model Selection
    │       │
    │       ├──► Classical ML (Week 2) ────────────► TF-IDF + LR/SVM
    │       │       └─ cached in model_services cache
    │       │
    │       ├──► Transformer (Week 3/4) ───────────► DistilBERT
    │       │       └─ cached in model_services cache
    │       │
    │       ├──► Bi-Encoder ───────────────────────► BGE / E5 / MPNet
    │       │       │  (cosine sim + sigmoid)
    │       │       └─ cached in embedding_cache + st_models
    │       │
    │       ├──► Cross-Encoder ────────────────────► DeBERTa / CE-Quora
    │       │       │  (softmax over NLI classes)
    │       │       └─ cached in st_models
    │       │
    │       └──► Semantic Ensemble ───────────────► Adaptive weighted
    │               └─ collect_all_votes() → analyze_agreement()
    │
    ├──► Cognitive Perception (optional)
    │       │ PerceptionPipeline.run()
    │       │  - validate → normalize → detect language
    │       │  → tokenize → structural analysis
    │       │  → linguistic analysis → metadata → profile
    │       └─ cached in perception_cache + linguistic_profile_cache
    │
    ├──► Semantic Intelligence (optional)
    │       │ SemanticIntelligenceEngine.assess()
    │       │  - semantic similarity → intent → concept
    │       │  → entity → context → conflicts
    │       └─ cached in semantic_representation_cache
    │
    └──► Fusion (DecisionFusion.fuse())
            │ 8 strategies:
            │ CE-only / Semantic-only / Fusion / CE-dominant
            │ Semantic-dominant / Confidence-weighted / Adaptive / Learned
            └─ conflict_penalty = num_conflicts * 0.3 (capped at max_severity)
```

## Lazy Execution
- CE mode: skips Semantic Engine entirely
- Semantic mode: skips Cross-Encoder entirely
- Fusion mode: runs both

## Data Flow
```
q1, q2
  → predict_with_sentence_transformer (bi-encoder/cross-encoder)
  → DecisionFusion.fuse()
    → _fuse() computes weighted score
    → conflict_penalty applied
    → final_score ∈ [0, 1]
    → "Duplicate" if final_score >= 0.5
```

## Cache Flow
```
Raw text → hash → LRUCache.get(hash)
  miss → compute_fn() → LRUCache.put(hash, result)
  hit  → return cached
```
