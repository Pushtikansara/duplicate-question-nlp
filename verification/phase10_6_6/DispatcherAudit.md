# Dispatcher Audit — Phase 10.6.6

## InferenceDispatcher Implementation

**File:** `src/ares/inference/dispatcher.py`

### Architecture
- `InferenceDispatcher.predict()` is the SINGLE prediction engine
- Routes by `model_type` from registry entry
- `_BACKEND_MAP` dictionary maps `model_type` → backend class
- No if/else chains - pure dictionary dispatch

### Backend Registration
```python
_BACKEND_MAP: dict[str, type[InferenceBackend]] = {
    "transformer": TransformerBackend,
    "cross-encoder": CrossEncoderBackend,
    "bi-encoder": EmbeddingBackend,
    "classical-ml": ClassicalBackend,
}
```

### Backend Interface
All backends implement `InferenceBackend.predict(model_name, question1, question2, threshold)` → `BackendResult`

### BackendResult Fields
- `predicted_label` - int (0 or 1)
- `prediction` - str ("Duplicate" or "Non-Duplicate")
- `confidence` - float (0.0 to 1.0)
- `prob_duplicate` - float
- `prob_non_duplicate` - float
- `model_name` - str
- `backend` - str (backend class name)
- `artifact_path` - str (model location)
- `tokenizer` - str (tokenizer type)
- `inference_function` - str (function used)
- `execution_time_ms` - float
- `raw_logits` - list[float]
- `softmax` - list[float]
- `predicted_class_id` - int
- `label_mapping` - dict[int, str]
- `final_label` - str
- `threshold` - float

### Removed Duplicate Logic
Files that previously contained prediction logic now delegate to `InferenceDispatcher.predict()`:
- `app/utils/constants.py` → `get_model_prediction()` delegates to dispatcher
- `app/utils/constants.py` → `run_batch_prediction()` delegates to dispatcher
- `app/services/runtime.py` → simplified, no model loading logic

### Unified Call Paths
| Entry Point | Calls |
|---|---|
| Prediction Page | `get_model_prediction()` → `InferenceDispatcher.predict()` |
| ARES Dashboard | `ARES.predict()` → `InferenceDispatcher.predict()` |
| REST API | `_run_prediction()` → `ARES.predict()` → `InferenceDispatcher.predict()` |
| gRPC Service | `AresGrpcService.predict()` → `ARES.predict()` → `InferenceDispatcher.predict()` |
| CLI | `predict()` → `ARES.predict()` → `InferenceDispatcher.predict()` |
| Batch CSV | `run_batch_prediction()` → `InferenceDispatcher.predict()` |
