# Phase 10.6.5 — Complete Inference Trace

## Trace: "what is ai" vs "what is artificial intelligence"
## Model: Cross-Encoder-Quora (Trained)

### Step 1: User Input
```
Q1: "what is ai"
Q2: "what is artificial intelligence"
```

### Step 2: UI (prediction.py:69)
```python
result = get_model_prediction(service, "Cross-Encoder-Quora (Trained)", q1, q2)
```

### Step 3: Model Routing (constants.py:93-100)
```python
is_week2_model("Cross-Encoder-Quora (Trained)") → False
is_ensemble_model("Cross-Encoder-Quora (Trained)") → False
is_new_embedding_model("Cross-Encoder-Quora (Trained)") → True  (CROSS_ENCODER_MODELS)
→ Routes to predict_with_sentence_transformer()
```

### Step 4: Text Normalization (embeddings.py:218-219)
```python
q1_norm = normalize_question("what is ai", expand_abbrevs=True, fix_typos=True)
→ "what is ai (artificial intelligence)"

q2_norm = normalize_question("what is artificial intelligence", expand_abbrevs=True, fix_typos=True)
→ "what is artificial intelligence"
```

Note: After normalization, q1_norm contains both "ai" and "artificial intelligence",
while q2_norm contains only "artificial intelligence". These are NOT identical
strings, so the identical-text shortcut does not trigger.

### Step 5: Model Loading (embeddings.py:75-122)
```python
get_sentence_transformer_model("Cross-Encoder-Quora (Trained)")
→ CrossEncoder(model_key=paths.finetuned_cross_encoder_dir, device="cpu")
```

### Step 6: Model Inference (embeddings.py:225)
```python
model.predict([(q1_norm, q2_norm)], apply_softmax=True)[0]
```
Cross-Encoder has num_labels=2 (fine-tuned on binary Quora data).
Output: [p_not_dup, p_dup] e.g., [0.05, 0.95]

### Step 7: Probability Extraction (embeddings.py:233)
```python
prob_duplicate = float(scores[1])  # index 1 = duplicate class
→ ~0.95
```

### Step 8: Threshold Application (embeddings.py:254)
```python
threshold = _get_threshold("Cross-Encoder-Quora (Trained)")
→ 0.10 (from configs/inference.yaml:per_model_thresholds)

pred_label = int(0.95 >= 0.10) → 1 (Duplicate)
```

### Step 9: Base Result (embeddings.py:257-259)
```python
_result_dict:
  predicted_label: 1
  prediction: "Duplicate"
  prob_duplicate: ~0.95
  prob_non_duplicate: ~0.05
  confidence: 0.95
  threshold: 0.10
  model_label: "Cross-Encoder-Quora (Trained)"
```

### Step 10: Semantic Assessment (constants.py:112)
```python
semantic_pipeline.assess("what is ai", "what is artificial intelligence")
→ SemanticAssessment with:
  semantic_similarity: ~0.85
  concept_overlap: {overlap_score: ~0.67, shared_concepts: ["ai", "artificial intelligence"], ...}
  intent_similarity: {score: ~0.9}
  conflicts: []
  confidence: ~0.85
```

### Step 11: Decision Fusion (constants.py:118-128)
```python
fusion = DecisionFusion(strategy=FusionStrategy.FUSION)
fusion_result = fusion.fuse(cross_encoder_score=0.95, semantic_assessment=assessment_dict)
→ {
    final_score: ~0.90,
    final_prediction: "Duplicate",
    strategy: "fusion",
    cross_encoder_score: 0.95,
    semantic_score: ~0.85,
    fusion_score: ~0.90,
    ...
  }
```

### Step 12: Final Result (constants.py:136-140)
```python
{
  "prediction": "Duplicate",
  "final_prediction": "Duplicate",
  "fusion_score": ~0.90,
  "prob_duplicate": ~0.95,
  "confidence": 0.95,
  "model_label": "Cross-Encoder-Quora (Trained)",
  "prediction_overridden": False,
}
```

## Developer Debug Exposure

The prediction page now exposes:
- ✓ Selected model name
- ✓ Actual model executed  
- ✓ Backend type (transformer / sentence-transformer / joblib)
- ✓ Raw probability (prob_duplicate)
- ✓ Threshold used
- ✓ Label mapping
- ✓ Fusion component scores
- ✓ Prediction override status
- ✓ Conflict detection
