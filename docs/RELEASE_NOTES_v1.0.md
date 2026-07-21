# ARES v1.0 — Release Notes

## Overview
ARES (Advanced Retrieval and Evaluation System) v1.0 is a production-stable duplicate question detection platform with 11 models, semantic intelligence, and an adaptive ensemble. This release stabilizes the codebase, fixes 35+ bugs, and ensures all models are visible, searchable, and predictable.

## What's New

### Model Registry (11 models)
- Week 2: TF-IDF + Logistic Regression, TF-IDF + Linear SVM
- Week 3: DistilBERT
- Week 4: Improved DistilBERT
- Bi-encoders: BGE-base-en-v1.5, E5-base-v2, E5-quora-finetuned, MPNet-base-v2
- Cross-encoders: DeBERTa-v3 Cross-Encoder, Cross-Encoder-Quora (Trained)
- Semantic Ensemble (adaptive weighted)

### Cache Architecture
- 7 LRU caches with configurable max sizes
- Embedding cache (10K), preprocessing (5K), semantic representation (500), linguistic profile (500), perception (500), ST models, model services (50)
- Thread-safe with RLock
- Cache stats tracking (hits, misses, evictions)

### Fusion System
- 8 fusion strategies: CE-only, semantic-only, fusion, CE-dominant, semantic-dominant, confidence-weighted, adaptive, learned-weighting
- Conflict-aware penalty scaling with severity bounds
- Provenance tracking via explanation builder

## Bug Fixes
- Cross-Encoder-Quora and E5-quora-finetuned added to registry (were missing)
- BGE-quora-finetuned removed from FINETUNED_EMBEDDING_MODELS (phantom model, never existed)
- Unbounded `_model_cache` and `sentence_transformer_cache` converted to LRU with max_size bounds
- `assess_with_representations()` metadata now includes `cache_hits` key (was missing)
- Fusion conflict penalty `num_conflicts * 0.3` capped at max severity (was unbounded)
- DeBERTa-v3 hidden_size corrected from 1024 to 768
- Ensemble v1 now includes E5-quora-finetuned and Cross-Encoder-Quora in weighting
- Perception pipeline import: `cached_semantic_representation` added to imports (was missing)
- Dead code removed from registry.py

## Performance
- 491/492 unit tests passing
- All 11 models load correctly
- LRU caches prevent unbounded memory growth
- O(n) ensemble weighting (was O(n*5))

## Known Issues
- `test_predict_with_csv_runs` fails due to stale module path (pre-existing)
- CUDA not auto-detected for cross-encoders (CPU-only)
- No live GPU acceleration for batch inference
