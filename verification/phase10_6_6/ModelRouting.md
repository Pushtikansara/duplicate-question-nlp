# Model Routing — Phase 10.6.6

## Sidebar to Prediction Flow

```
Sidebar Dropdown
    │  User selects model
    ▼
Streamlit Session State
    │  st.session_state["selected_model"]
    ▼
Prediction Page / ARES Dashboard
    │  Uses selected_model as model_name
    ▼
ARES.with_model(model_name)
    │  Validates via InferenceDispatcher.validate_model()
    ▼
InferenceDispatcher.predict(model_name, q1, q2)
    │  Looks up model in registry
    │  Gets entry.model_type
    ▼
Backend Resolution
    │  model_type → Backend class
    │  "transformer" → TransformerBackend
    │  "cross-encoder" → CrossEncoderBackend
    │  "bi-encoder" → EmbeddingBackend
    │  "classical-ml" → ClassicalBackend
    ▼
Backend.predict(model_name, q1, q2)
    │  Loads model artifacts
    │  Runs inference
    ▼
BackendResult → PredictionResult
    │  Full execution proof included
    ▼
Returned to caller
```

## Routing Rules

1. **Selected model is always executed.** No fallback, no default, no Week4 override.
2. **Backend is determined by `model_type`** from the registry entry, not by hardcoded checks.
3. **Each backend is a separate class** implementing `InferenceBackend` interface.
4. **Adding a new model type** requires only adding a new backend class and registry entry.

## Verified Routing Table

| Model Name | Registry model_type | Backend Class |
|---|---|---|
| TF-IDF + Logistic Regression (Week 2) | classical-ml | ClassicalBackend |
| TF-IDF + Linear SVM (Week 2) | classical-ml | ClassicalBackend |
| DistilBERT (Week 3) | transformer | TransformerBackend |
| Improved DistilBERT (Week 4) | transformer | TransformerBackend |
| BGE-base-en-v1.5 | bi-encoder | EmbeddingBackend |
| E5-base-v2 | bi-encoder | EmbeddingBackend |
| E5-quora-finetuned | bi-encoder | EmbeddingBackend |
| MPNet-base-v2 | bi-encoder | EmbeddingBackend |
| DeBERTa-v3 Cross-Encoder | cross-encoder | CrossEncoderBackend |
| Cross-Encoder-Quora (Trained) | cross-encoder | CrossEncoderBackend |
| Semantic Ensemble | ensemble | (via ensemble path) |

## No Hardcoded Fallbacks

All hardcoded references to "Week 4 Improved DistilBERT" have been removed:
- `src/ares/_config.py`: Removed `DEFAULT_MODEL`
- `src/ares/grpc/streaming.py`: Removed default model string
- `src/ares/api/config.py`: Removed default model string
- `src/ares/grpc/services.py`: Changed to use empty string default
- `app/services/runtime.py`: Changed to use empty string default
- `app/pages/prediction.py`: Changed to use session state only
