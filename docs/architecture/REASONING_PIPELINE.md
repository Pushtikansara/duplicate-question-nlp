# Reasoning Pipeline — ARES

**Version:** 1.0
**Status:** Architecture Specification

---

## Abstract

The ARES reasoning pipeline transforms a raw question pair through six sequential stages — Input, Understanding, Evidence, Reasoning, Decision, Reflection, and Learning — producing a calibrated, explained prediction. Each stage has well-defined inputs, outputs, and interfaces. This document provides a detailed specification of every stage, with concrete references to current implementation modules and future enhancements.

---

## 1. Pipeline Overview

```
  ┌──────┐   ┌──────────┐   ┌────────┐   ┌──────────┐   ┌────────┐   ┌──────────┐
  │INPUT │──▶│UNDERSTAND│──▶│EVIDENCE│──▶│ REASONING│──▶│DECISION│──▶│REFLECTION│
  │  (q1,│   │          │   │        │   │          │   │        │   │          │
  │  q2) │   │ normalized│   │linguistic│ │model    │   │ fused  │   │ calibrate│
  │      │   │ text +   │   │features +│ │predictions│   │decision│   │ + detect │
  │      │   │ features │   │embedding │ │+ votes  │   │        │   │ errors  │
  └──────┘   └──────────┘   └────────┘   └──────────┘   └────────┘   └──────────┘
                                                              │
                                                              ▼
                                                        ┌──────────┐
                                                        │ LEARNING │
                                                        │(log error,│
                                                        │ update wt)│
                                                        └──────────┘
```

---

## 2. Stage 1: Input Processing

### Purpose
Transform raw, unstructured question text into a normalized, machine-readable representation with extracted lexical features.

### Input
- `q1: str` — Raw first question (arbitrary length)
- `q2: str` — Raw second question (arbitrary length)

### Output
- `nq1: str` — Normalized first question
- `nq2: str` — Normalized second question
- `features: dict` — Lexical feature vector (word_overlap, char_overlap, word_count_diff, char_count_diff)

### Current Implementation

```
  _preprocessing/text.py :: normalize_question()
  _explainability/trace.py :: extract_lexical_features()
```

```
  User Input: "What's the difference between AI and ML?"
              "Explain the distinction between AI and ML"
      │
      ▼
  1. Strip whitespace
  2. Unicode NFKC normalization (curly quotes → ASCII)
  3. Strip HTML tags  (<p> → " ")
  4. Replace URLs/emails with placeholders
  5. Remove emoji Unicode blocks
  6. Normalize special chars ("!!!" → "!")
  7. Expand abbreviations:
     "AI" → "AI (Artificial Intelligence)"
     "ML" → "ML (Machine Learning)"
  8. Fix common typos: (none in this example)
  9. Collapse whitespace, lowercase

      │
      ▼
  nq1: "what's the difference between ai (artificial intelligence) and ml (machine learning)"
  nq2: "explain the distinction between ai (artificial intelligence) and ml (machine learning)"

      │
      ▼
  Features: {word_overlap: 0.78, char_overlap: 0.82,
             word_count_diff: 1, char_count_diff: 4}
```

### Data Flow Detail

```
  q1 ──▶ normalize_question() ──▶ nq1 ──▶ extract_lexical_features() ──▶ features
  q2 ──▶ normalize_question() ──▶ nq2 ──┘
         │                                                        │
         ├── expand_abbreviations                                 ├── word_overlap (Jaccard)
         ├── fix_common_typos                                     ├── char_3gram_overlap
         └── LRU cache (key=raw_text)                             ├── word_count_diff
                                                                  └── char_count_diff
```

### Future Implementation

- **Spelling correction via BERT masked LM** — Replace current dictionary-based typo fix with contextual spelling correction
- **Sentence segmentation** — For multi-sentence questions, segment and weight each sentence
- **POS tagging** — Add part-of-speech features for finer-grained lexical analysis
- **Dependency parsing** — Extract subject-verb-object triples as additional features
- **Multi-lingual normalization** — Unicode normalization for CJK, Arabic, Devanagari scripts

---

## 3. Stage 2: Understanding

### Purpose
Apply five specialized linguistic engines to extract structured semantic signals: negation polarity, contradiction score, entity overlap, intent category, and lexical penalty.

### Input
- `nq1: str` — Normalized question 1
- `nq2: str` — Normalized question 2

### Output
- `negation_penalty: float` (0.0–1.0)
- `contradiction_score: float` (0.0–1.0)
- `entity_penalty: float` (0.0–1.0)
- `intent_penalty: float` (0.0–0.5)
- `lexical_penalty: float` (0.0–0.8)

### Current Implementation

```
  _linguistics/negation.py :: get_negation_penalty()
  _linguistics/contradiction.py :: detect_contradiction()
  _linguistics/entity.py :: get_entity_penalty()
  _linguistics/intent.py :: intent_mismatch_penalty()
  _linguistics/lexical.py :: get_lexical_penalty()
```

```
  nq1: "how to install python on ubuntu"
  nq2: "how to uninstall python on linux"
      │
      ▼
  ┌─────────────────┐
  │ NEGATION ENGINE  │
  │                  │
  │ q1: "install"    │  ← no negation
  │ q2: "uninstall"  │  ← prefix negation (un-)
  │                  │
  │ Mismatch: YES    │
  │ Penalty: 0.8     │  ← install↔uninstall detected
  └────────┬─────────┘
           │
  ┌────────▼─────────┐
  │ CONTRADICTION    │
  │ ENGINE           │
  │                  │
  │ install↔uninstall│  ← direct negation pair
  │ Penalty: 0.5     │
  └────────┬─────────┘
           │
  ┌────────▼─────────┐
  │ ENTITY ENGINE    │
  │                  │
  │ q1: python(PL),  │
  │     ubuntu(OS)   │
  │ q2: python(PL),  │
  │     linux(OS)    │
  │                  │
  │ PL overlap: OK   │
  │ OS mismatch: YES │  ← ubuntu vs linux
  │ Penalty: 0.15    │
  └────────┬─────────┘
           │
  ┌────────▼─────────┐
  │ INTENT ENGINE    │
  │                  │
  │ q1: installation │  ← "how to install"
  │ q2: installation │  ← "how to uninstall"
  │                  │
  │ Same intent: YES │
  │ Penalty: 0.0     │
  └────────┬─────────┘
           │
  ┌────────▼─────────┐
  │ LEXICAL ENGINE   │
  │                  │
  │ Overlap: 0.55    │
  │ Languages: py=py  │
  │ OS: ubuntu≠linux │
  │ Penalty: 0.15    │
  └────────┬─────────┘
           │
           ▼
  Penalty vector: [0.8, 0.5, 0.15, 0.0, 0.15]
```

### Future Implementation

- **Contextual negation scope detection** — Use dependency parsing to identify exact negation scope, not just presence
- **NLI-based intent classification** — Replace regex patterns with DeBERTa NLI model for intent
- **Cross-lingual entity resolution** — Map entity variants ("Python 3.12" ≈ "py3.12")
- **Temporal reasoning** — Track time-based contradictions beyond simple before/after

---

## 4. Stage 3: Evidence Collection

### Purpose
Query all available models to produce a comprehensive evidence set of predictions, probabilities, and confidence scores.

### Input
- `nq1: str, nq2: str` — Normalized questions
- `paths: AppPaths` — System path configuration

### Output
- `votes: list[ModelVote]` — One vote per model with {model_name, label, prob, confidence, latency, error}

### Current Implementation

```
  _ensemble/agreement.py :: collect_all_votes()
```

```
  MODEL DISPATCH MATRIX:

  Model              │ Type          │ File                     │ Call
  ───────────────────┼───────────────┼──────────────────────────┼──────────────────
  TF-IDF + LR (W2)   │ classical-ml  │ _models/week2.py         │ predict_proba()
  TF-IDF + SVM (W2)  │ classical-ml  │ _models/week2.py         │ predict_proba()
  DistilBERT (W3)    │ transformer   │ _inference/transformer.py│ predict_proba()
  DistilBERT (W4)    │ transformer   │ _inference/transformer.py│ predict_proba()
  BGE-base-v1.5      │ bi-encoder    │ _models/embeddings.py    │ encode() + cos
  E5-base-v2         │ bi-encoder    │ _models/embeddings.py    │ encode() + cos
  MPNet-base-v2      │ bi-encoder    │ _models/embeddings.py    │ encode() + cos
  DeBERTa-v3 CE      │ cross-encoder │ _models/embeddings.py    │ predict() softmax
  CE-Quora (Trained) │ cross-encoder │ _models/embeddings.py    │ predict() softmax
```

```
  collect_all_votes(q1, q2, paths)
      │
      ├── groups = _get_models_by_group()
      │   → {"week2": [LR, SVM], "transformer": [W3, W4], "sentence": [BGE, E5, ...]}
      │
      ├── for m in groups["week2"]:
      │     w2 = Week2InferenceService(paths)
      │     label, prob = w2.predict_proba(q1, q2, m)
      │     → ModelVote(model_name=m, label, prob, ...)
      │     │  on error → ModelVote(error=str(e))
      │
      ├── for m in groups["transformer"]:
      │     model, tok, meta = load_model_and_tokenizer(paths, m)
      │     svc = DuplicateQuestionInferenceService(model, tok, meta)
      │     label, prob = svc.predict_proba(q1, q2)
      │     → ModelVote(model_name=m, label, prob, ...)
      │     │  on error → ModelVote(error=str(e))
      │
      └── for m in groups["sentence"]:
            result = predict_with_sentence_transformer(m, q1, q2)
            → ModelVote(model_name=m, label, prob, ...)
            │  on error → ModelVote(error=str(e))

      ▼
  votes = [9 ModelVote objects]
```

### Data Flow Detail

```
                    ┌────────────────────────────────────────┐
                    │         EVIDENCE COLLECTION             │
                    │                                        │
  nq1, nq2 ────────▶│  ┌──────────┐                         │
                    │  │Model   1 │──▶ LR: (1, 0.72)        │
                    │  └──────────┘                         │
                    │  ┌──────────┐                         │
                    │  │Model   2 │──▶ SVM: (1, 0.68)       │
                    │  └──────────┘                         │
                    │  ┌──────────┐                         │
                    │  │Model   3 │──▶ W3: (1, 0.81)        │
                    │  └──────────┘                         │
                    │  ...                                  │
                    │  ┌──────────┐                         │
                    │  │Model   9 │──▶ CE-Q: (1, 0.14)     │
                    │  └──────────┘                         │
                    └────────────────────────────────────────┘
```

### Embedding Model Inference Detail

```
  predict_with_sentence_transformer("E5-base-v2", q1, q2)

  q1_norm = normalize_question(q1)
  q2_norm = normalize_question(q2)

  resolve_best_available_e5_model("E5-base-v2")
      → checks for fine-tuned model on disk
      → upgrades to "E5-quora-finetuned" if available

  model = get_sentence_transformer_model("E5-base-v2")
      → checks _sentence_transformer_cache
      → loads from HuggingFace Hub (or local)
      → caches for future calls

  use_e5_prefix = True  → E5 uses "query:" / "passage:" prefixes

  emb1 = model.encode("query: " + q1_norm, normalize_embeddings=True)
  emb2 = model.encode("passage: " + q2_norm, normalize_embeddings=True)

  similarity = dot(emb1, emb2)

  steepness, midpoint = _get_sigmoid_params("e5")  → (15.0, 0.50)
  prob_duplicate = sigmoid(15.0 * (similarity - 0.50))

  threshold = _get_threshold("E5-base-v2")  → 0.35

  label = 1 if prob_duplicate >= 0.35 else 0
```

### Model Loading Pipeline

```
  First call for model X:
      get_sentence_transformer_model("X")
          → cache miss → load from HF/local
          → store in _sentence_transformer_cache["X"]
          → return model

  Subsequent calls:
      get_sentence_transformer_model("X")
          → cache hit → return _sentence_transformer_cache["X"]

  Embedding cache (LRU, 10000 entries):
      encode(text) → check (model_name, text_hash)
          → hit: return cached embedding
          → miss: compute → store → return
```

### Future Implementation

- **Asynchronous model dispatch** — Launch all model inferences concurrently via asyncio/gather
- **GPU batching** — Batch-all questions through each model for GPU utilization
- **Speculative execution** — Fast models provide early vote; slow models refine
- **Model distillation** — Student model approximates ensemble for faster single-model inference

---

## 5. Stage 4: Reasoning (Adaptive Ensemble)

### Purpose
Weight and combine all model votes using input-adaptive rules derived from linguistic features, then apply penalties for detected contradictions and mismatches.

### Input
- `votes: list[ModelVote]` — All model predictions
- `linguistic_features: dict` — 5 penalty values from Understanding stage

### Output
- `ensemble_prob: float` — Combined probability
- `adaptive_weights: AdaptiveWeights` — Per-group weight distribution
- `contributions: dict` — Per-model weighted contributions

### Current Implementation

```
  _ensemble/v1.py :: get_adaptive_ensemble_prediction()
  _ensemble/v2.py :: adaptive_ensemble_predict()
```

```
  Adaptive Weight Computation:

  Input: nq1, nq2
      │
      ▼
  compute_adaptive_weights(q1, q2)
      │
      ├── _count_lexical_overlap(q1, q2)     → 0.35
      ├── _detect_abbreviations(q1)            → []
      ├── _detect_abbreviations(q2)            → []
      ├── _detect_synonyms(q1, q2)             → ["difference↔distinction"]
      └── _detect_semantic_depth(q1, q2)       → 0.25
      │
      ▼
  Base weights:
    lexical = 0.15, transformer = 0.25, embedding = 0.35, cross_enc = 0.25
      │
      ▼
  Rules applied sequentially:
    Rule 1: overlap=0.35 (>0.2) → no change
    Rule 2: semantic_depth=0.25 (<0.4) → no change
    Rule 3: synonyms=["difference↔distinction"] → embed+=0.15, lex-=0.10
    ... (10 rules in V2)
      │
      ▼
  Normalized: lexical=0.10, transformer=0.24, embedding=0.42, cross_enc=0.24
```

```
  Weighted Fusion (V2 Dynamic Confidence Routing):

  tfidf_avg     = mean(LR_prob, SVM_prob)                = 0.70
  trans_avg     = mean(W3_prob, W4_prob)                 = 0.78
  embed_avg     = mean(BGE_prob, E5_prob, MPNet_prob)    = 0.72
  cross_avg     = mean(DeBERTa_prob, CE_Q_prob)          = 0.35

  ensemble_raw  = 0.10×0.70 + 0.24×0.78 + 0.42×0.72 + 0.24×0.35
                = 0.070 + 0.187 + 0.302 + 0.084
                = 0.643

  total_penalty = 0.5×entity + 0.5×intent + 0.6×negation
                + 0.8×contradiction + 0.4×lexical
                = 0.5×0.0 + 0.5×0.0 + 0.6×0.0 + 0.8×0.0 + 0.4×0.12
                = 0.048

  ensemble_prob = 0.643 × (1.0 - min(0.7, 0.048)) = 0.643 × 0.952 = 0.612

  label = 1 (prob >= 0.5)
  confidence = max(0.612, 0.388) = 0.612
```

### Fallback Chain

```
  get_adaptive_ensemble_prediction()  ← V1 preferred
      │ on import error
      ▼
  adaptive_ensemble_predict()         ← V2 fallback
      │ on import error
      ▼
  trimmed_mean(probs)                 ← Robust fallback
      │ drop 1 highest, 1 lowest
      ▼
  0.5 (default)                       ← Catastrophic fallback
```

### Future Implementation

- **Bayesian ensemble** — Replace weighted average with Gaussian Process ensemble that models prediction uncertainty
- **Online weight learning** — Gradient-based weight optimization from error log feedback
- **Mixture of Experts** — Gated routing network trained to select best model subset per input
- **Multi-task ensemble** — Joint optimization over duplicate detection + intent classification + entity extraction

---

## 6. Stage 5: Decision (Threshold & Output)

### Purpose
Apply optimal decision thresholds, construct the final prediction, and package all intermediate data for downstream consumption.

### Input
- `ensemble_prob: float` — Combined probability from Reasoning stage
- `threshold: float` — Decision boundary (default 0.5, per-model optimized)
- `metadata: dict` — All intermediate values for explainability

### Output
- `result: dict` — Complete prediction result with 18+ fields

### Current Implementation

Integrated into each model's `_result_dict()` function and `get_adaptive_ensemble_prediction()`:

```
  result = {
      "question1":            nq1,
      "question2":            nq2,
      "predicted_label":      0 or 1,
      "prediction":           "Duplicate" | "Non-Duplicate",
      "prob_duplicate":       float,
      "prob_non_duplicate":   float,
      "confidence":           max(prob_dup, prob_non),
      "threshold":            float,
      "model_label":          str,
      "model_name":           str,
      "device":               "cpu" | "cuda",
      "latency_ms":           float,
      "reason":               str,
      "feature_breakdown":    dict {model: {prob, weight, contribution}},
      "adaptive_weights":     dict,
      "feature_analysis":     dict,
      "models_agreeing":      list[str],
      "models_disagreeing":   list[str],
  }
```

### Threshold Optimization

```
  For each model, find threshold that maximizes F1 on validation set:

  _evaluation/metrics.py :: threshold_sweep()

  sweep thresholds from 0.05 to 0.95 in 0.01 steps
  for each threshold:
      predict labels
      compute F1 score
  select threshold with highest F1

  Example per-model optimal thresholds:
    E5-base-v2:              0.35  (high recall but many FPs below 0.35)
    BGE-base-v1.5:           0.30
    MPNet-base-v2:           0.36
    DeBERTa-v3 Cross-Enc.:   0.44  (NLI entailment ratio)
    Cross-Enc.-Quora (Trained): 0.10  (binary CE trained on this task)
    Ensemble:                0.50  (balanced)
```

### Future Implementation

- **Cost-sensitive thresholding** — Weight false positive vs false negative costs
- **Meta-threshold model** — Learn threshold as function of input features (e.g., lower threshold for high-agreement pairs)
- **Reject option** — Below confidence threshold, defer to human review instead of predicting

---

## 7. Stage 6: Reflection (Post-Decision Analysis)

### Purpose
Evaluate prediction quality after the fact: calibrate probabilities, detect contradictions, identify error patterns, and log failures for learning.

### Input
- `result: dict` — Full prediction result
- `true_label: int | None` — Ground truth (if available)

### Output
- `calibrated_probs: np.ndarray` — Temperature/Platt/Isotonic calibrated probabilities
- `error_analysis: dict` — Error categories detected
- `error_example: ErrorExample | None` — Logged error (if misprediction)

### Current Implementation

```
  _calibration/v1.py :: calibrate_model_prediction()
  _calibration/v2.py :: calibrate_predictions()
  _evaluation/error_analysis.py :: categorize_error()
  _logging/error_logger.py :: log_prediction_error()
```

```
  Reflection Process:

  After prediction:
      │
      ▼
  1. Calibrate probabilities:
     ┌──────────────────┬──────────┬──────────┐
     │ Model            │ Method   │ Param    │
     ├──────────────────┼──────────┼──────────┤
     │ LR (W2)          │ default  │ -        │
     │ SVM (W2)         │ platt    │ a=1,b=0  │
     │ DistilBERT (W3)  │ temp     │ T=2.0    │
     │ DistilBERT (W4)  │ temp     │ T=2.0    │
     │ BGE              │ temp     │ T=1.3    │
     │ E5               │ temp     │ T=1.8    │
     │ MPNet            │ temp     │ T=1.2    │
     │ DeBERTa          │ default  │ -        │
     └──────────────────┴──────────┴──────────┘
      │
      ▼
  2. Error categorization (if true_label available):
     categorize_error(q1, q2, predicted, true, prob, all_probs)
         → [Abbreviation, Synonym, Negation, Question Type,
            Entity Mismatch, Paraphrase, Borderline,
            Model Disagreement]
      │
      ▼
  3. Hardness classification:
     classify_hardness(prob, conf, agreement, pred, true)
         → "easy" | "medium" | "hard" | "borderline" | "error"
      │
      ▼
  4. Error logging (if misprediction):
     log_prediction_error(q1, q2, result, true_label, error_analysis)
         → appends to hard_examples.csv
         → includes all 25+ fields
```

### Calibration Detail

```
  Temperature Scaling:

  Given raw probability p:
      logit = ln(p / (1-p))
      scaled_logit = logit / T
      p_calibrated = sigmoid(scaled_logit)

  T=2.0 means:
      p_raw=0.90 → p_cal=0.82  (less confident)
      p_raw=0.70 → p_cal=0.62  (less confident)
      p_raw=0.60 → p_cal=0.56  (less confident)
      p_raw=0.50 → p_cal=0.50  (unchanged at decision boundary)

  T=1.8 (E5, which tends to overpredict):
      p_raw=0.90 → p_cal=0.80
      p_raw=0.70 → p_cal=0.60
```

### Future Implementation

- **Online calibration** — Continuously update temperature/PI att parameters with streaming data
- **Meta-calibration** — Calibrate the calibrator using held-out validation set
- **Prediction interval estimation** — Output confidence intervals, not just point estimates
- **Concept drift detection** — Monitor ECE/F1 sliding window; trigger recalibration on drift

---

## 8. Stage 7: Learning (Experience Replay)

### Purpose
Extract actionable insights from accumulated error logs to adapt system parameters.

### Input
- `error_df: DataFrame` — Loaded from hard_examples.csv
- `metadata: dict` — Current system configuration

### Output
- `recommendations: list[str]` — Improvement suggestions
- `updated_params: dict` — Recommended parameter changes

### Current Implementation

```
  _logging/error_logger.py :: analyze_error_log()
  _logging/error_logger.py :: mine_hard_examples()
```

```
  Learning Cycle:

  analyze_error_log(hard_examples.csv)
      │
      ├── total_errors, FP count, FN count
      ├── error category distribution:
      │     entity_mismatch:    120 (32%)
      │     intent_mismatch:     85 (23%)
      │     negation_mismatch:   42 (11%)
      │     model_disagreement:  68 (18%)
      │     lexical_mismatch:    58 (16%)
      │
      ├── confidence stats for errors:
      │     mean=0.82 → model is overconfident when wrong
      │
      └── top confident errors (model was sure but wrong)
      │
      ▼
  _generate_recommendations():
      → "High entity mismatch rate: Improve entity detection"
      → "Errors have high average confidence: Apply calibration"
      → "High model disagreement: Investigate ensemble weights"
      │
      ▼
  mine_hard_examples(df, n=100, strategy="balanced"):
      → returns 100 hardest examples for human review
```

### Future Implementation

- **Active learning loop** — Query human labels for lowest-confidence predictions
- **Self-supervised fine-tuning** — Use disagreement regions as training signal for model updates
- **Counterfactual learning** — Learn from "what if" scenarios simulated via linguistic perturbation
- **Automated rule discovery** — Decision tree over error features → discover new weight rules
- **Continuous model evaluation** — Scheduled re-evaluation of all models against latest error distribution

---

## 9. Complete Pipeline Data Flow Diagram

```
  STAGE 1                    STAGE 2                    STAGE 3
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │ q1:"How to..."   │       │ normalize_      │       │ collect_all_    │
  │ q2:"How can..."  │       │ question()      │       │ votes()         │
  │                  │       │                 │       │                 │
  │ 1. strip         │──────▶│ 5 engines run   │──────▶│ 9 model queries │
  │ 2. lowercase     │       │ negation        │       │ LR: 0.72        │
  │ 3. expand_abbr   │       │ contradiction   │       │ SVM: 0.68       │
  │ 4. fix_typos     │       │ entity          │       │ W3: 0.81        │
  │ 5. extract_feat  │       │ intent          │       │ W4: 0.77        │
  └─────────────────┘       │ lexical         │       │ BGE: 0.74       │
                            └─────────────────┘       │ E5: 0.69        │
                                                      │ MPNet: 0.73     │
                                                      │ DeBERTa: 0.88   │
                                                      │ CE-Q: 0.14      │
                                                      └─────────────────┘
                                                             │
                    ┌────────────────────────────────────────┘
                    │
                    ▼
  STAGE 4           ┌────────────────────────────────────────┐
  ┌─────────────────┐│  STAGE 5           STAGE 6            │
  │ compute_adaptive││  ┌─────────────────┐ ┌──────────────┐ │
  │ _weights()     ││  │ apply_threshold │ │ calibrate()  │ │
  │                 ││  │ ensemble_prob   │ │ categorize_  │ │
  │ overlap=0.35   ││  │ = 0.62          │ │ error()      │ │
  │ depth=0.25     ││  │ threshold=0.5   │ │              │ │
  │ syn detected   ││  │ label=1         │ │ log_error()  │ │
  │                 ││  │ confidence=0.62 │ │              │ │
  │ weights:       ││  └─────────────────┘ └──────────────┘ │
  │ lex=0.10       ││                                        │
  │ trans=0.24    ││                 ┌────────────────────┐  │
  │ embed=0.42    ││                 │ STAGE 7            │  │
  │ cross=0.24    ││                 │ analyze_error_log()│  │
  │                 ││                 │ mine_hard_examples│  │
  │ ensemble_prob  ││                 │ generate_recomm. │  │
  │ = 0.62         ││                 └────────────────────┘  │
  └─────────────────┘└────────────────────────────────────────┘
```

---

## 10. Latency Budget

| Stage | Operation | Latency | Cumulative |
|---|---|---|---|
| 1 | Normalization + feature extraction | 5ms | 5ms |
| 2 | 5 linguistic engines | 50ms | 55ms |
| 3a | Classical ML (2 models) | 20ms | 75ms |
| 3b | Transformers (2 models) | 1000ms | 1075ms |
| 3c | Bi-encoders (3 models) | 600ms | 1675ms |
| 3d | Cross-encoders (2 models) | 800ms | 2475ms |
| 4 | Weight computation + fusion | 5ms | 2480ms |
| 5 | Threshold + output construction | 1ms | 2481ms |
| 6 | Calibration + error analysis | 15ms | 2496ms |
| 7 | Error logging (async) | 10ms | 2506ms |
| **Total** | | **~2500ms** | |

*Note: Latencies measured on CPU (Intel i7, 16GB RAM). GPU reduces transformer/encoder stages by 3-5×.*
