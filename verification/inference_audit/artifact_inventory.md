# Artifact Inventory — Complete

## Per-Model Artifact Verification

### 1. TF-IDF + Logistic Regression (Week 2)
| Artifact | Path | Status |
|----------|------|--------|
| tfidf_vectorizer.joblib | `models/week2_models/tfidf_vectorizer.joblib` | ✅ Present (185 KB) |
| logistic_regression.joblib | `models/week2_models/logistic_regression.joblib` | ✅ Present (79 KB) |
| linear_svm.joblib | `models/week2_models/linear_svm.joblib` | ✅ Present (79 KB) |

**Missing:** None
**Can run today:** YES

---

### 2. TF-IDF + Linear SVM (Week 2)
Same files as above. Uses `linear_svm.joblib` instead of `logistic_regression.joblib`.

**Missing:** None
**Can run today:** YES

---

### 3. DistilBERT (Week 3)
| Artifact | Path | Status |
|----------|------|--------|
| config.json | `models/saved_transformer_model/config.json` | ✅ Present (664 B) |
| model.safetensors | `models/saved_transformer_model/model.safetensors` | ✅ Present (256 MB) |
| tokenizer.json | `models/saved_transformer_model/tokenizer.json` | ✅ Present (695 KB) |
| tokenizer_config.json | `models/saved_transformer_model/tokenizer_config.json` | ✅ Present (351 B) |
| special_tokens_map.json | — | ❌ Missing |
| vocab.txt | — | ❌ Missing (tokenizer.json is SentencePiece) |
| training_args.bin | — | ❌ Missing |
| trainer_state.json | — | ❌ Missing |

**Notes:** `AutoTokenizer.from_pretrained()` can load from only `tokenizer.json` and `tokenizer_config.json`. `special_tokens_map.json` is optional. The tokenizer is `BertTokenizer` which loads from `tokenizer.json`. **Config specifies transformers_version: 5.13.0** — see root cause analysis.

**Missing for training resume:** training_args.bin, trainer_state.json
**Missing for inference:** None (all required artifacts present)
**Can run today:** YES

---

### 4. Improved DistilBERT (Week 4)
| Artifact | Path | Status |
|----------|------|--------|
| config.json | `models/week4_improved_model/config.json` | ✅ Present (664 B) |
| model.safetensors | `models/week4_improved_model/model.safetensors` | ✅ Present (256 MB) |
| tokenizer.json | `models/week4_improved_model/tokenizer.json` | ✅ Present (695 KB) |
| tokenizer_config.json | `models/week4_improved_model/tokenizer_config.json` | ✅ Present (541 B) |
| special_tokens_map.json | — | ❌ Missing |
| vocab.txt | — | ❌ Missing |
| threshold_analysis.csv | `outputs/week4_improvement/threshold_analysis.csv` | ✅ Present (not checked directly) |

**Missing for inference:** None
**Can run today:** YES (DEFAULT MODEL)

---

### 5. BGE-base-en-v1.5
| Artifact | Path | Status |
|----------|------|--------|
| Local directory | `models/bge_base_en_v1_5/` | ❌ Not on disk |
| HF cache | HF hub cache (auto-download) | Depends on prior download |

**Missing:** All files — requires HF hub download
**Can run today:** YES (with internet access)

---

### 6. E5-base-v2
| Artifact | Path | Status |
|----------|------|--------|
| Local directory | `models/e5_base_v2/` | ❌ Not on disk |
| HF cache | HF hub cache (auto-download) | Depends on prior download |
| LR head | `models/e5_base_v2_lr_head.pkl` | ✅ Present (13 KB) |
| MLP head | `models/e5_mlp_head.pt` | ✅ Present (3.1 MB) |

**Missing:** Base model — requires HF hub download
**Can run today:** YES (with internet access)

---

### 7. E5-quora-finetuned
| Artifact | Path | Status |
|----------|------|--------|
| config.json | `models/e5-quora-finetuned/config.json` | ✅ Present (747 B) |
| model.safetensors | `models/e5-quora-finetuned/model.safetensors` | ✅ Present (418 MB) |
| tokenizer.json | `models/e5-quora-finetuned/tokenizer.json` | ✅ Present (695 KB) |
| tokenizer_config.json | `models/e5-quora-finetuned/tokenizer_config.json` | ✅ Present (391 B) |
| sentence_bert_config.json | `models/e5-quora-finetuned/sentence_bert_config.json` | ✅ Present |
| config_sentence_transformers.json | `models/e5-quora-finetuned/config_sentence_transformers.json` | ✅ Present |
| modules.json | `models/e5-quora-finetuned/modules.json` | ✅ Present |
| 1_Pooling/config.json | `models/e5-quora-finetuned/1_Pooling/config.json` | ✅ Present |
| README.md | `models/e5-quora-finetuned/README.md` | ✅ Present |
| evaluation results CSV | `models/e5-quora-finetuned/eval/binary_classification_evaluation_results.csv` | ✅ Present |

**Missing:** special_tokens_map.json (optional — tokenizer.json contains all data)
**Can run today:** YES (complete SentenceTransformer on disk)

---

### 8. MPNet-base-v2
| Artifact | Path | Status |
|----------|------|--------|
| Local directory | `models/mpnet_base_v2/` | ❌ Not on disk |
| HF cache | HF hub cache (auto-download) | Depends on prior download |
| LR head | `models/all_mpnet_base_v2_lr_head.pkl` | ✅ Present (13 KB) |

**Missing:** Base model — requires HF hub download
**Can run today:** YES (with internet access)

---

### 9. DeBERTa-v3 Cross-Encoder
| Artifact | Path | Status |
|----------|------|--------|
| Local directory | `models/deberta_v3_cross_encoder/` | ❌ Not on disk |
| HF cache | HF hub cache (auto-download) | Depends on prior download |

**Missing:** All files — requires HF hub download
**Can run today:** YES (with internet access)

---

### 10. Cross-Encoder-Quora (Trained)
| Artifact | Path | Status |
|----------|------|--------|
| config.json | `models/cross-encoder-quora/config.json` | ✅ Present (925 B) |
| model.safetensors | `models/cross-encoder-quora/model.safetensors` | ✅ Present (704 MB) |
| tokenizer.json | `models/cross-encoder-quora/tokenizer.json` | ✅ Present (8.0 MB) |
| tokenizer_config.json | `models/cross-encoder-quora/tokenizer_config.json` | ✅ Present (538 B) |
| special_tokens_map.json | — | ❌ Missing |
| sentence_bert_config.json | — | ❌ Missing (NOT a SentenceTransformer) |
| config_sentence_transformers.json | — | ❌ Missing (NOT a SentenceTransformer) |
| modules.json | — | ❌ Missing (NOT a SentenceTransformer) |

**Critical Issue:** `config.json` specifies `transformers_version: "5.13.0"` — this is NOT a valid public HuggingFace transformers release. The latest public release is ~4.49.x. This suggests:
1. The model was saved with a custom/forked transformers build
2. Or the version string is incorrect/incompatible

**Can run today:** UNKNOWN — depends on whether `transformers` 4.x can load a model tagged with version 5.13.0. In practice, AutoModelForSequenceClassification may reject or behave unexpectedly.

**Required for SentenceTransformer loading:** None — this model is NOT a SentenceTransformer. It is a raw `DebertaV2ForSequenceClassification` that is loaded via `CrossEncoder` wrapper from `sentence-transformers`. The `CrossEncoder` class initializes `AutoModelForSequenceClassification` internally.

---

### 11. Semantic Ensemble
| Artifact | Path | Status |
|----------|------|--------|
| N/A | N/A | ✅ Code-only |

**Can run today:** YES (depends on sub-models)

---

## Cross-Cutting Artifact Issues

### Issue 1: Missing special_tokens_map.json
Across all transformer models, `special_tokens_map.json` is missing. This is **not blocking** for inference — `AutoTokenizer.from_pretrained()` uses `tokenizer_config.json` and `tokenizer.json` only. However, some tokenizer operations (adding tokens, saving/reloading) may behave differently.

### Issue 2: No tokenizer for Week 2 models
Week 2 models (TF-IDF + LR/SVM) use a `tfidf_vectorizer.joblib` instead of a tokenizer. This is correct — no tokenizer is expected.

### Issue 3: transformers_version: "5.13.0" in local models
Both `saved_transformer_model/config.json`, `week4_improved_model/config.json`, `cross-encoder-quora/config.json`, and `e5-quora-finetuned/config.json` all specify `transformers_version: "5.13.0"`. This is the most concerning artifact issue — no public transformers release has version 5.x. The latest is 4.49.0.

This could mean:
- The training environment used a custom/forked transformers build
- The version tagging is inaccurate
- Loading with standard transformers 4.x may fail or produce warnings

### Issue 4: No ONNX or TorchScript exports
Zero ONNX files. Zero TorchScript files. All inference is eager-mode PyTorch behind safetensors.

### Issue 5: Training checkpoints retain optimizer states
Three checkpoints in `transformer_training_outputs/` each contain 511 MB `optimizer.pt` files. These are full training resume checkpoints, not trimmed inference exports. The `pytorch_model.bin`/`model.safetensors` from these checkpoints are usable for inference but the directories are 3x larger than necessary.
