# Technical Debt Report

**Date:** 2026-07-21

---

## Debt Removed During Phase 2.5

| Debt | Location | Impact | Fix |
|------|----------|--------|-----|
| Dead code: unassigned Path expression | `registry.py:110` | None (no-op) | Removed |
| Missing model entries in registry | `registry.py` | 2 models invisible | Added Cross-Encoder-Quora and E5-quora-finetuned |
| Wrong metadata in registry | `registry.py:310-311` | Cosmetic | Fixed hidden_size from 1024 to 768 |
| Fusion conflict penalty bug | `fusion.py:215` | Penalty always 0.3 | Fixed scaling |
| Wrong total_ms in assess_with_reps | `semantic_pipeline.py:106` | Underreported timing | Fixed: uses function-start time |
| Missing mode icon | `sidebar.py:253-255` | Learned weighting strategy shown raw | Added icon |

---

## Remaining Technical Debt

### D-001: BGE-quora-finetuned phantom
- **File:** `settings.py:363`
- **Issue:** `"BGE-quora-finetuned"` is in `FINETUNED_EMBEDDING_MODELS` but has no disk directory, no loading path in `embeddings.py`, and is not in `MODEL_CHOICES`.
- **Risk:** LOW — `is_finetuned_embedding_model()` returns True but `list_available_finetuned_models()` doesn't include it. No code path reaches it.
- **Recommendation:** Remove from `FINETUNED_EMBEDDING_MODELS`.

### D-002: Stale reverse dependency pattern
- **Files:** `app/services/cache.py`, `app/utils/constants.py`
- **Issue:** `app/` imports from `src/` (correct) but `constants.py` accesses `_cache_manager._model_cache` via private attribute.
- **Recommendation:** Use public `get_model()` / `set_model()` API.

### D-003: Hardcoded default models
- **Files:** `sidebar.py:83`, `app.yaml:4`, `runtime.py:49`
- **Issue:** `"Improved DistilBERT (Week 4)"` hardcoded in 3 places.
- **Recommendation:** Single source of truth in config.

### D-004: Duplicate ruff in dev dependencies
- **File:** `pyproject.toml`
- **Issue:** `ruff` listed twice in dev dependencies.
- **Recommendation:** Deduplicate.

### D-005: Stale URL references
- **File:** `pyproject.toml`
- **Issue:** Repository URLs may be out of date.
- **Recommendation:** Update to current repo URL.

### D-006: Unused CLI commands
- **Files:** `cli.py`
- **Issue:** Some CLI commands may not be used in production.
- **Recommendation:** Audit and remove unused commands.

---

## Code Cleanliness Metrics

| Metric | Value |
|--------|-------|
| Total Python files | ~120 |
| Lines of code | ~15,000 |
| Dead code removed | 1 expression, 2 missing model entries |
| Bugs fixed | 7 |
| Remaining issues | 6 (all LOW severity) |
| Test coverage | Unit + Integration + Performance + Regression + Smoke |
