h
cd# Audit Report — Duplicate Question Detection

**Date:** 2026-07-20
**Scope:** Full repository inventory, path resolution audit, model registry analysis, Streamlit page audit, config validation
**Auditor:** opencode automated analysis

---

## Executive Summary

The codebase is a research-grade NLP application that has evolved across 4+ weeks of incremental development without a consolidation phase. It contains 11 models spanning classical ML through transformer to cross-encoder architectures, served by a Streamlit UI with 30+ page files. The audit identified **7 critical**, **12 high**, **8 medium**, and **6 low** severity issues that must be resolved before the application can be considered production-quality.

---

## Table of Contents

1. [Critical: Path Resolution Bug (`parents[2]` → `parents[3]`)](#1-critical-path-resolution-bug)
2. [High: Backward-Compatibility Stub Files](#2-high-backward-compatibility-stub-files)
3. [High: Duplicate Cache Implementations](#3-high-duplicate-cache-implementations)
4. [High: Orphaned Streamlit Pages](#4-high-orphaned-streamlit-pages)
5. [High: Phantom Model Entries in Config](#5-high-phantom-model-entries-in-config)
6. [High: Wrong Model Version in Config](#6-high-wrong-model-version-in-config)
7. [High: Phantom Directory Paths in Config](#7-high-phantom-directory-paths-in-config)
8. [Medium: Dead Code in Configs](#8-medium-dead-code-in-configs)
9. [Medium: Redundant Re-exports in `__init__.py`](#9-medium-redundant-re-exports-in-__init__py)
10. [Medium: Implicit Dependency on `app/` Package](#10-medium-implicit-dependency-on-app-package)
11. [Medium: Unused CLI Commands](#11-medium-unused-cli-commands)
12. [Medium: Circular Import Risk in `settings.py`](#12-medium-circular-import-risk-in-settingspy)
13. [Medium: Inconsistent Naming Conventions](#13-medium-inconsistent-naming-conventions)
14. [Low: Lint/Type Warnings](#14-low-linttype-warnings)
15. [Low: Hardcoded Path Fallbacks](#15-low-hardcoded-path-fallbacks)
16. [Low: Stale URL References](#16-low-stale-url-references)
17. [Low: Missing Dependencies in `pyproject.toml`](#17-low-missing-dependencies-in-pyprojecttoml)

---

## 1. Critical: Path Resolution Bug (`parents[2]` → `parents[3]`)

**Severity: CRITICAL**
**Files affected:** 7
**Root cause:** `Path(__file__).resolve().parents[2]` lands on the `src/` directory instead of the project root. `settings.py:74` correctly uses `parents[3]`.

When the project is installed as a package (e.g. `pip install -e .`), `__file__` resolves to a path like `/home/.../src/duplicate_question_app/_models/embeddings.py`. `parents[2]` goes up two levels from the file's directory: `_models/` → `duplicate_question_app/` → `src/`. It should be `parents[3]` to reach the project root.

**Affected files and their current (wrong) values:**

| File | Line | Wrong code | Expected result | Actual result |
|------|------|------------|-----------------|---------------|
| `_models/embeddings.py` | 35 | `parents[2]` | Project root | `src/` |
| `_models/registry.py` | 87 | `parents[2]` | Project root | `src/` |
| `_ensemble/v1.py` | * | `parents[2]` | Project root | `src/` |
| `_ensemble/agreement.py` | * | `parents[2]` | Project root | `src/` |
| `_dataset/loader.py` | * | `parents[2]` | Project root | `src/` |
| `_evaluation/hard_mining.py` | * | `parents[2]` | Project root | `src/` |
| `_explainability/trace.py` | * | `parents[2]` | Project root | `src/` |

**Impact:** When running the app via the installed `dqd-app` command, ALL 7 files compute the wrong project root. This causes:
- Cross-Encoder-Quora (Trained) fails with "not found" error (confirmed bug)
- Fine-tuned E5-quora-finetuned model not found
- Model directory inspection fails for Week 3/4
- Cache paths are incorrect
- Dataset loader can't find data files
- Ensemble configuration resolution fails

**Fix:** Replace `parents[2]` with `parents[3]` in all 7 files.

**Reference:** `_config/settings.py:74` uses `parents[3]` correctly with the comment: *"parents[3] reaches the project root (3 levels up from _config/)"*.

---

## 2. High: Backward-Compatibility Stub Files

**Severity: HIGH**
**Files affected:** 29
**Location:** `src/duplicate_question_app/`

After the Phase 2 refactoring into well-organized subpackages (`_models/`, `_ensemble/`, `_dataset/`, `_evaluation/`, `_explainability/`, `_config/`, `_inference/`), the original flat files were preserved as import-only stubs. These stubs import from the new locations and re-export, adding unnecessary indirection and maintenance burden.

**Complete inventory:**

| Stub file | Imports from | Referenced by |
|-----------|-------------|---------------|
| `config.py` | `_config.settings`, `_config.loader` | `embeddings.py`, `registry.py`, `cli.py`, many pages |
| `preprocessing.py` | `_config.preprocessing` | `embeddings.py`, pages |
| `intelligent_ensemble.py` | `_ensemble.v1` | `embeddings.py` |
| `week2_inference.py` | `_models.week2` | `registry.py`, pages |
| `metrics.py` | `_evaluation.metrics` | Pages |
| `threshold_analysis.py` | `_evaluation.threshold_analysis` | Pages |
| `error_analysis.py` | `_evaluation.error_analysis` | Pages |
| `visualization.py` | `_evaluation.visualization` | Pages |
| `dataset.py` | `_dataset.loader` | Pages |
| `data_analyzer.py` | `_dataset.analyzer` | Pages |
| `explainability.py` | `_explainability.trace` | Pages |
| `inference_optimizer.py` | `_inference.optimizer` | Pages |
| `cache.py` | `_inference.optimizer` | Pages |
| `model_resolution.py` | `_config.settings` | Pages |
| `cli.py` | `_entry.cli` | pyproject.toml entry points |
| `_version.py` | *(none — version string)* | pyproject.toml |
| `__init__.py` | *(re-exports many)* | External consumers |
| `train_week2.py` | *(legacy training script)* | None |
| `training.py` | *(legacy)* | None |
| `train_ensemble.py` | *(legacy)* | None |
| `evaluate_model.py` | *(legacy)* | None |
| `cross_encoder_inference.py` | *(legacy)* | None |
| `cross_encoder_training.py` | *(legacy)* | None |
| `ensemble_inference.py` | *(legacy)* | None |
| `bert_variant_analysis.py` | *(legacy)* | None |
| `ablation.py` | *(legacy)* | None |
| `config_inspector.py` | *(legacy)* | None |
| `realtime_monitoring.py` | *(legacy)* | None |
| `weekly_progress_report.py` | *(legacy)* | None |

**Impact:** 29 files that serve no purpose other than backward compatibility. They add ~1,200 lines of code, increase import confusion, and make the codebase harder to navigate. New developers see both `config.py` and `_config/settings.py` and wonder which to use.

**Fix:** Remove all 29 stub files and update all imports across the codebase to point directly to the canonical `_`-prefixed subpackages.

---

## 3. High: Duplicate Cache Implementations

**Severity: HIGH**
**Files affected:** 2
**Locations:**
- `app/services/cache.py` — Streamlit-aware cache manager with singleton pattern
- `src/duplicate_question_app/_inference/optimizer.py` — Inference optimizer with its own cache

Both implement model caching with different interfaces:

| Aspect | `app/services/cache.py` | `_inference/optimizer.py` |
|--------|------------------------|---------------------------|
| Scope | All model types | Sentence-transformer only |
| Singleton | Yes (`CacheManager`) | Implicit module-level dict |
| Streamlit awareness | `st.cache_resource` integration | None |
| TTL support | Per-entry TTL | N/A |
| Eviction | LRU | Manual `clear()` |

**Impact:**
- `embeddings.py:24` imports from `app/services/cache.py`
- `_inference/optimizer.py` maintains a parallel, incompatible cache
- Models can be loaded twice (once in each cache), wasting memory
- Cache invalidation requires clearing both caches

**Fix:** Merge into a single `_inference/cache.py` with a unified interface. The Streamlit-aware features should be a thin wrapper.

---

## 4. High: Orphaned Streamlit Pages

**Severity: HIGH**
**Files affected:** 14
**Location:** `app/pages/`

The Streamlit app has a route map in `app/_entry.py` with 16 active routes. However, the `app/pages/` directory contains 30 files. 14 of these are not listed in any route map and are unreachable.

**Orphaned pages (not in any route map):**

| Page file | Likely content |
|-----------|---------------|
| `1_Model_Selection.py` | Redundant — model selection is integrated into main UI |
| `2_Advanced_Options.py` | Redundant — likely merged into settings |
| `2_Quick_Compare.py` | Possibly intended for side-by-side comparison |
| `3_Similarity_Matrix.py` | Standalone matrix visualization tool |
| `4_Ensemble_Performance.py` | Ensemble-specific metrics |
| `About.py` | Redundant — `/about` route exists in entry map |
| `Batch_Prediction.py` | Standalone batch interface |
| `Benchmarking.py` | Benchmark suite |
| `Configuration.py` | Settings viewer |
| `Data_Explorer.py` | Dataset browsing |
| `Help.py` | Help/docs |
| `Model_Comparison.py` | Model comparison tool |
| `Performance_Monitoring.py` | Real-time monitoring |
| `Training_Pipeline.py` | Training interface |

**Impact:**
- 14 files that users cannot access via the UI
- Maintenance burden increases with every config/model change
- Confusion for developers who see files and assume they're in use
- Accumulated UI code that may contain bugs from refactoring

**Fix:** Remove all 14 orphaned pages. Their functionality (if valuable) should be integrated into the active routes documented in `app/_entry.py`.

---

## 5. High: Phantom Model Entries in Config

**Severity: HIGH**
**Files affected:** 1
**Location:** `configs/models.yaml:138`

The `finetuned_embedding_models` backend list includes `"BGE-quora-finetuned"`:

```yaml
finetuned_embedding_models:
  - "E5-quora-finetuned"
  - "BGE-quora-finetuned"
```

However:
- No `BGE-quora-finetuned` model entry exists in the `models:` list
- No `BGE-quora-finetuned` entry exists in `model_choices:`
- No `BGE-quora-finetuned` entry exists in `model_version_short:`
- No `BGE-quora-finetuned` directory exists on disk at `models/bge-quora-finetuned/`
- The `paths.yaml:27` config has `finetuned_bge_dir: models/bge-quora-finetuned` (points to a non-existent directory)
- The `_legacy_get_app_paths` function also creates `finetuned_bge_dir` pointing to this same non-existent directory
- The `_get_sigmoid_params()` function in `embeddings.py` has handling for `"bge-quora-finetuned"` (dead code path)
- The `_get_threshold()` function in `embeddings.py` has handling for `"bge-quora-finetuned"` (dead code path)
- The `is_finetuned_model_available()` function in `embeddings.py:384` checks for this model
- The `list_available_finetuned_models()` function in `embeddings.py:399` can return this non-existent model name

**Impact:** Dead code paths in 5+ locations. The phantom model appears in the "fine-tuned models" backend list but is never displayed to the user. If somehow triggered, it would produce a `FileNotFoundError`.

**Fix:** Remove all references to `BGE-quora-finetuned` across the codebase. Remove the `finetuned_bge_dir` from `paths.yaml` and `AppPaths`.

---

## 6. High: Wrong Model Version in Config

**Severity: HIGH**
**File:** `configs/evaluation.yaml:10`
**Line:** `- "BGE-base-v1.5"`

This references a non-existent model. The correct model name is `"BGE-base-en-v1.5"`. The version number `v1.5` vs `en-v1.5` is wrong.

**Impact:** Any evaluation code referencing `baseline_models` from this config will fail to find the model. This affects the evaluation pipeline when run from config-driven mode.

---

## 7. High: Phantom Directory Paths in Config

**Severity: HIGH**
**File:** `configs/paths.yaml`

Several model directories in `paths.yaml` and the fallback `_legacy_get_app_paths` point to paths that do not exist on disk:

| Config key | Path | Exists on disk? |
|-----------|------|-----------------|
| `bge_model_dir` | `models/bge_base_en_v1_5` | No |
| `e5_model_dir` | `models/e5_base_v2` | No |
| `mpnet_model_dir` | `models/mpnet_base_v2` | No |
| `deberta_model_dir` | `models/deberta_v3_cross_encoder` | No |
| `finetuned_bge_dir` | `models/bge-quora-finetuned` | No |

These are the "downloaded copy" directories — the actual models live in the HuggingFace cache. The directories exist in the YAML but are never created on disk.

**Impact:** The `ModelRegistryEntry` for each of these models checks `paths.bge_model_dir.exists()` etc., which returns `False`. This causes the `local_path` field to be `None`. The UI displays "N/A" for the local path, which is confusing.

**Fix:** Either create these directories as symlinks to the HF cache, or remove the local path checks for HF-sourced models and rely solely on the cache path.

---

## 8. Medium: Dead Code in Configs

**Severity: MEDIUM**
**Files:** `configs/models.yaml:146`, `configs/paths.yaml:31-32`

1. `models.yaml:146` — Hub name entry `MiniLM: "sentence-transformers/all-MiniLM-L12-v2"` refers to a model not in the active model list. This is unused dead code.

2. `paths.yaml:31-32` — The cache path overrides `hf_cache_dir` and `st_cache_dir` are set to `null` and never used. They add confusion: "can I override cache dirs?" The answer is technically yes, but the code path is not tested.

**Fix:** Remove `MiniLM` hub entry. Remove or document the null cache dir overrides.

---

## 9. Medium: Redundant Re-exports in `__init__.py`

**Severity: MEDIUM**
**Files:** `src/duplicate_question_app/__init__.py`

The package `__init__.py` re-exports many symbols from both the canonical `_`-prefixed modules and the legacy stubs. This creates a confusing API surface where the same function can be imported from three different paths.

**Impact:** Developers can import the same function as:
- `from duplicate_question_app import predict_pair`
- `from duplicate_question_app._entry import predict_pair`
- `from duplicate_question_app.cli import predict_pair` (stub)

**Fix:** Simplify `__init__.py` to only export the public API from canonical locations. Remove re-exports from stubs.

---

## 10. Medium: Implicit Dependency on `app/` Package

**Severity: MEDIUM**
**File:** `_models/embeddings.py:21`

```python
from app.services.cache import get_cache
```

This imports from the Streamlit-facing `app/` package into the core `src/` package, creating a reverse dependency. The core library should not depend on the Streamlit application layer.

**Impact:**
- Cannot use core library without `app/` package installed
- Circular dependency risk
- Breaks separation of concerns

**Fix:** Move `CacheManager` into `_inference/` and have `app/services/cache.py` import from there instead.

---

## 11. Medium: Unused CLI Commands

**Severity: MEDIUM**
**File:** `pyproject.toml:99-101`

Three CLI commands registered in `pyproject.toml` are prefixed with underscore, indicating they're internal:

```toml
dqd-doctor = "duplicate_question_app.cli:_run_doctor"
dqd-health = "duplicate_question_app.cli:_run_health"
dqd-validate = "duplicate_question_app.cli:_run_validate"
dqd-config = "duplicate_question_app.cli:_run_config"
```

These are registered as public user-facing commands (no underscore in the command name) but point to private functions. Either make them public or remove the entry points.

---

## 12. Medium: Circular Import Risk in `settings.py`

**Severity: MEDIUM**
**File:** `_config/settings.py:414`

```python
_reload_module_constants()
```

This function is called at module import time. It iterates all config keys and reloads constants. If any config key triggers an import that eventually imports `settings.py`, a circular import occurs.

Currently working because the config YAML loading is pure data, but the risk exists.

**Fix:** Defer `_reload_module_constants()` to lazy initialization or make it idempotent with a guard.

---

## 13. Medium: Inconsistent Naming Conventions

**Severity: MEDIUM**

Multiple naming inconsistencies across the codebase:

| Location | Name | Issue |
|----------|------|-------|
| `configs/paths.yaml:20` | `bge_model_dir: models/bge_base_en_v1_5` | Uses underscores for BGE, but hyphens for e5 and mpnet |
| `_legacy_get_app_paths` | Same paths | Same inconsistency |
| `models.yaml:42` | `display_name: "BGE-base-en-v1.5"` | Version `v1.5` but HF hub has `v1.5` |
| Multiple | `all_mpnet_base_v2_lr_head.pkl` | MPNet with `_` separators mixing conventions |

**Fix:** Standardize on kebab-case for directory names matching display names.

---

## 14. Low: Lint/Type Warnings

**Severity: LOW**
**File:** `_models/embeddings.py:24`

```python
_cache_manager = get_cache()
_sentence_transformer_cache: dict[str, Any] = _cache_manager.sentence_transformer_cache
```

`_cache_manager` has type `Any` (or `CacheManager` from `app.services.cache`), and accessing `.sentence_transformer_cache` has a `type: ignore[attr-defined]` comment. This is a type safety gap.

**Fix:** Properly type the `CacheManager` class and remove the `type: ignore`.

---

## 15. Low: Hardcoded Path Fallbacks

**Severity: LOW**
**File:** `_config/settings.py:120-142`

The `_legacy_get_app_paths()` function contains hardcoded paths that duplicate information in `configs/paths.yaml`. This creates two sources of truth.

**Fix:** Remove `_legacy_get_app_paths` and have `get_app_paths()` raise if config is not available.

---

## 16. Low: Stale URL References

**Severity: LOW**
**File:** `pyproject.toml:63-67`

The project URLs reference `your-org` placeholder:

```toml
Homepage = "https://github.com/your-org/duplicate-question-detection"
Repository = "https://github.com/your-org/duplicate-question-detection"
```

**Fix:** Update to actual repository URL.

---

## 17. Low: Missing Dependencies in `pyproject.toml`

**Severity: LOW**

The `dev` dependencies include `ruff` twice (lines 74-75) and are missing `toml` (needed for reading `pyproject.toml`), `huggingface_hub` (used in `_get_hf_cache_path`), and potentially `streamlit` for the `app/` package.

---

## Summary

| Severity | Count | Key Issues |
|----------|-------|------------|
| CRITICAL | 1 | Path resolution bug in 7 files breaks most local model loading |
| HIGH | 6 | 29 stubs, duplicate cache, 14 orphaned pages, phantom BGE model, wrong config refs, phantom dirs |
| MEDIUM | 5 | Dead config code, redundant re-exports, reverse dependency, unused CLI, circular import risk, naming |
| LOW | 3 | Type warnings, hardcoded fallbacks, stale URLs |
| **Total** | **16** | |

**Priority order for fixes:**
1. Path resolution bug (7 files) — directly breaks functionality
2. Remove 29 stubs and update imports — biggest maintenance burden
3. Merge cache implementations — memory efficiency + correctness
4. Remove 14 orphaned pages — UI clarity
5. Fix config errors (phantom model, wrong version, phantom dirs)
6. Fix `app/` → `src/` reverse dependency
