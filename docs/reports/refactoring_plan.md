# Refactoring Plan — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Guiding Principles

1. **Never change business logic** — All refactoring preserves exact behavior
2. **Never reduce prediction quality** — Output probabilities and decisions must be identical
3. **Never remove working functionality** — Only relocate or rename
4. **Small, verifiable steps** — Each refactoring must be independently testable
5. **Preserve backward compatibility** — Public API in `__init__.py` and `cli.py` must not change

---

## 2. Refactoring Catalog

### R-01: Break Circular Dependency (_models ↔ _ensemble)

**Current state:**
- `_models/embeddings.py` imports `get_adaptive_ensemble_prediction` from `_ensemble/v1.py`
- `_ensemble/v1.py` and `_ensemble/agreement.py` import prediction functions from `_models/embeddings.py`

**Target state:**
- `_models/embeddings.py` removes `get_ensemble_prediction()` — move it to `_ensemble/v1.py`
- `_models/embeddings.py` removes all direct references to `_ensemble`
- `_ensemble/` imports cleanly from `_models/`

**Steps:**
1. Move `get_ensemble_prediction()` from `embeddings.py` to `ensemble/v1.py`
2. Update all callers of `get_ensemble_prediction()` to import from `_ensemble/v1.py`
3. Verify no remaining imports from `_models/` to `_ensemble/`

**Risk:** Low — purely mechanical move
**Effort:** 1 day

---

### R-02: Break Reverse Dependency (_models → app/)

**Current state:**
- `_models/embeddings.py` imports `get_cache` from `app/services/cache.py`
- `app/services/cache.py` is a thin re-export from `_inference/cache.py`

**Target state:**
- `_models/embeddings.py` imports `get_cache` directly from `_inference/cache.py`
- No `src/` module imports from `app/`

**Status:** ✅ Already completed in Phase 2.5
**Verification:** Confirm `_models/embeddings.py` imports from `_inference.cache`

---

### R-03: Split God Module `_models/embeddings.py` (410 lines)

**Current state:** Single file containing:
- Path resolution
- Device detection
- Model loading (sentence-transformers)
- E5 model auto-upgrade
- Sigmoid parameter lookup
- Threshold lookup
- Single prediction
- Batch prediction
- Ensemble prediction entry point
- Fine-tuned model availability checks
- Cache clearing

**Target state:** Split into:
- `_models/loader.py` — Model loading, caching, device detection
- `_models/predictors.py` — Single and batch prediction
- `_models/calibration.py` — Sigmoid params, threshold lookup (or keep in embeddings.py as thin coordinator)

**Steps:**
1. Extract `get_sentence_transformer_model()` → `_models/loader.py`
2. Extract `_get_sigmoid_params()`, `_get_threshold()` → `_models/calibration.py`
3. Extract `resolve_best_available_e5_model()` → `_models/loader.py`
4. Extract `predict_with_sentence_transformer()`, `predict_batch_sentence_transformer()` → `_models/predictors.py`
5. Extract `is_finetuned_model_available()`, `list_available_finetuned_models()` → `_models/loader.py`
6. Extract `clear_embedding_cache()` → `_models/loader.py`
7. Move `get_ensemble_prediction()` → `_ensemble/v1.py` (see R-01)
8. Update all imports

**Risk:** Low-Medium — mechanical but many callers
**Effort:** 2 days

---

### R-04: Consolidate Tool Argument Parsing

**Current state:** Each of 12 tools/ scripts has its own argparse, often duplicating:
- `--model-dir`, `--data-dir`, `--output-dir` paths
- `--device`, `--batch-size`, `--seed` parameters

**Target state:** Shared argument parser in `tools/__init__.py` or `tools/arg_parser.py`

**Steps:**
1. Create `tools/arg_parser.py` with common arguments (model paths, data paths, device, seed, batch size)
2. Create convenience builders for model-specific args
3. Update each script to use shared parser + script-specific additions
4. Verify all scripts produce same results

**Risk:** Low
**Effort:** 2 days

---

### R-05: Add Config Schema Validation

**Current state:** `_config/loader.py` loads YAML values without validation. Typos or missing keys silently default to unexpected values.

**Target state:** Each YAML file has a corresponding Pydantic/msgspec schema that validates:
- Required keys present
- Value types correct
- Allowed values for enums
- File paths exist (or warn)

**Steps:**
1. Define schema for each YAML file using `msgspec` or `pydantic`
2. Add validation step after loading each config
3. Raise `ConfigurationError` with descriptive message on validation failure
4. Remove environment override handling from loader (let schema handle type coercion)

**Risk:** Medium — new dependency; may break if config values are not as expected
**Effort:** 3 days

---

### R-06: Add Experiment Tracking Interface

**Current state:** No experiment tracking. Results are printed to stdout or saved to files without structured logging.

**Target state:** Abstract `ExperimentTracker` interface with:
- `log_params(params: dict)`
- `log_metrics(metrics: dict, step: int)`
- `log_artifact(path: str)`
- `save()` / `load()`

With concrete implementations:
- `StdoutTracker` (print to console — default)
- `MLflowTracker` (log to MLflow)
- `JsonFileTracker` (log to JSON file)

**Steps:**
1. Define `_tracking/` subpackage with abstract interface
2. Implement `StdoutTracker`
3. Integrate into `tools/` scripts
4. Add environment config to select tracker type

**Risk:** Low — additive change only
**Effort:** 2 days

---

### R-07: Add Dependency Injection for Cache Manager

**Current state:** `CacheManager` is a global singleton accessed via `get_cache()`. Hard to mock or replace.

**Target state:** `CacheManager` is injectable, with singleton as default:
- `InferenceOptimizer.__init__(cache_manager=None)` → uses provided or `get_cache()`
- Test code can pass `MockCacheManager()`

**Steps:**
1. Add optional `cache_manager` parameter to classes that use cache
2. Default to `get_cache()` if not provided
3. Add `MockCacheManager` for testing

**Risk:** Low
**Effort:** 1 day

---

### R-08: Standardize Docstrings

**Current state:** Mix of styles:
- Google-style
- NumPy-style
- Descriptive comments
- Missing docstrings

**Target state:** All public functions have Google-style docstrings with:
- Description
- Args
- Returns
- Raises

**Steps:**
1. Configure `ruff` docstring convention
2. Add missing docstrings to all public functions
3. Standardize existing docstrings

**Risk:** Low
**Effort:** 2 days

---

### R-09: Add File Header Standardization

**Current state:** Inconsistent file headers — some have docstrings, some have copyright, some nothing.

**Target state:** Every `.py` file has:
```python
"""<One-line description>.

<Optional: multi-line description with usage examples>
"""

from __future__ import annotations
```

**Steps:**
1. Standardize all file headers
2. Add `from __future__ import annotations` to files missing it

**Risk:** Low
**Effort:** 1 day

---

### R-10: Improve Cache Invalidation

**Current state:** Caches grow unboundedly; no TTL mechanism; `clear_all()` is only invalidation.

**Target state:** `LRUCache` supports:
- Per-entry TTL (time-to-live)
- Max age eviction
- Size-based eviction (current behavior)
- Event hooks for eviction callbacks

**Steps:**
1. Add optional TTL parameter to `LRUCache.put()`
2. Add background eviction thread or lazy check on `get()`
3. Add eviction callback support

**Risk:** Low-Medium — must preserve thread safety
**Effort:** 2 days

---

## 3. Refactoring Roadmap

```
Sprint 1 (Week 1-2):
  ├── R-01: Break circular dependency
  ├── R-02: Verify reverse dependency fix
  └── R-04: Consolidate tool argparse

Sprint 2 (Week 3-4):
  ├── R-03: Split god module
  ├── R-07: Cache DI
  └── R-10: Cache invalidation

Sprint 3 (Week 5-6):
  ├── R-05: Config validation
  ├── R-08: Docstring standardization
  └── R-09: File headers

Sprint 4 (Week 7-8):
  └── R-06: Experiment tracking
```

---

## 4. Verification Strategy

Each refactoring must pass:

1. **Syntax check:** `python -c "import py_compile; py_compile.compile('file.py')"`
2. **Import check:** `python -c "from duplicate_question_app import *"`
3. **Existing tests:** `pytest tests/ -v`
4. **CLI smoke test:** `dqd-predict "How to cook pasta" "How to boil spaghetti"`
5. **Same output:** Compare before/after predictions on 10 test pairs
