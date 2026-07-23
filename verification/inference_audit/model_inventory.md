# Model Inventory — Complete

## 11 Registered Models

### 1. TF-IDF + Logistic Regression (Week 2)
| Field | Value |
|-------|-------|
| Display Name | TF-IDF + Logistic Regression (Week 2) |
| Internal ID | `week2_lr` |
| Architecture | Logistic Regression (scikit-learn) |
| Task | Binary Classification (duplicate / non-duplicate) |
| Framework | scikit-learn / joblib |
| Training Method | Custom scikit-learn training on TF-IDF n-gram features (1,2) |
| Saved Format | joblib pickle |
| Artifact Location | `models/week2_models/logistic_regression.joblib` |
| Model Size | 79 KB |
| Tokenizer | None (TF-IDF vectorizer only) |
| Inference Backend | `Week2InferenceService` |
| Current Status | Ready — all files present |
| Supported | YES |
| Reason | Complete, tested, dedicated loader |

### 2. TF-IDF + Linear SVM (Week 2)
| Field | Value |
|-------|-------|
| Display Name | TF-IDF + Linear SVM (Week 2) |
| Internal ID | `week2_svm` |
| Architecture | Linear SVM (scikit-learn) |
| Task | Binary Classification |
| Framework | scikit-learn / joblib |
| Training Method | Custom scikit-learn training on TF-IDF features |
| Saved Format | joblib pickle |
| Artifact Location | `models/week2_models/linear_svm.joblib` |
| Model Size | 79 KB |
| Tokenizer | None (TF-IDF vectorizer only) |
| Inference Backend | `Week2InferenceService` |
| Current Status | Ready — all files present |
| Supported | YES |
| Reason | Complete, tested, dedicated loader |

### 3. DistilBERT (Week 3)
| Field | Value |
|-------|-------|
| Display Name | DistilBERT (Week 3) |
| Internal ID | `week3` |
| Architecture | `DistilBertForSequenceClassification` (6 layers, 768 hidden) |
| Task | Binary Classification |
| Framework | PyTorch / HuggingFace Transformers |
| Training Method | HuggingFace Trainer, 3 epochs, batch_size=8 |
| Saved Format | safetensors + config.json + tokenizer |
| Artifact Location | `models/saved_transformer_model/` |
| Model Size | 256 MB (weights) + tokenizer files |
| Tokenizer | `BertTokenizer` (do_lower_case=True) |
| Inference Backend | `DuplicateQuestionInferenceService` |
| Current Status | Ready — all files present |
| Supported | YES |
| Reason | Complete, tested, dedicated loader |

### 4. Improved DistilBERT (Week 4)
| Field | Value |
|-------|-------|
| Display Name | Improved DistilBERT (Week 4) |
| Internal ID | `week4` |
| Architecture | `DistilBertForSequenceClassification` (6 layers, 768 hidden) |
| Task | Binary Classification |
| Framework | PyTorch / HuggingFace Transformers |
| Training Method | HuggingFace Trainer, 3 epochs (best at epoch 3: acc=0.8941) |
| Saved Format | safetensors + config.json + tokenizer |
| Artifact Location | `models/week4_improved_model/` |
| Model Size | 256 MB (weights) + tokenizer files |
| Tokenizer | `BertTokenizer` (do_lower_case=True, max_length=128) |
| Inference Backend | `DuplicateQuestionInferenceService` |
| Current Status | Ready — all files present (DEFAULT model) |
| Supported | YES (default) |
| Reason | Complete, tested, dedicated loader, best accuracy |

### 5. BGE-base-en-v1.5
| Field | Value |
|-------|-------|
| Display Name | BGE-base-en-v1.5 |
| Internal ID | `bge` |
| Architecture | BERT-based bi-encoder (sentence-transformers) |
| Task | Embedding → Cosine Similarity → Sigmoid Calibration |
| Framework | sentence-transformers / PyTorch |
| Training Method | Pre-trained (BAAI/bge-base-en-v1.5) |
| Saved Format | HF hub auto-download |
| Artifact Location | Not on disk — downloaded from `BAAI/bge-base-en-v1.5` on HF Hub |
| Model Size | ~400 MB (hub download) |
| Tokenizer | BERT tokenizer (auto-downloaded) |
| Inference Backend | `SentenceTransformer` via `_models/embeddings.py` |
| Current Status | Requires HF hub download at runtime |
| Supported | YES (requires internet/hub access) |
| Reason | HF model available, loader exists, LR head available |

### 6. E5-base-v2
| Field | Value |
|-------|-------|
| Display Name | E5-base-v2 |
| Internal ID | `e5` |
| Architecture | BERT-based bi-encoder (sentence-transformers) |
| Task | Embedding → Cosine Similarity → Sigmoid Calibration |
| Framework | sentence-transformers / PyTorch |
| Training Method | Pre-trained (intfloat/e5-base-v2) |
| Saved Format | HF hub auto-download |
| Artifact Location | Not on disk — downloaded from `intfloat/e5-base-v2` on HF Hub |
| Model Size | ~400 MB (hub download) |
| Tokenizer | BERT tokenizer (auto-downloaded) |
| Inference Backend | `SentenceTransformer` via `_models/embeddings.py` |
| Current Status | Requires HF hub download at runtime |
| Supported | YES (requires internet/hub access) |
| Reason | HF model available, loader exists, LR head + MLP head available |

### 7. E5-quora-finetuned
| Field | Value |
|-------|-------|
| Display Name | E5-quora-finetuned |
| Internal ID | `e5_ft` |
| Architecture | `BertModel` (SentenceTransformer) fine-tuned from `intfloat/e5-base-v2` |
| Task | Embedding → Cosine Similarity → Sigmoid Calibration |
| Framework | sentence-transformers 5.6.0 / PyTorch 2.6.0 |
| Training Method | Fine-tuned with `MultipleNegativesRankingLoss`, 5 epochs, batch_size=64, fp16 |
| Saved Format | safetensors (418 MB) + full SentenceTransformer config |
| Artifact Location | `models/e5-quora-finetuned/` |
| Model Size | 418 MB (weights) + tokenizer + config |
| Tokenizer | `BertTokenizer` (do_lower_case=True) |
| Inference Backend | `SentenceTransformer` via `_models/embeddings.py` |
| Current Status | Ready — all files present |
| Supported | YES |
| Reason | Complete SentenceTransformer package, local disk |

### 8. MPNet-base-v2
| Field | Value |
|-------|-------|
| Display Name | MPNet-base-v2 |
| Internal ID | `mpnet` |
| Architecture | MPNet-based bi-encoder (sentence-transformers) |
| Task | Embedding → Cosine Similarity → Sigmoid Calibration |
| Framework | sentence-transformers / PyTorch |
| Training Method | Pre-trained (sentence-transformers/all-mpnet-base-v2) |
| Saved Format | HF hub auto-download |
| Artifact Location | Not on disk — downloaded from `sentence-transformers/all-mpnet-base-v2` on HF Hub |
| Model Size | ~400 MB (hub download) |
| Tokenizer | MPNet tokenizer (auto-downloaded) |
| Inference Backend | `SentenceTransformer` via `_models/embeddings.py` |
| Current Status | Requires HF hub download at runtime |
| Supported | YES (requires internet/hub access) |
| Reason | HF model available, loader exists, LR head available |

### 9. DeBERTa-v3 Cross-Encoder
| Field | Value |
|-------|-------|
| Display Name | DeBERTa-v3 Cross-Encoder |
| Internal ID | `deberta` |
| Architecture | `cross-encoder/nli-deberta-v3-base` (sentence-transformers CrossEncoder) |
| Task | NLI 3-class → Convert to duplicate probability |
| Framework | sentence-transformers / PyTorch |
| Training Method | Pre-trained NLI cross-encoder |
| Saved Format | HF hub auto-download |
| Artifact Location | Not on disk — downloaded from `cross-encoder/nli-deberta-v3-base` on HF Hub |
| Model Size | ~700 MB (hub download) |
| Tokenizer | DeBERTa tokenizer (auto-downloaded) |
| Inference Backend | `CrossEncoder` via `_models/embeddings.py` |
| Current Status | Requires HF hub download at runtime |
| Supported | YES (requires internet/hub access) |
| Reason | HF model available, loader exists |

### 10. Cross-Encoder-Quora (Trained)
| Field | Value |
|-------|-------|
| Display Name | Cross-Encoder-Quora (Trained) |
| Internal ID | `ce_quora` |
| Architecture | `DebertaV2ForSequenceClassification` |
| Task | Binary Classification (Quora duplicate pairs) |
| Framework | HuggingFace Transformers 5.13.0 |
| Training Method | **Unknown** — no training script found |
| Saved Format | safetensors (704 MB) + config.json + tokenizer files |
| Artifact Location | `models/cross-encoder-quora/` |
| Model Size | 704 MB (weights) + tokenizer + config |
| Tokenizer | `DebertaV2Tokenizer` (spm, do_lower_case=False) |
| Inference Backend | `CrossEncoder` from sentence-transformers (via `_models/embeddings.py`) |
| Current Status | **WARNING** — files present but `transformers_version: "5.13.0"` is suspicious |
| Supported | PARTIAL — files exist but untested loading |
| Reason | Complete artifact set, but `transformers_version: 5.13.0` in config.json does not match any public release (latest is ~4.49) |

### 11. Semantic Ensemble
| Field | Value |
|-------|-------|
| Display Name | Semantic Ensemble |
| Internal ID | `ensemble` |
| Architecture | Adaptive weighted ensemble of 9 sub-models |
| Task | Binary Classification (ensemble voting) |
| Framework | Custom (ensemble of all available backends) |
| Training Method | Rule-based dynamic weighting (10 rules) |
| Saved Format | Built-in (no artifact files) |
| Artifact Location | N/A — pure code |
| Model Size | N/A |
| Tokenizer | N/A |
| Inference Backend | `_ensemble/v1.py` or `v2.py` |
| Current Status | Works if at least one sub-model works |
| Supported | YES (depends on sub-models) |
| Reason | Code-based ensemble, no artifacts needed |

### Auxiliary Artifacts (not registered models)

| Artifact | Type | Size | Purpose |
|----------|------|------|---------|
| `models/e5_base_v2_lr_head.pkl` | LogisticRegression head (sklearn) | 13 KB | Classification head for E5-base-v2 embeddings |
| `models/bge_lr_head.pkl` | LogisticRegression head (sklearn) | 13 KB | Classification head for BGE embeddings |
| `models/all_mpnet_base_v2_lr_head.pkl` | LogisticRegression head (sklearn) | 13 KB | Classification head for MPNet embeddings |
| `models/e5_mlp_head.pt` | MLP head (PyTorch state_dict) | 3.1 MB | MLP head for E5-base-v2 embeddings |
| `models/baseline_model_cache/word2vec_quora.model` | Word2Vec | 47 MB | Pre-trained Word2Vec on Quora |
| `models/baseline_model_cache/sbert_q1_embeddings.npy` | NumPy embeddings | 593 MB | Pre-computed SBERT Q1 embeddings |
| `models/baseline_model_cache/sbert_q2_embeddings.npy` | NumPy embeddings | 593 MB | Pre-computed SBERT Q2 embeddings |

### Training Checkpoints (not inference-ready)

| Path | Epoch | Accuracy | F1 | Optimizer State |
|------|-------|----------|----|-----------------|
| `models/transformer_training_outputs/checkpoint-18193` | 1.0 | 0.8735 | 0.8727 | 511 MB (optimizer.pt) |
| `models/transformer_training_outputs/checkpoint-36386` | 2.0 | 0.8903 | 0.8910 | 511 MB (optimizer.pt) |
| `models/transformer_training_outputs/checkpoint-54579` | 3.0 | **0.8941** | **0.8946** | 511 MB (optimizer.pt) |

### Key Observations

1. **No ONNX models exist anywhere** in the project
2. **No TorchScript models** (e5_mlp_head.pt is a state_dict, not TorchScript)
3. **Cross-Encoder-Quora (Trained)** has a `transformers_version: "5.13.0"` in config.json — this is NOT a valid HuggingFace transformers release version (current is ~4.49), suggesting either a modified/custom build or a config-generation bug
4. **3 HF hub models** (BGE, E5, MPNet) require internet access for first load
5. **E5-quora-finetuned** is the only SentenceTransformer model fully on disk
6. **Week 4 model** is the only model with a dedicated threshold file (`threshold_analysis.csv`)
7. **Training checkpoints** retain 511 MB optimizer states each — they are resume-capable checkpoints, not trimmed inference exports
