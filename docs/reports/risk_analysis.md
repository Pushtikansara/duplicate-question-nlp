# Risk Analysis — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Risk Matrix

| ID | Risk | Probability | Impact | Score | Category |
|----|------|------------|--------|-------|----------|
| R-01 | Circular dependency breaks import order | Medium | High | 8 | Architecture |
| R-02 | Missing dependencies on fresh install | High | Medium | 6 | Build |
| R-03 | Path resolution fails in deployed context | Medium | High | 8 | Deployment |
| R-04 | Config typos cause silent misbehavior | Medium | High | 8 | Configuration |
| R-05 | Singleton cache state leaks between requests | Low | Medium | 4 | Performance |
| R-06 | No auth leads to unauthorized access | High | Medium | 6 | Security |
| R-07 | Unbounded input causes OOM | Medium | High | 8 | Security |
| R-08 | Experiment results not reproducible | Medium | High | 8 | Research |
| R-09 | Model artifacts version mismatch | Medium | Medium | 6 | Operations |
| R-10 | Streamlit community cloud limits reached | Low | Medium | 3 | Deployment |
| R-11 | No monitoring — failures undetected | Medium | High | 8 | Operations |
| R-12 | nltk data not downloaded | High | Low | 3 | Build |

---

## 2. Detailed Risk Analysis

### R-01: Circular Dependency Import Order

**Description:** `_models/embeddings.py` and `_ensemble/v1.py` import from each other. Depending on import order at module load time, this could cause `ImportError` or `AttributeError`.

**Probability:** Medium — Python handles circular imports at module level reasonably well, but function-level imports can fail if the module isn't fully initialized.

**Impact:** High — app crashes at startup or on first prediction.

**Current mitigation:** The circular dependency is resolved at function-call time (imports inside functions), so it works. But it's fragile.

**Recommended action:** Break circular dependency (see Refactoring Plan R-01).

---

### R-02: Missing Dependencies

**Description:** `pyproject.toml` does not list `nltk` or `huggingface_hub`, both of which are imported at runtime.

**Probability:** High — any fresh install will be missing these.

**Impact:** Medium — `nltk` failure breaks `_linguistics/lexical.py` (lexical penalty engine). `huggingface_hub` failure breaks `_models/registry.py` HF cache scanning.

**Current mitigation:** ImportError is caught in some places (e.g., `_get_hf_cache_path` has `try/except ImportError`).

**Recommended action:** Add both dependencies to `pyproject.toml`.

---

### R-03: Path Resolution Failure

**Description:** `Path(__file__).resolve().parents[2]` lands on `src/` instead of project root when package is installed (e.g., `pip install -e .`).

**Probability:** Medium — depends on installation method.

**Impact:** High — all 7 affected files compute wrong project root, causing model loading failures.

**Current mitigation:** The correct `parents[3]` is used in `_config/settings.py`. 7 other files were fixed in Phase 2.5.

**Verification:** Confirm no remaining `parents[2]` in codebase.

---

### R-04: Config Typos

**Description:** YAML configs have no schema validation. Typos like `BGE-base-v1.5` (instead of `BGE-base-en-v1.5`) go undetected.

**Probability:** Medium — human error in editing YAML.

**Impact:** High — wrong model name causes silent fallback or wrong metric evaluation.

**Current mitigation:** None.

**Recommended action:** Add config schema validation (see Refactoring Plan R-05).

---

### R-05: Singleton State Leakage

**Description:** Global `CacheManager` singleton persists across requests. In multi-user Streamlit deployment, cached data from one user may be visible to another (if cache contains user-specific data).

**Probability:** Low — currently cache is model/embedding only, not user data.

**Impact:** Medium — if user-specific data is cached in the future.

**Current mitigation:** Cache only contains model instances and embeddings, not user data.

**Recommended action:** Add per-user cache partitioning when user-specific data is introduced.

---

### R-06: No Authentication

**Description:** Streamlit app has no authentication. Anyone with the URL can access it.

**Probability:** High — if deployed publicly.

**Impact:** Medium — duplicate detection is low-sensitivity data, but model inference costs money.

**Current mitigation:** None.

**Recommended action:** Add Streamlit authentication or deploy behind VPN.

---

### R-07: Unbounded Input

**Description:** Text inputs have no length validation. A user could paste an entire book, causing OOM during tokenization/encoding.

**Probability:** Medium — accidental or malicious.

**Impact:** High — Streamlit app crashes, model serving disrupted.

**Current mitigation:** None (preprocessing normalizes but doesn't truncate).

**Recommended action:** Add max input length validation at the entry point.

---

### R-08: Experiment Reproducibility

**Description:** No experiment tracking, no deterministic training mode, no data versioning.

**Probability:** Medium — training scripts set random seeds but GPU nondeterminism is not controlled.

**Impact:** High — cannot confidently reproduce published results.

**Current mitigation:** Random seeds set in config.

**Recommended action:** Add experiment tracking (see Refactoring Plan R-06).

---

### R-09: Model Version Mismatch

**Description:** No model versioning. If a model is retrained, old predictions cannot be mapped to the specific model version used.

**Probability:** Medium — after any retraining.

**Impact:** Medium — evaluation results become ambiguous.

**Current mitigation:** Config has `version_key` field but it's not used for artifact identification.

**Recommended action:** Add model versioning with hash-based artifact identification.

---

## 3. Risk Heat Map

```
High Impact │  R-01  R-03  R-04     R-07  R-08  R-11
            │  R-02  
 Medium     │  R-05  R-09        R-06  
            │  R-12  
 Low Impact │              R-10
            └──────────────────────────────
              Low      Med       High
                     Probability
```

---

## 4. Risk Response Plan

### Accept (No Action)
- **R-10** (Streamlit limits) — Too speculative; address when scaling is needed
- **R-12** (nltk data) — Low impact; fix when it breaks

### Mitigate (Reduce Probability or Impact)
- **R-01** (Circular dependency) — Break in Sprint 1
- **R-02** (Missing deps) — Add to pyproject.toml
- **R-03** (Path resolution) — Verify all fixed, add test
- **R-04** (Config typos) — Add schema validation
- **R-07** (Unbounded input) — Add input validation

### Transfer (Move Responsibility)
- **R-06** (No auth) — Deploy behind VPN or SSO

### Avoid (Eliminate Cause)
- **R-05** (Singleton leakage) — Add isolation if user data added
- **R-08** (Reproducibility) — Add experiment tracking
- **R-09** (Version mismatch) — Add artifact versioning
- **R-11** (No monitoring) — Add health checks
