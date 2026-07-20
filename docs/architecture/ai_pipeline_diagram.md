# AI Pipeline Diagram — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. End-to-End ML Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA ACQUISITION                                 │
│                                                                         │
│  Quora Dataset (CSV)                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ 404,290     │  │ 37% dup     │  │ 63% non-dup │  │ id, qid1,   │  │
│  │ pairs       │  │ 149,263     │  │ 255,027     │  │ qid2, q1,   │  │
│  │             │  │             │  │             │  │ q2, label   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA PREPROCESSING                               │
│                                                                         │
│  _preprocessing/text.py :: normalize_question()                         │
│                                                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────┐ │
│  │ tolower│→│ NFKC   │→│ decode │→│remove  │→│ expand │→│ trim  │ │
│  │        │  │        │  │ HTML   │  │ URLs   │  │ abbrev │  │space │ │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └──────┘ │
│                                                       │                │
│                                          ┌────────────┴────────┐       │
│                                          │ Typo correction      │       │
│                                          │ (15+ mappings)       │       │
│                                          └─────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        TRAINING PIPELINE                                │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 80/10/10 Stratified Split                                        │   │
│  │ train_df: 323,432 | val_df: 40,429 | test_df: 40,429            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                   │
│         ┌──────────────────────────┼──────────────────────────┐        │
│         ▼                          ▼                          ▼        │
│  ┌──────────────┐        ┌──────────────────┐       ┌────────────────┐ │
│  │ Classical ML  │        │ Transformer       │       │ Embedding      │ │
│  │ (Week 2)      │        │ (Week 3 & 4)      │       │ (Phase 2)      │ │
│  │               │        │                   │       │                │ │
│  │ TF-IDF (1,2)  │        │ DistilBERT        │       │ BGE-base-v1.5  │ │
│  │ ↓             │        │ (66.9M params)    │       │ E5-base-v2     │ │
│  │ LR / SVM      │        │ 128 max seq       │       │ MPNet-base-v2  │ │
│  │               │        │ lr=2e-5           │       │                │ │
│  │ ~73% accuracy │        │ batch=32          │       │ LR heads       │ │
│  │               │        │ 3 epochs          │       │ (pkl files)    │ │
│  │               │        │                   │       │                │ │
│  │               │        │ ~83% accuracy     │       │ Frozen: ~80%   │ │
│  │               │        │ Week4: +class wt  │       │ Fine-tuned:+5% │ │
│  └──────────────┘        └──────────────────┘       └────────────────┘ │
│                                    │                                   │
│         ┌──────────────────────────┘                                   │
│         ▼                                                              │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Advanced Training (tools/)                                      │    │
│  │                                                                 │    │
│  │ tools/train_cross_encoder.py                                    │    │
│  │   → DeBERTa-v3-base (184M params)                               │    │
│  │   → 200K training pairs                                         │    │
│  │   → FP16 + fused AdamW                                          │    │
│  │   → models/cross-encoder-quora/                                 │    │
│  │                                                                 │    │
│  │ tools/train_e5_quora.py                                         │    │
│  │   → E5-base-v2 contrastive fine-tuning                          │    │
│  │   → MultipleNegativesRankingLoss                                │    │
│  │   → models/e5-quora-finetuned/                                  │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        MODEL REGISTRY                                   │
│                                                                         │
│  _models/registry.py :: build_registry()                                │
│                                                                         │
│  ┌──────┬──────────────┬──────────┬────────┬───────┬─────────┐        │
│  │  #   │ Model Name    │ Type     │ Source │Params │ Status  │        │
│  ├──────┼──────────────┼──────────┼────────┼───────┼─────────┤        │
│  │  1   │ TF-IDF+LR    │ classical│ local  │ ~5K   │ present │        │
│  │  2   │ TF-IDF+SVM   │ classical│ local  │ ~5K   │ present │        │
│  │  3   │ DistilBERT W3│ transform│ local  │66.9M  │ present │        │
│  │  4   │ DistilBERT W4│ transform│ local  │66.9M  │ present │        │
│  │  5   │ BGE v1.5     │ bi-enc   │ HF     │ 110M  │ cached  │        │
│  │  6   │ E5 v2        │ bi-enc   │ HF     │ 118M  │ cached  │        │
│  │  7   │ E5-ft (Quora)│ bi-enc   │ local  │ 118M  │ present │        │
│  │  8   │ MPNet v2     │ bi-enc   │ HF     │ 110M  │ cached  │        │
│  │  9   │ DeBERTa-v3 CE│ cross-enc│ HF     │ 184M  │ cached  │        │
│  │ 10   │ CE-Quora (Tr)│ cross-enc│ local  │ 184M  │ present │        │
│  │ 11   │ Ensemble     │ ensemble │ built  │ varies│ loaded  │        │
│  └──────┴──────────────┴──────────┴────────┴───────┴─────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        INFERENCE PIPELINE                               │
│                                                                         │
│  User Input (q1, q2)                                                    │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │            Model Dispatch (services/runtime.py)              │       │
│  │                                                              │       │
│  │  is_week2_model? → _models/week2.py :: Week2InferenceService │       │
│  │  is_transformer? → _inference/transformer.py                 │       │
│  │  is_cross_enc?   → _models/embeddings.py :: CrossEncoder     │       │
│  │  is_bi_encoder?  → _models/embeddings.py :: SentenceTransf.  │       │
│  │  is_ensemble?    → _models/embeddings.py :: get_ensemble     │       │
│  └─────────────────────────────────────────────────────────────┘       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │            Post-Processing                                   │       │
│  │                                                              │       │
│  │  1. Sigmoid Calibration (per-model params from config)       │       │
│  │  2. Threshold Comparison (per-model threshold from config)   │       │
│  │  3. Result dict construction                                 │       │
│  └─────────────────────────────────────────────────────────────┘       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │            Output                                              │       │
│  │                                                              │       │
│  │  { prob, label, confidence, threshold, latency }              │       │
│  └─────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EVALUATION PIPELINE                              │
│                                                                         │
│  test_df (40K pairs)                                                    │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  _evaluation/metrics.py :: generate_evaluation_report()       │       │
│  │                                                              │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │       │
│  │  │ Classification│  │ Ranking      │  │ Calibration  │       │       │
│  │  │ Metrics       │  │ Metrics      │  │ Metrics      │       │       │
│  │  ├──────────────┤  ├──────────────┤  ├──────────────┤       │       │
│  │  │ Accuracy    │  │ ROC-AUC     │  │ ECE          │       │       │
│  │  │ Precision   │  │ PR-AUC      │  │ MCE          │       │       │
│  │  │ Recall      │  │              │  │ Brier        │       │       │
│  │  │ F1          │  │              │  │              │       │       │
│  │  │ MCC         │  │              │  │              │       │       │
│  │  │ Specificity │  │              │  │              │       │       │
│  │  │ NPV         │  │              │  │              │       │       │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │       │
│  └─────────────────────────────────────────────────────────────┘       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Error Analysis (_evaluation/error_analysis.py)              │       │
│  │                                                              │       │
│  │  Categories: false_entity, negation, intent, quantity,       │       │
│  │              scope, lexical, ambiguity                        │       │
│  └─────────────────────────────────────────────────────────────┘       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Visualizations (_visualization/plots.py)                     │       │
│  │                                                              │       │
│  │  Confusion Matrix | ROC Curve | PR Curve | Calibration Curve │       │
│  │  Score Distribution | Threshold Sweep | Radar Chart          │       │
│  └─────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXPLAINABILITY PIPELINE                          │
│                                                                         │
│  Input: (q1, q2, model_name)                                            │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Linguistic Analysis (5 engines)                             │       │
│  │                                                              │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │       │
│  │  │Negation  │ │Contradic │ │ Entity   │ │ Intent   │       │       │
│  │  │Detector  │ │tion Det. │ │ Detector │ │ Detector │       │       │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │       │
│  │  ┌────────────────────────────────────────────────────┐     │       │
│  │  │ Lexical Penalty Analyzer                           │     │       │
│  │  │ (POS-tag heuristics, 7 penalty types)              │     │       │
│  │  └────────────────────────────────────────────────────┘     │       │
│  └─────────────────────────────────────────────────────────────┘       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Model Agreement (_explainability/agreement_dashboard.py)    │       │
│  │                                                              │       │
│  │  9 models vote → agreement % → entropy → strength class     │       │
│  └─────────────────────────────────────────────────────────────┘       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Decision Trace (_explainability/trace.py)                   │       │
│  │                                                              │       │
│  │  17+ fields: votes, agreement, linguistic analysis, weights │       │
│  └─────────────────────────────────────────────────────────────┘       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Text Explanation (_explainability/text.py)                  │       │
│  │                                                              │       │
│  │  Level 1: Basic  (1-2 sentences)                             │       │
│  │  Level 2: Standard (paragraph)                               │       │
│  │  Level 3: Detailed (multi-paragraph)                         │       │
│  │  Level 4: Comprehensive (full report + counterfactuals)      │       │
│  └─────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ensemble Pipeline Detail

```
                    ┌─────────────┐
                    │  Input Pair │
                    │  (q1, q2)   │
                    └──────┬──────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │  Linguistic Feature Extraction│
              │  (5 engines, ~50ms total)     │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────────┐ ┌──────────┐ ┌──────────────────┐
    │ lexical_sim     │ │entity_ov │ │ negation_mismatch │
    │ (lexical.py)    │ │(entity.py)│ │ (negation.py)     │
    └────────┬────────┘ └────┬─────┘ └────────┬─────────┘
              │              │                │
    ┌─────────┼──────────────┼────────────────┼──────────┐
    ▼         ▼              ▼                ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────────┐ ┌──────┐
│ TFIDF│ │Transf│ │BiEnc │ │Cross │ │ Contradiction│ │Intent│
│Group │ │Group │ │Group │ │EncGp │ │ (contrad.py) │ │Match │
│(2mod)│ │(2mod)│ │(3mod)│ │(2mod)│ └──────┬───────┘ │(intent)
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘        │         └──┬───┘
   │        │        │        │             │            │
   └────────┴────────┴────────┴─────────────┴────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Dynamic Weight      │
                 │ Computation         │
                 │                     │
                 │ w_tfidf = f(lex)    │
                 │ w_trans = f(intent) │
                 │ w_emb  = f(entity)  │
                 │ w_ce   = f(neg,cont)│
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Weighted Average    │
                 │                     │
                 │ pred = Σ(w_i * p_i) │
                 │       ───────────   │
                 │         Σ(w_i)      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Trimmed Mean        │
                 │ (exclude outliers)  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Final Prediction    │
                 │ + Confidence        │
                 └─────────────────────┘
```

---

## 3. Model Training Lifecycle

```
Notebook Prototyping
    │
    ├── data_analysis.ipynb (Week 1)
    │   → Understanding data distribution, class balance, question lengths
    │
    ├── baseline_model.ipynb (Week 2)
    │   → TF-IDF + LR / SVM prototyping
    │   → ~73% accuracy established
    │
    ├── transformer_model.ipynb (Week 3)
    │   → DistilBERT fine-tuning
    │   → ~83% accuracy (10% improvement)
    │
    └── week4_improvement.ipynb (Week 4)
        → Class weighting + threshold tuning
        → ~1-2% F1 improvement
        → Ablation studies, error analysis
    │
    ▼
Productionization (tools/)
    │
    ├── export_week2_models.py
    │   → Reproduce notebook results as reloadable joblib
    │
    ├── train_cross_encoder.py
    │   → DeBERTa-v3 fine-tuning on 200K pairs
    │   → GPU-optimized (FP16, fused AdamW)
    │
    ├── train_e5_quora.py
    │   → E5-base contrastive fine-tuning
    │   → MultipleNegativesRankingLoss
    │
    └── run_training_pipeline.py
        → Orchestrates all training steps
        → mine → train-e5 → train-cross-encoder → evaluate
    │
    ▼
Model Evaluation (tools/)
    │
    ├── enhanced_evaluation.py
    ├── evaluate_embedding_models.py
    ├── ultimate_benchmark.py
    ├── verify_all_models.py
    ├── self_validation.py
    └── fix_e5_predictions.py
    │
    ▼
Model Integration
    │
    ├── Add to _models/ (inference code)
    ├── Add to configs/models.yaml (registry entry)
    ├── Add to _models/registry.py (metadata)
    └── Add to _ensemble/ (if ensemble participant)
```
