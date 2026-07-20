# Future Architecture — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Vision

The target architecture for ARES (Adaptive Reasoning Engine for Semantic Understanding) is a **research-grade AI cognitive architecture** with:

- **Plugin-based model system** — Add models without touching existing code
- **Pipeline-based inference** — Chain models, linguistic engines, and post-processors
- **Event-driven architecture** — Reactive components that respond to inference events
- **Experiment framework** — Track, compare, and reproduce every experiment
- **Distributed inference** — Scale model serving horizontally
- **Research dashboard** — Visualize experiments, metrics, and model comparisons

---

## 2. Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARES Core Platform                           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Public API (stable)                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │ Python   │ │  CLI     │ │  REST    │ │  Streamlit   │   │   │
│  │  │ Library  │ │  (8 cmd) │ │  (FastAPI)│ │  (App Layer) │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Plugin Registry                           │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │Model     │ │Linguistic│ │Ensemble  │ │Calibration   │   │   │
│  │  │Plugins   │ │Plugins   │ │Plugins   │ │Plugins       │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                Inference Pipeline Engine                     │   │
│  │                                                              │   │
│  │  Input → Preprocess → Route → Predict → Calibrate → Output   │   │
│  │                                                              │   │
│  │  Pipeline configurable via YAML:                             │   │
│  │    pipeline:                                                  │   │
│  │      - normalize                                              │   │
│  │      - linguistic_analysis                                    │   │
│  │      - model_selection (dynamic)                              │   │
│  │      - ensemble_weighted                                      │   │
│  │      - calibrate                                              │   │
│  │      - threshold                                              │   │
│  │      - explain                                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                Experiment Framework                          │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │Tracker   │ │Config    │ │Metrics   │ │Report        │   │   │
│  │  │(MLflow)  │ │Snapshots │ │Database  │ │Generator     │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Infrastructure Layer                      │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
│  │  │Docker    │ │Redis     │ │Postgres  │ │Object Store  │   │   │
│  │  │Container │ │Cache     │ │(Metrics) │ │(Artifacts)   │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Migration Path

### Phase 0 (Current) → Phase 1

```
Current:                              Phase 1 Target:
┌──────────────────┐                  ┌──────────────────┐
│  Streamlit App   │                  │  Streamlit App   │
│  (monolithic)    │                  │  (thin client)   │
└────────┬─────────┘                  └────────┬─────────┘
         │ import                             │ HTTP/gRPC
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│  Core Library    │                  │  REST API        │
│  (sync, blocking)│                  │  (FastAPI)       │
└────────┬─────────┘                  └────────┬─────────┘
         │                                     │ import
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│  Models (disk)   │                  │  Core Library    │
└──────────────────┘                  │  (async-ready)   │
                                       └────────┬─────────┘
                                                │
                                                ▼
                                       ┌──────────────────┐
                                       │  Models (disk/HF)│
                                       └──────────────────┘
```

### Phase 1 → Phase 2

```
Phase 1 Target:                       Phase 2 Target:
┌──────────────────┐                  ┌──────────────────┐
│  Streamlit App   │                  │  Streamlit App   │
│  (thin client)   │                  │  (research dash) │
└────────┬─────────┘                  └────────┬─────────┘
         │ HTTP/gRPC                           │ HTTP/gRPC
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│  REST API        │                  │  API Gateway     │
│  (FastAPI)       │                  │  (auth, routing) │
└────────┬─────────┘                  └────────┬─────────┘
         │ import                     ┌─────────┼─────────┐
         ▼                            ▼         ▼         ▼
┌──────────────────┐          ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Core Library    │          │ Model    │ │Linguistic│ │Experiment│
│  (plugin-based)  │          │ Workers  │ │Workers   │ │Database  │
└────────┬─────────┘          │ (GPU)    │ │(CPU)     │ │(Postgres)│
         │                    └──────────┘ └──────────┘ └──────────┘
         ▼
┌──────────────────┐
│  Distributed     │
│  Cache (Redis)   │
└──────────────────┘
```

---

## 4. Key Architectural Changes

### 4.1 Plugin System (Phase 1)

**Current:** Adding a model requires editing 8+ files across the codebase.

**Future:** Models are discovered automatically via plugin registration:

```python
# _models/plugins/bge.py
@register_model
class BGEModel(BaseModel):
    name = "BGE-base-en-v1.5"
    model_type = "bi-encoder"
    ...
```

### 4.2 Pipeline Engine (Phase 1)

**Current:** Inference logic is scattered across multiple files with hardcoded dispatch.

**Future:** Pipelines are configured in YAML:

```yaml
pipeline:
  - step: normalize
  - step: linguistic_analysis
    engines: [negation, entity, intent, contradiction, lexical]
  - step: select_model
    strategy: auto
  - step: predict
  - step: calibrate
  - step: threshold
  - step: explain
    level: detailed
```

### 4.3 Experiment Framework (Phase 2)

**Current:** No experiment tracking. Results in notebook cells and DOCX files.

**Future:** Every experiment is tracked:

```python
with experiment("cross-encoder-quora-v2", config={
    "learning_rate": 2e-5,
    "batch_size": 32,
    "epochs": 5,
}):
    model = train(...)
    metrics = evaluate(model)
    experiment.log_metrics(metrics)
    experiment.log_artifact("models/cross-encoder-quora-v2/")
```

### 4.4 Distributed Inference (Phase 3)

**Current:** All inference is single-process, single-machine.

**Future:** Models can be distributed across machines:

```
Client → Load Balancer → Model Worker (GPU: DeBERTa)
                       → Model Worker (CPU: TF-IDF)
                       → Linguistic Worker (CPU)
                       → Ensemble Aggregator
```

---

## 5. Technology Stack Recommendations

| Component | Current | Target | Rationale |
|-----------|---------|--------|-----------|
| API | None (Streamlit only) | FastAPI | Async, auto-docs, production-ready |
| Model serving | In-process | TorchServe / BentoML | GPU sharing, auto-scaling |
| Cache | In-memory LRU | Redis | Distributed, persistent, shared |
| Experiment tracking | None | MLflow | Industry standard, self-hosted |
| Metrics DB | None | PostgreSQL + TimescaleDB | Structured metric storage |
| Containerization | None | Docker + Docker Compose | Reproducible environments |
| Orchestration | None | Docker Compose → K8s | Scale when needed |
| Config validation | None | Pydantic / msgspec | Type-safe config loading |

---

## 6. Migration Risks

| Risk | Phase | Mitigation |
|------|-------|-----------|
| REST API breaks Streamlit integration | 1 | Keep Streamlit as one client; add API alongside |
| Plugin system too complex | 1 | Start with simple decorator-based registry, not full plugin loader |
| Async conversion breaks sync code | 1 | Use `asyncio.run()` bridge; convert gradually |
| Over-engineering before need | All | Only add patterns justified by current requirements |
| Experiment tracking adds friction | 2 | Make tracking optional (no-op tracker by default) |
