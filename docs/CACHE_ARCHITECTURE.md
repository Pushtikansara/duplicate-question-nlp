# ARES Cache Architecture

## Overview
Seven caches managed by `CacheManager` in `_inference/cache.py`.

## Cache Types

| Cache | Type | Max Size | Key Format | Usage |
|-------|------|----------|------------|-------|
| embedding | LRUCache | 10,000 | `model_name:text_hash` | Sentence embeddings |
| preprocessing | LRUCache | 5,000 | Raw text | normalize_question output |
| semantic_representation | LRUCache | 500 | `sem_rep:text_hash` | SemanticRepresentation objects |
| linguistic_profile | LRUCache | 500 | `ling_profile:text_hash` | LinguisticProfile objects |
| perception | LRUCache | 500 | `perception:text_hash` | PerceptionPipeline results |
| st_models | dict | unbounded | model_name | Loaded SentenceTransformer/CrossEncoder |
| model_services | LRUCache | 50 | service key | Loaded model services |

## Design Decisions

### Why `st_models` stays unbounded
Only ~11 models max are ever loaded. Memory bound by model count, not input diversity.

### Why `_model_cache` was converted to LRU (50 max)
Was a plain dict — unbounded growth possible from dynamic model creation in ensemble.

## Thread Safety
- `CacheManager._lock` wraps all public methods
- Each LRUCache has its own `threading.RLock`
- CacheManager operations use `_model_cache_lock` and `_st_cache_lock`

## Key Functions
- `cached_embedding(model_name, text, compute_fn)` — compute + cache
- `cached_preprocessing(text, compute_fn)` — text normalization cache
- `cached_perception(text, compute_fn)` — perception pipeline cache
- `cached_linguistic_profile(text, compute_fn)` — linguistic profile cache
- `cached_semantic_representation(text, compute_fn)` — semantic rep cache
