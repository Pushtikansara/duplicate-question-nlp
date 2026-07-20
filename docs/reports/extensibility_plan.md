# Extensibility Plan — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Extensibility Score: 7.5/10

**Interpretation:** The codebase is **well-designed for extension**. The modular architecture, config-driven design, and consistent patterns make it relatively easy to add new models, linguistic engines, or UI pages.

---

## 2. Extension Points

### 2.1 Adding a New Model

**Current effort required:** 6-8 steps across multiple files.

**Step-by-step:**

1. **Train the model** → `tools/` (new script or existing)
2. **Add inference code** → `_models/` (new file or extend existing)
3. **Add config entry** → `configs/models.yaml` (model metadata)
4. **Add to registry** → `_models/registry.py` (build_registry entry)
5. **Add to inference config** → `configs/inference.yaml` (threshold, sigmoid params)
6. **Add to ensemble** → `_ensemble/` (if ensemble participant)
7. **Add to agreement** → `_ensemble/agreement.py` (collect_all_votes)
8. **Add to explainability** → `_explainability/` (if visible in explanations)

**Common mistakes when adding a model:**
- Forgetting to update `registry.py`
- Forgetting to update `collect_all_votes()` in `agreement.py`
- Forgetting per-model calibration params in `inference.yaml`
- Hardcoding model name in string-matching logic

**Recommendation:** Create a **model addition checklist** (see Section 5).

---

### 2.2 Adding a New Linguistic Engine

**Current effort:** 4-5 steps.

**Step-by-step:**

1. **Create engine file** → `_linguistics/<engine_name>.py`
2. **Register in `__init__.py`** → Add import
3. **Integrate with ensemble** → `_ensemble/v2.py` (add feature)
4. **Integrate with explainability** → `_explainability/trace.py` (include in trace)
5. **Create UI page** → `app/pages/<engine_name>.py`

**Pattern to follow:**
- Each engine returns a dataclass with structured results
- Engine has a single public function (`detect_X()`, `compute_X()`)
- Engine is self-contained (dependencies minimal)

---

### 2.3 Adding a New UI Page

**Current effort:** 3-4 steps.

**Step-by-step:**

1. **Create page file** → `app/pages/<page_name>.py` with `def render():`
2. **Register in `__init__.py`** → Add import
3. **Add to route map** → `app/_entry.py` (add entry)
4. **Add to sidebar** → `app/components/sidebar.py` (add navigation item)

**Pattern to follow:**
- Page has single `render()` function
- Page imports from `src/` library, not from `app/` services
- Page handles its own error states
- Page uses consistent CSS via `inject_styles()`

---

### 2.4 Adding a New Ensemble Strategy

**Current effort:** 2-3 steps.

**Step-by-step:**

1. **Create ensemble file** → `_ensemble/v3.py`
2. **Register in config** → `configs/models.yaml` (add to model list)
3. **Add to dispatch** → `services/runtime.py` (or `_models/embeddings.py`)

**Pattern to follow:**
- Ensemble takes (q1, q2, paths) → returns result dict
- Ensemble can access all models via `_models` and all linguistic engines via `_linguistics`
- Ensemble returns same result dict format as individual models

---

### 2.5 Adding a New Calibration Method

**Current effort:** 1-2 steps.

**Step-by-step:**

1. **Create calibration file** → `_calibration/v3.py`
2. **Register in config** → `configs/inference.yaml`

**Pattern to follow:**
- Calibration function takes (scores, model_name) → calibrated scores
- Calibration parameters from config (per-model or global)

---

## 3. Extension Readiness by Module

| Module | Readiness | Why |
|--------|-----------|-----|
| `_config` | 8/10 | Adding config keys is trivial; adding new config files easy |
| `_models` | 7/10 | Adding model requires updating multiple files; no abstract base class |
| `_inference` | 7/10 | Adding new inference type (e.g., API-based) needs new file |
| `_linguistics` | 9/10 | Adding new engine is straightforward; clear pattern |
| `_ensemble` | 6/10 | Two versions create confusion about which to extend; no abstract base |
| `_evaluation` | 7/10 | Adding new metric is easy; adding new evaluation type needs new file |
| `_explainability` | 6/10 | Tightly coupled to ensemble and linguistics; adding new explanation type is harder |
| `_calibration` | 9/10 | Adding new method is straightforward |
| `_visualization` | 8/10 | Adding new plot type is easy |
| `app/pages` | 8/10 | Adding page is straightforward; consistent pattern |
| `app/services` | 7/10 | Adding new service is easy; but some services too coupled to Streamlit |

---

## 4. Abstraction Layer Recommendations

To improve extensibility scores to 9+, add abstract base classes:

### 4.1 Abstract Model Base

```python
class BaseModel(ABC):
    @abstractmethod
    def predict(self, q1: str, q2: str) -> dict[str, Any]: ...

    @abstractmethod
    def predict_batch(self, pairs: list[tuple[str, str]]) -> list[dict[str, Any]]: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def model_type(self) -> str: ...
```

### 4.2 Abstract Linguistic Engine Base

```python
class BaseLinguisticEngine(ABC):
    @abstractmethod
    def analyze(self, q1: str, q2: str) -> dict[str, Any]: ...

    @property
    @abstractmethod
    def engine_name(self) -> str: ...
```

### 4.3 Abstract Ensemble Base

```python
class BaseEnsemble(ABC):
    @abstractmethod
    def predict(self, q1: str, q2: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_weights(self) -> dict[str, float]: ...
```

---

## 5. Model Addition Checklist

When adding a new model to ARES, verify each checkbox:

```
[ ] 1. Training script exists in tools/
[ ] 2. Inference code exists in _models/<model_name>.py
[ ] 3. Config entry in configs/models.yaml (models: list)
[ ] 4. Config entry in configs/models.yaml (model_choices)
[ ] 5. Config entry in configs/models.yaml (model_version_short)
[ ] 6. Config entry in configs/models.yaml (backends: section)
[ ] 7. Config entry in configs/inference.yaml (per_model_thresholds)
[ ] 8. Config entry in configs/inference.yaml (sigmoid_params)
[ ] 9. Registry entry in _models/registry.py (build_registry)
[ ] 10. Dispatch logic in services/runtime.py (or embeddings.py type checks)
[ ] 11. Agreement voting in _ensemble/agreement.py (collect_all_votes)
[ ] 12. Ensemble participation in _ensemble/v1.py or v2.py
[ ] 13. Explainability visibility in _explainability/text.py (if needed)
[ ] 14. Model selector in app/components/sidebar.py (if user-facing)
[ ] 15. Smoke test in verify_all_models.py (test entry)
[ ] 16. Documentation in docs/ (model card)
```
