# Technical Debt Report — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Executive Summary

The repository has accumulated technical debt through several phases of development without dedicated consolidation periods. The recent Phase 2.5 cleanup addressed some high-profile issues (29 stubs removed, 12 orphaned pages removed, cache consolidated), but structural debt remains in the form of circular dependencies, god modules, and missing infrastructure.

**Estimated effort to resolve all debt:** 4-6 weeks (single developer)

**Debt categories:**
- **Critical:** 2 items
- **High:** 5 items
- **Medium:** 8 items
- **Low:** 10 items

---

## 2. Complete Debt Inventory

### 2.1 Critical Debt

| ID | Debt Item | Location | Impact | Effort |
|----|-----------|----------|--------|--------|
| C-01 | Circular dependency: `_models` ↔ `_ensemble` | `_models/embeddings.py` ↔ `_ensemble/v1.py` | Breaks clean architecture; prevents independent module testing | 2 days |
| C-02 | Reverse dependency: `_models` imports from `app/` | `_models/embeddings.py` → `app/services/cache.py` | Core library cannot be used without UI layer | 1 day (partially fixed) |

### 2.2 High Debt

| ID | Debt Item | Location | Impact | Effort |
|----|-----------|----------|--------|--------|
| H-01 | God module: `_config` depended by all | `_config/` | Any change to config interface cascades everywhere | 3 days |
| H-02 | God module: `_models/embeddings.py` too large | 410 lines, 10+ functions | Hard to test, hard to extend, multiple responsibilities | 2 days |
| H-03 | Duplicate argument parsing in tools/ | All 12 tools/ scripts | Each script has its own argparse; adding a new model requires updating 12 parsers | 2 days |
| H-04 | No model evaluation summary | None | Cannot compare all 11 models on same metrics | 3 days |
| H-05 | Singleton cache manager | `_inference/cache.py` | Hard to mock for testing; global state | 1 day |

### 2.3 Medium Debt

| ID | Debt Item | Location | Impact | Effort |
|----|-----------|----------|--------|--------|
| M-01 | Missing type hints in some functions | Various | Type checker cannot validate all code paths | 2 days |
| M-02 | Inconsistent docstring style | Various | Documentation tools cannot auto-generate API docs | 1 day |
| M-03 | Hardcoded model names in multiple places | `embeddings.py`, `_get_sigmoid_params`, etc. | Adding a model requires updating many functions | 2 days |
| M-04 | Missing nltk in pyproject.toml | `_linguistics/lexical.py` | Dependency not declared; breaks on fresh install | 1 hour |
| M-05 | Missing huggingface_hub in pyproject.toml | `_models/registry.py` | Same | 1 hour |
| M-06 | No async/await for I/O operations | All inference | Blocking calls waste resources | 3 days |
| M-07 | Config keys not validated against schema | `_config/loader.py` | Typos in YAML silently default to wrong values | 2 days |
| M-08 | No cache invalidation mechanism | `_inference/cache.py` | Caches grow unbounded; stale model data | 1 day |

### 2.4 Low Debt

| ID | Debt Item | Location | Impact | Effort |
|----|-----------|----------|--------|--------|
| L-01 | Stale README | `README.md` | Misleading for new developers | 4 hours |
| L-02 | Missing Dockerfile | Root | Cannot containerize | 4 hours |
| L-03 | No experiment tracking | All | Cannot reproduce results | 3 days |
| L-04 | Inconsistent naming: `bge_model_dir: bge_base_en_v1_5` | `paths.yaml` | Underscores vs hyphens inconsistency | 1 hour |
| L-05 | `ruff` listed twice in dev dependencies | `pyproject.toml:74-75` | No functional impact but unprofessional | 1 min |
| L-06 | Placeholder URLs in pyproject.toml | `pyproject.toml:63-67` | References `your-org` | 1 min |
| L-07 | `build/` directory not in .gitignore | Root | Build artifacts could be committed | 1 min |
| L-08 | No `.dockerignore` | Root | Docker builds would include .venv, etc. | 1 hour |
| L-09 | No data versioning | `data/` | Cannot track which dataset version was used | 2 days |
| L-10 | No model versioning | `models/` | Cannot track which training run produced a model | 2 days |

---

## 3. Debt by Module

### 3.1 Source Library (src/) — Total: 12 items

| Module | Items | Severity | Priority |
|--------|-------|----------|----------|
| `_config` | H-01 (god module), M-07 (no validation) | High | High |
| `_models/embeddings.py` | C-01 (circular), H-02 (god func), M-03 (hardcoded) | Critical | High |
| `_inference/cache.py` | H-05 (singleton), M-08 (no invalidation) | High | Med |
| `_ensemble` | C-01 (circular) | Critical | High |
| `_linguistics/lexical.py` | M-04 (missing dep) | Medium | Med |

### 3.2 Application (app/) — Total: 3 items

| Module | Items | Severity | Priority |
|--------|-------|----------|----------|
| `services/` | C-02 (reverse dep — partially fixed) | High | High |
| `pages/` | M-06 (no async) | Medium | Low |

### 3.3 Tools — Total: 4 items

| Module | Items | Severity | Priority |
|--------|-------|----------|----------|
| All scripts | H-03 (duplicate argparse) | High | High |
| All scripts | L-03 (no experiment tracking) | Low | Med |

### 3.4 Tests — Total: 2 items

| Module | Items | Severity | Priority |
|--------|-------|----------|----------|
| All | No model comparison test | Low | Low |

---

## 4. Debt Trend

Based on the repository evolution visible in the codebase:

```
Week 1-2:  Low debt (simple scripts, notebooks)
    │
Week 3-4:  Medium debt (adding features without refactoring)
    │
Week 5:    High debt (streamlit app rushed)
    │
Phase 2:   Very high debt (11 models, 5 engines, ensemble — rapid expansion)
    │
Phase 2.5: Medium debt (recent cleanup: stubs, pages, cache)
    │
Now:       Medium-high debt (structural issues remain)
```

---

## 5. Debt Resolution Priority Matrix

```
                    High Impact │ Low Impact
                 ───────────────┼─────────────
     Easy │      H-03, M-04    │  L-01, L-05, L-06
          │      M-05, L-01    │  L-07
          │                    │
  Medium  │      C-01, C-02    │  M-01, M-02
          │      H-02, H-04    │  L-04
          │                    │
   Hard   │      H-01          │  L-03, L-09, L-10
          │      M-06, M-07    │
```

**Recommended order:**
1. C-01 (circular dependency) — Easy-Medium, High Impact
2. C-02 (reverse dependency) — Easy, High Impact
3. M-04, M-05 (missing deps) — Easy, Medium Impact
4. H-03 (duplicate argparse) — Medium, High Impact
5. H-02 (god module split) — Medium, High Impact
6. H-04 (evaluation summary) — Medium, High Impact
7. H-05 (singleton → DI) — Medium, Medium Impact
8. M-07 (config validation) — Medium, Medium Impact
