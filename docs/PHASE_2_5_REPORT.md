# Phase 2.5 — Product Polish & Stability Report

**Date:** 2026-07-20
**Objective:** Stabilize the Duplicate Question Detection application into a production-quality ML product through comprehensive audit and targeted fixes.

---

## Summary of Changes

| # | Change | Severity | Files Changed | Status |
|---|--------|----------|---------------|--------|
| 1 | Path resolution bug fix (`parents[2]` → `parents[3]`) | CRITICAL | 7 | ✅ |
| 2 | Removed backward-compat stub files | HIGH | 29 removed, ~50 import updates | ✅ |
| 3 | Consolidated duplicate cache implementations | HIGH | 3 files (created `_inference/cache.py`) | ✅ |
| 4 | Removed orphaned Streamlit pages | HIGH | 12 removed, 2 cleaned up | ✅ |
| 5 | Removed phantom `BGE-quora-finetuned` model | HIGH | 3 YAML + 3 Python | ✅ |
| 6 | Fixed wrong model version in evaluation config | HIGH | 1 | ✅ |
| 7 | Generated comprehensive audit report | MEDIUM | 1 (docs/AUDIT_REPORT.md) | ✅ |
| 8 | Generated this report | MEDIUM | 1 | ✅ |

---

## 1. Path Resolution Bug (Critical)

**Root Cause:** `Path(__file__).resolve().parents[2]` lands on the `src/` directory instead of the project root when the project is installed as a package.

**Files Fixed:**
- `src/duplicate_question_app/_models/embeddings.py:35`
- `src/duplicate_question_app/_models/registry.py:87`
- `src/duplicate_question_app/_dataset/loader.py:37,90`
- `src/duplicate_question_app/_evaluation/hard_mining.py:302`
- `src/duplicate_question_app/_ensemble/agreement.py:296`
- `src/duplicate_question_app/_ensemble/v1.py:211`
- `src/duplicate_question_app/_explainability/trace.py:217`

**Impact:** Fixes "Trained cross-encoder not found" error and all other local model loading failures when running via the installed `dqd-app` command.

---

## 2. Backward-Compat Stub Removal (High)

**29 files removed** from `src/duplicate_question_app/` that existed only as import-only stubs re-exporting from `_`-prefixed subpackages.

**All imports updated** across the codebase (`src/`, `app/`, `tools/`, `tests/`) to point directly to canonical locations:

| Old Import | New Import |
|-----------|------------|
| `duplicate_question_app.config` | `duplicate_question_app._config.settings` |
| `duplicate_question_app.preprocessing` | `duplicate_question_app._preprocessing` |
| `duplicate_question_app.intelligent_ensemble` | `duplicate_question_app._ensemble.v1` |
| `duplicate_question_app.week2_inference` | `duplicate_question_app._models.week2` |
| `duplicate_question_app.explainability` | `duplicate_question_app._explainability.trace` |
| `duplicate_question_app.artifacts` | `duplicate_question_app._artifacts` |
| `duplicate_question_app.inference` | `duplicate_question_app._inference.transformer` |
| `duplicate_question_app.data_loader` | `duplicate_question_app._dataset.loader` |
| `duplicate_question_app.model_registry` | `duplicate_question_app._models.registry` |
| `duplicate_question_app.embedding_models` | `duplicate_question_app._models.embeddings` |
| (and 19 more stubs similarly remapped) | |

---

## 3. Cache Consolidation (High)

**Problem:** Two independent cache implementations: `app/services/cache.py` (Streamlit-aware `CacheManager`) and `_inference/optimizer.py` (with its own `LRUCache`). Core `embeddings.py` imported from `app/` (reverse dependency).

**Solution:** Created `src/duplicate_question_app/_inference/cache.py` as the single canonical cache implementation containing:
- `CacheStats` dataclass
- `LRUCache` class (combined features from both implementations)
- `CacheManager` class with all cache types
- Helper functions (`get_cache`, `cached_embedding`, `cached_preprocessing`)

Then:
- `_inference/optimizer.py` imports `LRUCache` and `CacheStats` from `_inference/cache.py`
- `app/services/cache.py` re-exports from `_inference/cache.py`
- `_models/embeddings.py` now imports from `_inference.cache` instead of `app.services.cache`

---

## 4. Orphaned Streamlit Pages Removed (High)

**12 page files removed** that were not reachable via the navigation sidebar:

- `calibration.py` (redundant — `advanced_calibration.py` is active)
- `error_analysis.py`
- `error_logger.py`
- `evaluation_suite.py`
- `explainability.py`
- `hard_test_generator.py`
- `model_agreement.py`
- `model_comparison.py`
- `models.py`
- `overview.py`
- `performance_optimizer.py`
- `pipeline.py`

**Updated:** `app/pages/__init__.py` to only export the 16 active render functions used by `app/_entry.py`.

**Active pages remain:**
🏠 Home, 🎯 Prediction, 📊 Batch CSV, 📉 Performance, 🧪 Entity/Intent/Negation/Contradiction Detection, 🧪 Lexical Penalty, 🔄 Adaptive Ensemble, ⚙️ Calibration, 💡 Explainability, 📋 Agreement Dashboard, 🔬 Hard Example Mining, 🔗 Model Manager, 📋 Dataset Info

---

## 5. Phantom Model Removal (High)

**Removed `BGE-quora-finetuned`** from:
- `configs/models.yaml` — removed from `finetuned_embedding_models` list
- `_models/embeddings.py` — removed dead code branches in `_get_sigmoid_params()`, `_get_threshold()`, `is_finetuned_model_available()`, `list_available_finetuned_models()`, and `get_sentence_transformer_model()`

**Impact:** Eliminates dead code paths and potential `FileNotFoundError` for a model that does not exist.

---

## 6. Wrong Model Version Fix (High)

**Fixed** `configs/evaluation.yaml:10`:
- `"BGE-base-v1.5"` → `"BGE-base-en-v1.5"`

**Impact:** Evaluation pipeline no longer fails when referencing baseline models from config.

---

## Files Modified Summary

```
Modified:
  src/duplicate_question_app/_models/embeddings.py          (path fix + cache import + clean up phantom model)
  src/duplicate_question_app/_models/registry.py             (path fix)
  src/duplicate_question_app/_dataset/loader.py              (path fix ×2)
  src/duplicate_question_app/_evaluation/hard_mining.py      (path fix)
  src/duplicate_question_app/_ensemble/agreement.py          (path fix)
  src/duplicate_question_app/_ensemble/v1.py                 (path fix)
  src/duplicate_question_app/_explainability/trace.py        (path fix)
  src/duplicate_question_app/__init__.py                     (canonical imports)
  src/duplicate_question_app/_inference/optimizer.py         (canonical LRUCache import)
  src/duplicate_question_app/_inference/cache.py             (NEW — canonical cache)
  app/services/cache.py                                      (thin re-export)
  app/pages/__init__.py                                      (only active pages)
  app/_entry.py                                              (no change needed)
  configs/models.yaml                                        (removed phantom model + dead hub entry)
  configs/evaluation.yaml                                    (fixed model name)
  configs/paths.yaml                                         (kept phantom dir with comment)
  tests/unit/test_stubs.py                                   (canonical imports)
  tools/*.py                                                 (import updates)
  app/**/*.py                                                (import updates)

Removed:
  src/duplicate_question_app/*.py                            (29 backward-compat stubs)
  app/pages/*.py                                             (12 orphaned pages)
```

---

## Remaining Issues (Deferred)

| Issue | Priority | Notes |
|-------|----------|-------|
| Phantom directory paths in config (5 paths to non-existent dirs) | LOW | Code handles gracefully; cosmetic only |
| Duplicate `ruff` in dev dependencies | LOW | No functional impact |
| Stale URL references in pyproject.toml | LOW | Cosmetic |
| Hardcoded path fallback in `_legacy_get_app_paths` | LOW | Works correctly, just duplicated |
| Reverse dependency `app/` importing from `src/` | LOW | Minimal, cache issue resolved |
| Unused CLI commands | LOW | Internal-only, no user-facing impact |
