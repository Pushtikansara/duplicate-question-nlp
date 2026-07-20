# Module Interaction Graph — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Module Interaction Matrix

### 1.1 Call Graph (which module calls which)

```
 Caller \ Callee    │ cfg│ pre│ mod│ inf│ ens│ lin│ eva│ dat│ exp│ cal│ vis│ trn│ tst│ log│ val│ cli
────────────────────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────
 _config            │ ██ │    │    │    │    │    │    │    │    │    │    │    │    │    │    │
 _preprocessing     │  █ │ ██ │    │    │    │    │    │    │    │    │    │    │    │    │    │
 _models            │  █ │  █ │ ██ │  █ │    │    │    │    │    │    │    │    │    │    │    │
 _inference         │  █ │  █ │    │ ██ │    │    │    │    │    │    │    │    │    │    │    │
 _ensemble          │  █ │  █ │  █ │    │ ██ │  █ │    │    │    │    │    │    │    │    │    │
 _linguistics       │  █ │    │    │    │    │ ██ │    │    │    │    │    │    │    │    │    │
 _evaluation        │  █ │  █ │  █ │    │    │    │ ██ │  █ │    │    │    │    │    │    │    │
 _dataset           │  █ │    │    │    │    │    │    │ ██ │    │    │    │    │    │    │    │
 _explainability    │  █ │  █ │    │    │  █ │  █ │    │    │ ██ │    │    │    │    │    │    │
 _calibration       │  █ │    │    │    │    │    │    │    │    │ ██ │    │    │    │    │    │
 _visualization     │    │    │    │    │    │    │    │    │    │    │ ██ │    │    │    │    │
 _training          │  █ │  █ │    │    │    │    │    │  █ │    │    │    │ ██ │    │    │    │
 _testing           │    │  █ │    │    │    │    │    │    │    │    │    │    │ ██ │    │    │
 _logging           │    │    │    │    │    │    │    │    │    │    │    │    │    │ ██ │    │
 _validation        │  █ │    │    │    │    │    │    │    │    │    │    │    │    │    │ ██ │
 cli.py             │  █ │    │  █ │  █ │    │    │    │    │    │    │    │    │    │    │    │ ██
 app/ (pages)       │  █ │    │  █ │    │    │    │    │    │    │    │    │    │    │    │    │
 app/ (services)    │  █ │    │  █ │    │    │    │    │    │    │    │    │    │    │    │    │
────────────────────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────
```

---

## 2. Module Cohesion Analysis

### 2.1 High Cohesion Modules (Good)

| Module | Cohesion Level | Rationale |
|--------|---------------|-----------|
| `_linguistics` | High | All files detect specific linguistic phenomena; clear single purpose |
| `_calibration` | High | Both files calibrate probabilities; no unrelated functionality |
| `_preprocessing` | High | Single file with single responsibility (text normalization) |
| `_dataset` | High | Single file handling data loading only |
| `_logging` | High | Single purpose (error logging) |
| `_visualization` | High | All files generate plots |
| `_testing` | High | Single file for test generation |

### 2.2 Medium Cohesion Modules

| Module | Cohesion Level | Rationale |
|--------|---------------|-----------|
| `_ensemble` | Medium | Contains ensemble prediction (v1, v2) AND agreement analysis — related but distinct concerns |
| `_evaluation` | Medium | Contains metrics, error analysis, AND hard mining — related but could be split |
| `_explainability` | Medium | Contains decision traces, text generation, AND agreement dashboard — related but distinct |

### 2.3 Low Cohesion Modules (Needs Improvement)

| Module | Cohesion Level | Rationale |
|--------|---------------|-----------|
| `_config` | Low | Contains settings, path resolution, model config, exceptions, logging setup — all configuration-related but diverse |
| `_inference` | Low | Contains transformer inference, general caching, AND performance optimization — three distinct concerns in one package |
| `_models` | Low | Contains embedding inference, model registry, week2 inference — all model-related but functionally separate |

---

## 3. Coupling Analysis

### 3.1 Tightly Coupled Pairs

| Pair | Coupling | Reason |
|------|----------|--------|
| `_models` ↔ `_ensemble` | Tight | Circular dependency; ensemble calls models, models call ensemble entry point |
| `_explainability` ↔ `_ensemble` | Tight | Explainability calls ensemble for votes and weights |
| `_explainability` ↔ `_linguistics` | Tight | Explainability calls all 5 linguistic engines |
| `_evaluation` ↔ `_models` | Tight | Evaluation calls model inference functions directly |
| `_training` ↔ `_dataset` | Tight | Training uses dataset loader for train/val splits |

### 3.2 Loosely Coupled Pairs (Good)

| Pair | Coupling | Reason |
|------|----------|--------|
| `_calibration` ↔ Rest | Loose | Only depends on config and numpy/scipy |
| `_visualization` ↔ Rest | Loose | Independent module, no internal dependencies |
| `_logging` ↔ Rest | Loose | Independent module |
| `_testing` ↔ Rest | Loose | Only depends on preprocessing |

---

## 4. Interface Analysis

### 4.1 Public Interfaces (defined in `__init__.py`)

**`src/duplicate_question_app/__init__.py` exports:**
- Model discovery: `MODEL_CHOICES`, `AppPaths`, `ModelDirectoryStatus`, `ModelMetrics`, `ModelResolution`
- Inference: `DuplicateQuestionInferenceService`, `load_model_and_tokenizer`
- Model selection: `resolve_model_selection`, `resolve_preferred_model_dir`
- Path resolution: `get_app_paths`
- Utilities: `inspect_model_dir`, `is_new_embedding_model`, `is_transformer_model`
- Analysis: `available_week4_plots`, `build_dataset_summary`, `build_transformer_metrics`, `build_week4_metrics`
- Loaders: `load_confusion_matrix_csv`, `load_dataset_frame`, `load_transformer_predictions`, etc.
- Week 2: `Week2InferenceService`, `check_week2_artifacts`, `is_week2_model`

### 4.2 Missing Interfaces

1. **No `Predictor` base class/ABC** — Each model type has a different call signature
2. **No `LinguisticAnalyzer` base class** — 5 engines with different outputs but no shared interface
3. **No `Evaluator` base class** — Evaluation functions scattered across modules
4. **No `Trainer` base class** — Training scripts are standalone, not reusable components

---

## 5. State Management

### 5.1 Global State (Singletons)

| State | Location | Type | Thread-Safe |
|-------|----------|------|-------------|
| Config cache | `_config/loader.py` | Module-level dict | Yes (read-only after load) |
| Cache manager | `_inference/cache.py` | Global `_cache_manager` | Yes (RLock) |
| ST model cache | `_models/embeddings.py` | Module-level dict | No (dict operations not atomic) |
| Logger | `_config/logging_setup.py` | Module-level | Yes (logging is thread-safe) |

### 5.2 State Management Concerns

1. `_cache_manager` is a singleton — hard to mock for testing
2. `_sentence_transformer_cache` in `embeddings.py` is unprotected (no lock)
3. No cache invalidation strategy (caches grow unboundedly)
4. No mechanism to reload config at runtime
