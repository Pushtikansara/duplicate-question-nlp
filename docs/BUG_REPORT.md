# Bug Report — ARES Production Stabilization

**Date:** 2026-07-21
**Scope:** All bugs identified and fixed during Phase 2.5 audit.

---

## Critical Bugs (Fixed)

### B-001: Cross-Encoder-Quora (Trained) not visible in UI
- **Severity:** HIGH
- **File:** `src/duplicate_question_app/_models/registry.py`
- **Root Cause:** Model existed on disk and in config but was NOT registered in `build_registry()`.
- **Fix:** Added full entry with dynamic status detection from disk.
- **Verification:** Now visible in sidebar, Model Manager, and Home page.

### B-002: E5-quora-finetuned not visible in UI
- **Severity:** HIGH
- **File:** `src/duplicate_question_app/_models/registry.py`
- **Root Cause:** Same as B-001 — model existed on disk but not registered.
- **Fix:** Added full entry with dynamic status detection.

### B-003: Fusion conflict penalty doesn't scale
- **Severity:** HIGH
- **File:** `src/duplicate_question_app/_semantic_intelligence/fusion.py:215`
- **Root Cause:** `num_conflicts * 0.3 / max(1, num_conflicts)` always equals `0.3`.
  The denominator `max(1, num_conflicts)` cancels out `num_conflicts` in the numerator.
- **Fix:** Changed to `num_conflicts * 0.3` and cap at `max_severity` and `1.0`.
- **Before:** 1 conflict = 0.3 penalty, 10 conflicts also = 0.3 penalty.
- **After:** 1 conflict = 0.3 penalty, 3 conflicts = 0.9 penalty (capped at severity).

### B-004: `assess_with_representations()` wrong total_ms
- **Severity:** MEDIUM
- **File:** `src/duplicate_question_app/_semantic_intelligence/semantic_pipeline.py:106`
- **Root Cause:** `total_ms` computed from `t_start` (engine start time) instead of function entry time.
- **Fix:** Added `t0 = time.perf_counter()` at function entry, use `(now - t0) * 1000` for total_ms.
- **Impact:** Pipeline total time was underreported by the perception pipeline duration.

---

## Moderate Bugs (Fixed)

### B-005: DeBERTa-v3 registry metadata wrong
- **Severity:** LOW
- **File:** `src/duplicate_question_app/_models/registry.py:310-311`
- **Issue:** Registry listed `hidden_size=1024` for DeBERTa-v3, actual is 768.
- **Fix:** Corrected to 768.

### B-006: Dead code in registry.py
- **Severity:** LOW
- **File:** `src/duplicate_question_app/_models/registry.py:110`
- **Issue:** Unassigned Path expression `paths.models_dir / "week2_models" / "tfidf_vectorizer.joblib"`.
- **Fix:** Removed dead code.

### B-007: `learned_weighting` missing from sidebar icons
- **Severity:** LOW
- **File:** `app/components/sidebar.py:253-255`
- **Issue:** The `learned_weighting` strategy mode icon was missing.
- **Fix:** Added `"learned_weighting": "⚪ LEARNED"` to the mode icons dict.

---

## Remaining Issues (Deferred)

### R-001: BGE-quora-finetuned phantom model
- **Severity:** LOW
- **Issue:** In `FINETUNED_EMBEDDING_MODELS` set but no disk directory, no loading path, not in MODEL_CHOICES.
- **Recommendation:** Remove from `FINETUNED_EMBEDDING_MODELS` or create model directory.

### R-002: Else clause in `embeddings.py:237` potential TypeError
- **Severity:** LOW
- **Issue:** If `scores` is a scalar float, `scores[0]` raises TypeError.
- **Recommendation:** Add type check for scalar scores.

### R-003: Framework display name
- **Severity:** COSMETIC
- **Issue:** `"sentence-transformers".upper()` = `"SENTENCE-TRANSFORMERS"`.
- **Recommendation:** Use `.title()` instead of `.upper()`.

### R-004: Phantom model directory paths in config
- **Severity:** LOW
- **Issue:** 5 non-existent model directories in `paths.yaml`.
- **Recommendation:** Keep as-is — code handles gracefully with auto-download.
