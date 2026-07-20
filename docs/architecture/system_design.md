# System Design Document — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20
**Status:** Draft — Architecture Audit Phase

---

## 1. System Overview

ARES (Adaptive Reasoning Engine for Semantic Understanding) is a research-grade NLP system for duplicate question detection. It is designed as a **layered architecture** with clear separation between:

- **Core Library** (`src/duplicate_question_app/`) — ML models, inference, evaluation, linguistic analysis
- **Application Layer** (`app/`) — Streamlit web UI
- **Configuration Layer** (`configs/`) — YAML-driven settings with environment overrides
- **Tooling Layer** (`tools/`) — Training scripts, evaluation runners, utilities
- **Test Layer** (`tests/`) — Unit, integration, regression, and smoke tests

---

## 2. Architecture Principles

| Principle | Description |
|-----------|-------------|
| **Separation of Concerns** | Each subpackage has a single, well-defined responsibility |
| **Configuration over Code** | All tunable parameters in YAML, not hardcoded |
| **Fail Fast** | Validate inputs early; raise specific exceptions |
| **Lazy Loading** | Load models and data on demand, not at import time |
| **Singleton Caching** | Centralized cache manager for models, embeddings, preprocessing |
| **Defensive Programming** | Graceful fallbacks at every level (model → model → error) |

---

## 3. System Architecture

### 3.1 Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Presentation Layer                    │
│                    app/ (Streamlit)                       │
│  _entry.py  │  pages/ (14)  │  components/ (4)          │
│  services/ (4)  │  utils/ (1)                            │
└──────────────────────┬───────────────────────────────────┘
                       │ import
                       ▼
┌──────────────────────────────────────────────────────────┐
│                     Core Library Layer                    │
│              src/duplicate_question_app/                  │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │
│  │ _config/   │  │ _models/   │  │ _inference/      │   │
│  │ settings   │  │ embeddings │  │ transformer      │   │
│  │ loader     │  │ registry   │  │ cache            │   │
│  │ exceptions │  │ week2      │  │ optimizer        │   │
│  └─────┬──────┘  └─────┬──────┘  └───────┬──────────┘   │
│        │               │                  │              │
│  ┌─────┴──────┐  ┌─────┴──────┐  ┌───────┴──────────┐   │
│  │_linguistic │  │_ensemble   │  │ _evaluation      │   │
│  │ negation   │  │ v1         │  │ metrics          │   │
│  │ contradict │  │ v2         │  │ error_analysis   │   │
│  │ entity     │  │ agreement  │  │ hard_mining      │   │
│  │ intent     │  │            │  │                  │   │
│  │ lexical    │  │            │  │                  │   │
│  └────────────┘  └────────────┘  └──────────────────┘   │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │
│  │_dataset/   │  │_training/  │  │ _calibration/    │   │
│  │ loader     │  │ classifier │  │ v1, v2           │   │
│  └────────────┘  └────────────┘  └──────────────────┘   │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │
│  │_explainab. │  │_visualiz.  │  │ cli.py, __init__ │   │
│  │ trace      │  │ plots      │  │ (public API)     │   │
│  │ text       │  │            │  │                  │   │
│  │ agreement  │  │            │  │                  │   │
│  └────────────┘  └────────────┘  └──────────────────┘   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                     Data Layer                           │
│  models/ (trained artifacts)                             │
│  data/ (Quora dataset)                                   │
│  outputs/ (evaluation results)                           │
│  HuggingFace Hub (pre-trained models)                    │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Component Dependency Graph

```
_config/          ← imports by EVERY other component
  │
  ├── _models/    ← imports _config (paths, model metadata)
  │   │              imports _preprocessing (normalize_question)
  │   │              imports _inference.cache (cache manager)
  │   │
  │   ├── _ensemble/  ← imports _config, _models, _linguistics
  │   │
  │   ├── _evaluation/ ← imports _config, _dataset, _models
  │   │
  │   ├── _explainability/ ← imports _config, _ensemble, _linguistics, _preprocessing
  │   │
  │   └── _inference/ ← imports _config, _preprocessing, _models (circular)
  │
  ├── _linguistics/   ← imports _config (self-contained)
  │
  ├── _dataset/       ← imports _config (data paths)
  │
  ├── _calibration/   ← external deps only (numpy, scipy)
  │
  ├── _training/      ← imports _config, _preprocessing, _dataset
  │
  ├── _visualization/ ← external deps only (matplotlib, seaborn)
  │
  └── _logging/       ← external deps only (logging, csv)
```

---

## 4. Key Architectural Decisions

### ADR-1: Config-Driven Design
**Decision:** All tunable parameters stored in YAML files under `configs/`.
**Rationale:** Decouples configuration from code; enables environment-specific overrides via `DQD_` prefix.
**Trade-off:** Adds YAML parsing overhead at startup; requires documentation of all config keys.

### ADR-2: `_`-Prefixed Subpackages
**Decision:** Internal implementation modules prefixed with underscore.
**Rationale:** Python convention for private modules; clearly separates public API (`__init__.py`, `cli.py`) from internals.
**Trade-off:** Longer import paths; requires `__init__.py` re-exports for public surface.

### ADR-3: Model Registry Pattern
**Decision:** Central `build_registry()` function enumerates all models with metadata.
**Rationale:** Single source of truth for model discovery; clean separation of model metadata from inference logic.
**Trade-off:** Registry must be manually kept in sync with config.

### ADR-4: Singleton Cache Manager
**Decision:** Global singleton `CacheManager` accessed via `get_cache()`.
**Rationale:** Ensures model reuse across requests; thread-safe for concurrent access.
**Trade-off:** Singletons hinder testing (global state); complicates cache invalidation.

### ADR-5: Lazy Model Loading
**Decision:** Models loaded on first inference request, not at import time.
**Rationale:** Reduces startup time; allows graceful handling of missing models.
**Trade-off:** First request for each model is slow (cold start).

---

## 5. Module Boundaries

| Module | Responsibility | External Dependencies | Internal Dependencies |
|--------|---------------|----------------------|----------------------|
| `_config` | Configuration loading, env overrides, path resolution | pyyaml, os, pathlib | None |
| `_models` | Model inference (all 11 models), registry | torch, transformers, sentence-transformers, joblib | `_config`, `_preprocessing`, `_inference.cache` |
| `_inference` | Inference orchestration, caching, optimization | torch, transformers, numpy | `_config`, `_preprocessing` |
| `_linguistics` | Linguistic analysis (5 engines) | nltk, re | `_config` |
| `_ensemble` | Ensemble prediction, model agreement | numpy | `_config`, `_models`, `_linguistics`, `_preprocessing` |
| `_evaluation` | Metrics, error analysis, hard mining | numpy, sklearn, scipy, matplotlib | `_config`, `_dataset`, `_models` |
| `_dataset` | Data loading, splitting | pandas, numpy | `_config` |
| `_explainability` | Decision traces, text explanations, agreement dashboard | numpy | `_config`, `_ensemble`, `_linguistics`, `_preprocessing` |
| `_calibration` | Probability calibration | numpy, scipy, sklearn | `_config` |
| `_training` | Classifier head training | torch, joblib, numpy | `_config`, `_preprocessing`, `_dataset` |
| `_visualization` | Plot generation | matplotlib, seaborn, sklearn | None |
| `_testing` | Hard test generation | None | `_preprocessing` |
| `_logging` | Error logging | logging, csv, json | None |
| `_validation` | Input validation | None | `_config` |

---

## 6. Design Patterns Used

| Pattern | Location | Purpose |
|---------|----------|---------|
| Singleton | `_inference/cache.py`, `_config/loader.py` | Global cache and config access |
| Factory | `services/runtime.py` | Model service creation based on type |
| Registry | `_models/registry.py` | Model metadata enumeration |
| Strategy | `_ensemble/v1.py`, `_ensemble/v2.py` | Interchangeable ensemble algorithms |
| Adapter | `_inference/transformer.py` | Wraps HuggingFace models in uniform interface |
| Facade | `cli.py` | Unified CLI for all operations |
| Data Transfer Object | Various `*Result` dataclasses | Type-safe data transfer between layers |
| Template Method | `_preprocessing/text.py` | Consistent normalization pipeline |
| Lazy Initialization | Model loading throughout | Defer expensive operations |

---

## 7. Error Handling Strategy

```
Exception Hierarchy:
  DuplicateQuestionAppError (base)
  ├── ConfigurationError
  ├── ModelNotFoundError
  ├── ModelNotReadyError
  ├── DatasetNotFoundError
  ├── InferenceError
  ├── PreprocessingError
  ├── EnsembleError
  ├── EvaluationError
  ├── CalibrationError
  ├── RegistryError
  ├── DataError
  ├── TrainingError
  └── LinguistError
```

**Error handling principles:**
1. Specific exceptions for specific failure modes
2. Graceful fallback chains (model → model → error message)
3. User-facing errors caught in `_safe_render()` wrapper
4. Internal errors logged with stack traces
5. Validation at module boundaries (`_validation/`)

---

## 8. Performance Characteristics

| Operation | Typical Latency | Caching | Notes |
|-----------|----------------|---------|-------|
| Config loading | <100ms | Yes (memoized) | Once at startup |
| Model loading | 1-10s | Yes (LRU) | Per model, first request |
| Week 2 inference | <10ms | No | TF-IDF + LR/SVM |
| Transformer inference | ~500ms | No | DistilBERT on CPU |
| Bi-encoder inference | ~200ms | Yes (embeddings) | BGE, E5, MPNet |
| Cross-encoder inference | ~400ms | No | DeBERTa-v3 |
| Ensemble inference | ~2-5s | Partial | Loads ALL models |
| Normalization | <5ms | Yes (LRU) | Abbreviation + typo fix |
| Linguistic analysis | <50ms | Partial | 5 engines |

---

## 9. Security Architecture

**Current state:** Minimal security measures.

**Existing:**
- Input normalization (prevents injection via text)
- Exception handling (prevents traceback leaks)
- Config env overrides (not file-based secrets)

**Missing:**
- No authentication
- No rate limiting
- No input size validation
- No secrets management

---

## 10. Deployment Architecture

**Current:** Streamlit single-process application.

**Entry points:**
1. `streamlit run app/_entry.py` — Web UI
2. `dqd-app` — CLI shortcut (via pyproject.toml)
3. `dqd-predict` — Headless prediction
4. `dqd-benchmark` — Performance benchmarking
5. Other CLI commands (doctor, health, validate, config)

**Missing:**
- Dockerfile
- Docker Compose
- CI/CD pipeline
- Health checks
- Monitoring
- Horizontal scaling
