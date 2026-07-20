# Dependency Graph — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Complete Dependency Map

### 1.1 Import Graph (Internal Dependencies)

```
src/duplicate_question_app/
│
├── __init__.py
│   ├── _artifacts
│   └── _config.settings
│   └── _inference.transformer
│   └── _models.week2
│
├── cli.py
│   ├── _config.settings
│   ├── _models.week2
│   └── _inference.transformer
│
├── _config/
│   ├── __init__.py
│   ├── loader.py          [pyyaml, os, pathlib]
│   ├── settings.py         [loader, hashlib, os, pathlib]
│   ├── exceptions.py       [none]
│   ├── logging_setup.py    [logging, loader]
│   ├── preprocessing.py    [loader]
│   └── model_config.py     [loader]
│
├── _artifacts/
│   ├── __init__.py         [loader]
│   └── loader.py           [pandas, _config]
│
├── _preprocessing/
│   ├── __init__.py         [text]
│   └── text.py             [re, unicodedata, html, typing]
│
├── _inference/
│   ├── __init__.py
│   ├── transformer.py      [torch, transformers, _config, _preprocessing]
│   ├── cache.py            [hashlib, threading, collections, numpy]
│   └── optimizer.py        [hashlib, threading, numpy, _inference.cache, _preprocessing, sentence_transformers]
│
├── _models/
│   ├── __init__.py
│   ├── embeddings.py       [numpy, torch, _config, _preprocessing, _inference.cache, _ensemble.v1?] (circular)
│   ├── registry.py         [_config, _models.week2]
│   └── week2.py            [joblib, _config, _preprocessing]
│
├── _ensemble/
│   ├── __init__.py
│   ├── v1.py               [_config, _linguistics, _models, _preprocessing]
│   ├── v2.py               [_config, _linguistics, _models, _preprocessing, _inference.cache]
│   └── agreement.py        [_config, _models, _linguistics, _preprocessing]
│
├── _linguistics/
│   ├── __init__.py
│   ├── negation.py         [re, _config]
│   ├── contradiction.py    [re, _config]
│   ├── entity.py           [re, _config]
│   ├── intent.py           [re, _config]
│   └── lexical.py          [nltk, re, _config]
│
├── _evaluation/
│   ├── __init__.py
│   ├── metrics.py          [numpy, sklearn, scipy, matplotlib, _config]
│   ├── error_analysis.py   [numpy, _config]
│   └── hard_mining.py      [numpy, sklearn, _config, _dataset, _models, _preprocessing]
│
├── _dataset/
│   ├── __init__.py
│   └── loader.py           [pandas, numpy, sklearn, _config]
│
├── _explainability/
│   ├── __init__.py
│   ├── trace.py            [_config, _ensemble, _linguistics, _preprocessing]
│   ├── text.py             [_config, _explainability.trace, _ensemble, _linguistics]
│   └── agreement_dashboard.py [_config, _ensemble, _linguistics, _preprocessing]
│
├── _calibration/
│   ├── __init__.py
│   ├── v1.py               [numpy, _config]
│   └── v2.py               [numpy, scipy, sklearn, _config]
│
├── _training/
│   ├── __init__.py
│   └── classifier_head.py  [torch, joblib, numpy, _config, _preprocessing, _dataset]
│
├── _visualization/
│   ├── __init__.py
│   └── plots.py            [matplotlib, seaborn, sklearn, numpy]
│
├── _testing/
│   ├── __init__.py
│   └── hard_test_generator.py [_preprocessing]
│
├── _logging/
│   ├── __init__.py
│   └── error_logger.py     [logging, csv, json, threading]
│
├── _validation/
│   └── validation_types.py [_config]
│
└── utils/
    ├── metrics.py          [numpy]
    └── device.py           [torch]
```

### 1.2 Circular Dependencies

**Identified circular dependency chain:**

```
_models/embeddings.py
    → imports from _ensemble/v1.py (get_adaptive_ensemble_prediction)

_ensemble/v1.py
    → imports from _models/embeddings.py (predict_with_sentence_transformer)

_ensemble/agreement.py
    → imports from _models/embeddings.py (...)
    → imports from _models/week2.py (...)
```

**Resolution:** The circular dependency exists because `embeddings.py` provides the ensemble entry point `get_ensemble_prediction()` which delegates to `_ensemble/v1.py`. Meanwhile, `_ensemble/v1.py` and `_ensemble/agreement.py` import prediction functions from `_models/embeddings.py`. This is a **design smell** — the ensemble module should depend on models, not the other way around.

### 1.3 External Dependencies

```
Core Dependencies (pyproject.toml):
  pandas>=2.0.0
  numpy>=1.24.0
  matplotlib>=3.7.0
  seaborn>=0.13.0
  scipy>=1.10.0
  scikit-learn>=1.3.0
  pyarrow>=14.0.0
  streamlit>=1.36.0
  torch>=2.0.0
  transformers>=4.30.0
  safetensors>=0.4.0
  sentence-transformers>=3.0.0
  accelerate>=1.1.0
  joblib>=1.3.0
  pyyaml>=6.0

Additional (not in pyproject.toml, used by tools):
  nltk                (_linguistics/lexical.py)
  python-docx         (tools/generate_book.py)
  huggingface_hub     (_models/registry.py)
  tqdm                (tools/ training scripts)
```

---

## 2. Dependency Analysis

### 2.1 Fan-in / Fan-out

| Module | Fan-in (depended on by) | Fan-out (depends on) |
|--------|------------------------|----------------------|
| `_config` | 15 modules | 1 (pyyaml) |
| `_preprocessing` | 8 modules | 0 (stdlib only) |
| `_models` | 7 modules | 2 (config, preprocessing) |
| `_inference` | 3 modules | 2 (config, preprocessing) |
| `_linguistics` | 5 modules | 1 (config) |
| `_ensemble` | 3 modules | 4 (config, models, linguistics, preprocessing) |
| `_evaluation` | 0 | 4 (config, dataset, models, preprocessing) |
| `_dataset` | 2 modules | 1 (config) |
| `_explainability` | 0 | 5 (config, ensemble, linguistics, preprocessing) |
| `_calibration` | 1 module | 1 (config) |
| `_visualization` | 2 modules | 0 (external only) |
| `_logging` | 0 | 0 (external only) |
| `_testing` | 0 | 1 (preprocessing) |
| `_training` | 0 | 3 (config, preprocessing, dataset) |
| `_validation` | 0 | 1 (config) |

### 2.2 High-Risk Dependencies

1. **`_config`** is a "god module" — every other module depends on it. Changes to config interfaces affect the entire system.
2. **`_models/embeddings.py`** has both high fan-in (many dependents) and cross-module dependencies (ensemble, cache), making it a refactoring risk.
3. **`_ensemble`** has high coupling — depends on models, linguistics, config, and preprocessing. Touches most of the system.

---

## 3. Version Conflicts

| Package | Requirement | Actual (likely) | Risk |
|---------|------------|-----------------|------|
| torch | >=2.0.0 | 2.x | Low |
| transformers | >=4.30.0 | 4.x | Low |
| sentence-transformers | >=3.0.0 | 3.x | Medium — API breaking changes possible |
| streamlit | >=1.36.0 | 1.x | Low |
| numpy | >=1.24.0 | 1.x | Low |
