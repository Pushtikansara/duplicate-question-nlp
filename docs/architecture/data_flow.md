# Data Flow Architecture — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Training Data Flow

```
Quora Dataset (CSV/Parquet)
    │ id, qid1, qid2, question1, question2, is_duplicate
    │
    ▼
data/cleaned_quora.parquet  (~404K pairs, 37% duplicate, 63% non-duplicate)
    │
    ▼
_dataset/loader.py :: load_quora_data()
    │
    ├── Read parquet (fast) or CSV (fallback)
    ├── Stratified split by is_duplicate label
    │
    ├── train_df (80% = ~323K pairs)
    │   ├──▶ tools/export_week2_models.py
    │   │       → TF-IDF vectorizer (models/week2_models/)
    │   │       → Logistic Regression (models/week2_models/)
    │   │       → Linear SVM (models/week2_models/)
    │   │
    │   ├──▶ notebooks/transformer_model.ipynb
    │   │       → DistilBERT Week 3 (models/saved_transformer_model/)
    │   │       → Test predictions (outputs/transformer_model/)
    │   │
    │   ├──▶ notebooks/week4_improvement.ipynb
    │   │       → DistilBERT Week 4 (models/week4_improved_model/)
    │   │       → Threshold analysis (outputs/week4_improvement/)
    │   │       → Ablation study (outputs/week4_improvement/)
    │   │
    │   ├──▶ tools/train_e5_quora.py
    │   │       → E5 fine-tuned (models/e5-quora-finetuned/)
    │   │       → MultipleNegativesRankingLoss / CoSENT
    │   │
    │   └──▶ tools/train_cross_encoder.py
    │           → DeBERTa-v3 fine-tuned (models/cross-encoder-quora/)
    │           → Binary classification head
    │
    ├── val_df (10% = ~40K pairs)
    │   └── Used for threshold tuning, early stopping, calibration
    │
    └── test_df (10% = ~40K pairs)
        └── Used for evaluation, benchmarking, error analysis
```

---

## 2. Inference Data Flow (Single Pair)

```
User Input: question1, question2 (raw strings)
    │
    ▼
_preprocessing/text.py :: normalize_question()
    │
    ├── Lowercase
    ├── Unicode NFKC normalization
    ├── HTML entity decode
    ├── URL removal
    ├── Abbreviation expansion
    │   ├── "what's" → "what is"
    │   ├── "don't" → "do not"
    │   ├── "how's" → "how is"
    │   └── 7+ more mappings
    ├── Typo correction
    │   ├── "quora" → "quora" (no change, valid)
    │   └── 15+ specific typo mappings
    └── Whitespace normalization
    │
    ▼
normalized questions (nq1, nq2)
    │
    ▼
Model selection dispatch (services/runtime.py)
    │
    ├── Classical ML (week2_lr, week2_svm)
    │   └── _models/week2.py
    │       ├── Load TF-IDF vectorizer (joblib)
    │       ├── Vectorize: v1 = vec.transform([nq1]), v2 = vec.transform([nq2])
    │       ├── Feature diff: X = |v1 - v2| (element-wise absolute difference)
    │       └── Predict: clf.predict_proba(X) → probability
    │
    ├── Transformer (week3, week4)
    │   └── _inference/transformer.py
    │       ├── Load tokenizer + model
    │       ├── Tokenize: tokenizer(nq1, nq2, padding, truncation)
    │       ├── Forward pass: model(**inputs).logits
    │       └── Softmax: F.softmax(logits) → probability
    │
    ├── Bi-Encoder (bge, e5, mpnet, e5_ft)
    │   └── _models/embeddings.py :: predict_with_sentence_transformer()
    │       ├── Load SentenceTransformer
    │       ├── Apply E5 prefix if needed: "query: ...", "passage: ..."
    │       ├── Encode: emb1 = model.encode(nq1, normalize_embeddings=True)
    │       ├── Encode: emb2 = model.encode(nq2, normalize_embeddings=True)
    │       ├── Cosine: sim = dot(emb1, emb2)
    │       └── Calibrate: sigmoid(steepness * (sim - midpoint))
    │
    ├── Cross-Encoder (deberta, ce_quora)
    │   └── _models/embeddings.py :: predict_with_sentence_transformer()
    │       ├── Load CrossEncoder
    │       ├── Predict: model.predict([(nq1, nq2)], apply_softmax=True)
    │       └── Parse:
    │           ├── 3-class: entail / (contradiction + entail)
    │           └── 2-class: direct probability
    │
    └── Ensemble
        └── _models/embeddings.py :: get_ensemble_prediction()
            └── _ensemble/v1.py :: get_adaptive_ensemble_prediction()
                │
                ├── Run linguistic analysis (all 5 engines)
                ├── Run all sub-models
                ├── Compute dynamic weights
                ├── Weighted average
                └── Trimmed mean outlier removal
    │
    ▼
Post-processing
    ├── Apply threshold (per-model, from config)
    ├── pred_label = 1 if prob >= threshold else 0
    └── Build result dict:
        {
            "question1": nq1,
            "question2": nq2,
            "predicted_label": 0|1,
            "prediction": "Non-Duplicate"|"Duplicate",
            "prob_non_duplicate": float,
            "prob_duplicate": float,
            "confidence": max(prob_non, prob_dup),
            "threshold": float,
            "model_label": str,
            "model_name": str,
            "device": str,
            "latency_ms": float,
            "reason": None|str,
            "feature_breakdown": None|dict
        }
```

---

## 3. Batch Inference Data Flow

```
CSV Upload (via Streamlit file_uploader)
    │
    ▼
app/pages/batch_prediction.py :: render()
    │
    ├── Parse CSV
    ├── Auto-detect question1/question2 columns
    ├── Preview table (first 5 rows)
    ├── User selects model
    │
    ▼
For each row in CSV:
    predict_with_sentence_transformer() / week2 / transformer
        │
        └── Collect results in list
    │
    ▼
Results DataFrame
    ├── Display in Streamlit (st.dataframe)
    └── Download as CSV (st.download_button)
```

---

## 4. Evaluation Data Flow

```
test_df (from loader)
    │
    ▼
For each model:
    │
    ├── Predict all test pairs
    ├── Compare with ground truth
    │
    ▼
_evaluation/metrics.py :: generate_evaluation_report()
    │
    ├── Accuracy, Precision, Recall, F1, MCC
    ├── ROC curve + AUC
    ├── PR curve + AUC
    ├── Confusion matrix
    ├── Calibration curve + ECE + MCE + Brier
    ├── Score distribution
    └── Threshold sweep (F1, Youden's J, MCC)
    │
    ▼
Plots saved (if path provided) or returned as matplotlib figures
```

---

## 5. Explainability Data Flow

```
Input: (q1, q2)
    │
    ▼
_explainability/trace.py :: generate_decision_trace()
    │
    ├── collective_all_votes(q1, q2)
    │   ├── Week2 LR prediction
    │   ├── Week2 SVM prediction  
    │   ├── Week3 DistilBERT prediction
    │   ├── Week4 DistilBERT prediction
    │   ├── BGE prediction
    │   ├── E5 prediction
    │   ├── MPNet prediction
    │   ├── DeBERTa-v3 prediction
    │   └── Cross-Encoder-Quora prediction
    │
    ├── compute_agreement_metrics()
    │   ├── Agreement percentage
    │   ├── Entropy (uncertainty)
    │   ├── Variance (spread)
    │   └── Vote distribution
    │
    ├── run_linguistic_analyses()
    │   ├── Entity mismatch
    │   ├── Negation mismatch
    │   ├── Intent match
    │   ├── Contradiction score
    │   └── Lexical penalty
    │
    └── Build DecisionTrace (17+ fields)
    │
    ▼
_explainability/text.py :: generate_explanation(level)
    │
    ├── Level 1 (Basic): 1-2 sentence summary
    ├── Level 2 (Standard): Paragraph with confidence, agreement, key factors
    ├── Level 3 (Detailed): Multi-paragraph breakdown by model type
    └── Level 4 (Comprehensive): Full report with counterfactuals
```

---

## 6. Cache Data Flow

```
First Request for Model X
    │
    ├── Check _sentence_transformer_cache (dict)
    │   └── Miss → Load model from disk/HF
    │       ├── Store in cache
    │       └── Return model
    │
Subsequent Requests for Model X
    │
    └── Check _sentence_transformer_cache (dict)
        └── Hit → Return cached model
    │
Embedding Cache (LRU, max 10000)
    │
    ├── Check LRU cache by (model_name, text_hash)
    │   ├── Hit → Return cached embedding
    │   └── Miss → Compute embedding → Store in LRU → Return
    │
Preprocessing Cache (LRU, max 5000)
    │
    ├── Check LRU cache by text
    │   ├── Hit → Return cached normalized text
    │   └── Miss → Normalize → Store in LRU → Return
```

---

## 7. Configuration Data Flow

```
Startup
    │
    ▼
_config/loader.py :: load_all_configs()
    │
    ├── Scan configs/ directory
    ├── For each YAML file:
    │   ├── Read file
    │   ├── Walk dict tree
    │   ├── For each leaf value:
    │   │   ├── Check for DQD_<KEY>_<SUBKEY> env var
    │   │   └── Override if present
    │   └── Store in module-level _configs dict
    │
    ▼
Any component calls get_config("models")
    │
    └── Return cached dict for "models" key
    │
    ▼
_config/settings.py :: _reload_module_constants()
    │
    ├── Read model_choices from config
    ├── Read model_version_short from config
    ├── Read backend lists from config
    └── Set module-level constants
```
