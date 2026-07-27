# Phase 10.6.5 — Model Routing Audit

## Routing Logic

```
st.session_state["selected_model"] (from sidebar)
  ↓
get_inference_service() in app/services/runtime.py:86
  ├── is_week2_model()          → Week2InferenceService
  ├── is_ensemble_model()        → get_ensemble_prediction()
  ├── is_new_embedding_model()   → predict_with_sentence_transformer()
  └── (else) transformer         → DuplicateQuestionInferenceService
```

## Sidebar Model Selection

Verified in `app/components/sidebar.py:82-140`:
- User selects model from dropdown
- `_on_model_change()` callback sets `st.session_state["selected_model"]`
- Model cache is cleared, forcing fresh load
- `get_inference_service()` reads `st.session_state["selected_model"]`

## Model-to-Backend Mapping

| Display Name | Backend | Route Function |
|---|---|---|
| TF-IDF + Logistic Regression (Week 2) | joblib | `Week2InferenceService.predict_single()` |
| TF-IDF + Linear SVM (Week 2) | joblib | `Week2InferenceService.predict_single()` |
| DistilBERT (Week 3) | transformers | `DuplicateQuestionInferenceService.predict_single()` |
| Improved DistilBERT (Week 4) | transformers | `DuplicateQuestionInferenceService.predict_single()` |
| BGE-base-en-v1.5 | sentence-transformers | `predict_with_sentence_transformer()` |
| E5-base-v2 | sentence-transformers | `predict_with_sentence_transformer()` |
| E5-quora-finetuned | sentence-transformers | `predict_with_sentence_transformer()` |
| MPNet-base-v2 | sentence-transformers | `predict_with_sentence_transformer()` |
| DeBERTa-v3 Cross-Encoder | sentence-transformers | `predict_with_sentence_transformer()` |
| Cross-Encoder-Quora (Trained) | sentence-transformers | `predict_with_sentence_transformer()` |
| Semantic Ensemble | ensemble | `get_ensemble_prediction()` |

## Audit Findings

### Finding 1: Silent fallback removed
**Status: FIXED**

Previously, `get_inference_service()` had a nested try/except that would silently
fall back from the selected model to the default. This meant the user could select
"Cross-Encoder-Quora (Trained)" but get "DistilBERT (Week 4)" results if the
cross-encoder failed to load.

The fix in `runtime.py:137-151` now raises a clear error instead.

### Finding 2: Model selection is correctly passed
**Status: PASS**

`get_model_prediction()` receives `selected_model` as a parameter and routes to
the correct backend. No hidden defaults override the selection.

### Finding 3: E5 model auto-upgrade
**Status: NOTED**

`resolve_best_available_e5_model()` in `embeddings.py:50` auto-upgrades E5-base-v2
to E5-quora-finetuned if the fine-tuned model exists. This improves accuracy
but means the exact model name in the UI may differ from the model actually
executed. The result dict correctly reports the actual model used.

### Finding 4: All backends are mutually exclusive
**Status: PASS**

The routing checks are ordered: week2 → ensemble → embedding → transformer.
Each model name matches exactly one backend. No overlap exists in the sets.
