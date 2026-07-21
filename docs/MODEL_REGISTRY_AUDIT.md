# Model Registry Audit Report

**Date:** 2026-07-21
**Auditor:** ARES Production Stabilization

---

## Models Registered: 11 / 11

| # | Display Name | Internal ID | Type | Status | Artifacts |
|---|-------------|-------------|------|--------|-----------|
| 1 | TF-IDF + Logistic Regression (Week 2) | `week2_lr` | classical-ml | available | ✅ |
| 2 | TF-IDF + Linear SVM (Week 2) | `week2_svm` | classical-ml | available | ✅ |
| 3 | DistilBERT (Week 3) | `week3` | transformer | loaded | ✅ |
| 4 | Improved DistilBERT (Week 4) | `week4` | transformer | loaded | ✅ |
| 5 | BGE-base-en-v1.5 | `bge` | bi-encoder | available (auto-download) | ✅ |
| 6 | E5-base-v2 | `e5` | bi-encoder | available (auto-download) | ✅ |
| 7 | E5-quora-finetuned | `e5_ft` | bi-encoder | loaded | ✅ |
| 8 | MPNet-base-v2 | `mpnet` | bi-encoder | available (auto-download) | ✅ |
| 9 | DeBERTa-v3 Cross-Encoder | `deberta` | cross-encoder | available (auto-download) | ✅ |
| 10 | Cross-Encoder-Quora (Trained) | `ce_quora` | cross-encoder | loaded | ✅ |
| 11 | Semantic Ensemble | `ensemble` | ensemble | loaded | ✅ |

---

## Discovery Compliance

| Check | Status | Notes |
|-------|--------|-------|
| All MODELS in MODEL_CHOICES registered | ✅ | 11/11 models registered |
| All models discoverable via `build_registry()` | ✅ | Returns 11 entries |
| All models findable via `find_registry_entry()` | ✅ | Verified for all 11 |
| Models visible in sidebar | ✅ | Search + filter + categories |
| Models visible in Model Manager page | ✅ | Table + search + details |
| Models visible in Home page | ✅ | Registry table on landing |
| Models loadable via embeddings.py | ✅ | All 11 have loading paths |
| Models predictable via get_model_prediction() | ✅ | All 11 dispatch routes exist |

---

## Bugs Found & Fixed

### Bug 1: Cross-Encoder-Quora (Trained) missing from registry
- **File:** `src/duplicate_question_app/_models/registry.py`
- **Issue:** The model existed on disk (`models/cross-encoder-quora/`, 703 MB), was listed in `MODEL_CHOICES` and `configs/models.yaml`, but was **not registered** in `build_registry()`.
- **Impact:** Not visible in Model Manager, sidebar registry data, or `find_registry_entry()`.
- **Fix:** Added entry with `internal_id="ce_quora"`, `type="cross-encoder"`, dynamic status from disk check.

### Bug 2: E5-quora-finetuned missing from registry
- **File:** `src/duplicate_question_app/_models/registry.py`
- **Issue:** Model existed on disk (`models/e5-quora-finetuned/`, 418 MB), listed in `MODEL_CHOICES`, but not registered.
- **Impact:** Not visible in any model listing.
- **Fix:** Added entry with `internal_id="e5_ft"`, `type="bi-encoder"`, dynamic status.

### Bug 3: DeBERTa-v3 incorrect hidden_size
- **File:** `src/duplicate_question_app/_models/registry.py` (line 310-311)
- **Issue:** Registry listed `embedding_size=1024, hidden_size=1024` for DeBERTa-v3, but the actual model has `hidden_size=768`.
- **Fix:** Corrected to `embedding_size=768, hidden_size=768`.

### Bug 4: Dead code in registry.py
- **File:** `src/duplicate_question_app/_models/registry.py` (line 110)
- **Issue:** `paths.models_dir / "week2_models" / "tfidf_vectorizer.joblib"` — unassigned Path expression.
- **Fix:** Removed dead code.

---

## Disk Model Discovery

| Model Directory | Exists | Size | Status |
|----------------|--------|------|--------|
| `models/week2_models/` | ✅ | 3 files | All joblib artifacts present |
| `models/saved_transformer_model/` | ✅ | 255 MB | Week 3 DistilBERT |
| `models/week4_improved_model/` | ✅ | 255 MB | Week 4 DistilBERT |
| `models/cross-encoder-quora/` | ✅ | 703 MB | Trained Cross-Encoder |
| `models/e5-quora-finetuned/` | ✅ | 418 MB | Fine-tuned E5 |
| `models/bge_base_en_v1_5/` | ❌ | — | Auto-download from HF |
| `models/e5_base_v2/` | ❌ | — | Auto-download from HF |
| `models/mpnet_base_v2/` | ❌ | — | Auto-download from HF |
| `models/deberta_v3_cross_encoder/` | ❌ | — | Auto-download from HF |
| `models/bge-quora-finetuned/` | ❌ | — | Reserved, not created |

---

## Summary

- **11/11 models** registered, discoverable, and visible in UI.
- **Cross-Encoder-Quora (Trained)** and **E5-quora-finetuned** were missing — now fixed.
- All models have proper loading paths in `embeddings.py`.
- Phase 2 models (BGE, E5, MPNet, DeBERTa) auto-download from HuggingFace on first use.
- BGE-quora-finetuned remains a phantom model — no disk artifacts, no loading path, not in MODEL_CHOICES. Should be cleaned from `FINETUNED_EMBEDDING_MODELS` in a future phase.
