# Inference Architecture — Phase 10.6.6

## Architecture Overview

```
User/Client
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    UI / API / CLI Layer                  │
│  (Prediction Page, ARES Dashboard, REST, gRPC, CLI)     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    ARES (Orchestration)                  │
│   Thin orchestration layer. NEVER owns prediction.      │
│   Adds reflection, semantic validation.                 │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              PredictAgent / MultiAgentEngine             │
│   Agent-layer coordination. Delegates inference.        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                InferenceDispatcher                       │
│   THE SINGLE PREDICTION ENGINE. Routes by model_type.   │
└──┬──────────┬──────────┬──────────┬─────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│Trans-  │ │Cross-  │ │Embed-  │ │Classical │
│former  │ │Encoder │ │ding    │ │Backend   │
│Backend │ │Backend │ │Backend │ │          │
└───┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘
    │          │          │           │
    ▼          ▼          ▼           ▼
┌─────────────────────────────────────────────────────────┐
│                    Model Artifacts                       │
│  (Local dirs, HuggingFace cache, joblib files)          │
└─────────────────────────────────────────────────────────┘
```

## ONE Prediction Engine

**InferenceDispatcher.predict()** is the single entry point for ALL predictions:
- Prediction Page → `get_model_prediction()` → `InferenceDispatcher.predict()`
- ARES Dashboard → `ARES.predict()` → `InferenceDispatcher.predict()`
- REST API → `_run_prediction()` → `ARES.predict()` → `InferenceDispatcher.predict()`
- gRPC → `AresGrpcService.predict()` → `ARES.predict()` → `InferenceDispatcher.predict()`
- CLI → `predict()` → `ARES.predict()` → `InferenceDispatcher.predict()`
- Batch CSV → `run_batch_prediction()` → `InferenceDispatcher.predict()`

## Backend Routing

The dispatcher routes by `model_type` from the registry:
- `transformer` → `TransformerBackend` (DistilBERT Week 3/4)
- `cross-encoder` → `CrossEncoderBackend` (DeBERTa, Cross-Encoder-Quora)
- `bi-encoder` → `EmbeddingBackend` (BGE, E5, MPNet)
- `classical-ml` → `ClassicalBackend` (TF-IDF + LR/SVM)

No if/else chains inside ARES. No fallback. No default.

## Execution Proof

Every prediction returns:
- `selected_model` — what the user chose
- `executed_model` — what actually ran
- `backend` — which backend class
- `artifact_path` — where the model loaded from
- `tokenizer` — which tokenizer was used
- `inference_function` — the function called
- `execution_time_ms` — inference time
- `raw_logits` — raw model output
- `softmax` — normalized probabilities
- `predicted_class_id` — argmax index
- `label_mapping` — class ID to label
- `final_label` — human-readable prediction
- `threshold` — decision threshold used

## Verification

Selected model always equals executed model.
No hidden Week4 fallback.
Every prediction is explainable from raw logits to final decision.
