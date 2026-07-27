# Model Truth Audit — Phase 11.0

**Date:** 2026-07-25
**Status:** Investigation Only (no fixes applied)
**Goal:** Discover the truth about every prediction model — identity, loading, preprocessing, label mapping, thresholds, confidence, known problems.

---

## 1. Model Inventory (11 Entries)

| # | Internal ID | Display Name | Backend | Artifact Status | Family |
|---|-------------|-------------|---------|----------------|--------|
| 1 | `week2_lr` | TF-IDF + Logistic Regression (Week 2) | CLASSICAL_ML | ✅ READY | TFIDF |
| 2 | `week2_svm` | TF-IDF + Linear SVM (Week 2) | CLASSICAL_ML | ✅ READY | TFIDF |
| 3 | `week3` | DistilBERT (Week 3) | TRANSFORMER | ✅ READY | DISTILBERT |
| 4 | `week4` | Improved DistilBERT (Week 4) | TRANSFORMER | ✅ READY | DISTILBERT |
| 5 | `bge` | BGE-base-en-v1.5 | BI_ENCODER | ⚠️ AUTO-DOWNLOAD | BGE |
| 6 | `e5` | E5-base-v2 | BI_ENCODER | ⚠️ AUTO-DOWNLOAD | E5 |
| 7 | `e5_ft` | E5-quora-finetuned | BI_ENCODER | ✅ READY | E5 |
| 8 | `mpnet` | MPNet-base-v2 | BI_ENCODER | ⚠️ AUTO-DOWNLOAD | MPNET |
| 9 | `deberta` | DeBERTa-v3 Cross-Encoder | CROSS_ENCODER | ⚠️ AUTO-DOWNLOAD | DEBERTA |
| 10 | `ce_quora` | Cross-Encoder-Quora (Trained) | CROSS_ENCODER | ✅ READY | CROSS_ENCODER_QUORA |
| 11 | `ensemble` | Semantic Ensemble | ENSEMBLE | ✅ BUILT-IN | ENSEMBLE |

---

## 2. Model-by-Model Truth Assessment

### 2.1 Week 2 Classical Models (`week2_lr`, `week2_svm`)

**Artifacts on disk:**
- `models/week2_models/logistic_regression.joblib` — LogisticRegression, coef_.shape=(1,10000), C=1.0
- `models/week2_models/linear_svm.joblib` — LinearSVC, coef_.shape=(1,10000), C=1.0
- `models/week2_models/tfidf_vectorizer.joblib` — TfidfVectorizer, max_features=5000, vocab_size=5000

**Loading:** ✅ Works. Both models and vectorizer load from the `week2_models/` directory.

**Preprocessing:** `normalize_question()` is applied to both questions, then concatenated with a space (`q1_norm + " " + q2_norm`) before TF-IDF transform.

**Label mapping:** {0: "Non-Duplicate", 1: "Duplicate"} — hardcoded in `InferenceDispatcher._label_mapping`.

**Threshold:** Uses `default_threshold: 0.5` from `inference.yaml` (no per-model override for week2 models).

**Known problems:**
- LinearSVC does NOT have `predict_proba()` — the dispatcher falls back to Platt scaling via `decision_function()` + sigmoid, which is an approximation, not true probability calibration.
- The SVM's probability estimates are unreliable.
- The TF-IDF vectorizer uses max_features=5000 but the model has 10000 coefficients — this is because the combined text `q1 + " " + q2` produces more n-gram features than would be expected from single questions.
- **DISCREPANCY:** Training notebook (`baseline_model.ipynb`) likely used a different vectorizer configuration than what the registry describes. Need to verify the notebook to confirm.

### 2.2 DistilBERT Week 3 (`week3`)

**Artifacts on disk:**
- `models/saved_transformer_model/config.json` — DistilBertForSequenceClassification, 66.9M params
- `models/saved_transformer_model/model.safetensors` — 256MB

**Loading:** ✅ Loads via `AutoModelForSequenceClassification.from_pretrained()`.

**Preprocessing:** `normalize_question()` with `expand_abbrevs=True, fix_typos=True`. Tokenizer auto-loaded from model directory.

**Label mapping:** {0: "Non-Duplicate", 1: "Duplicate"} — NOT in config.json (no `id2label` field). Relies entirely on the hardcoded mapping in `InferenceDispatcher._label_mapping`. This is a **consistency risk** — if the model was trained with reversed labels (0=duplicate, 1=non-duplicate), predictions would be inverted.

**Threshold:** `default_threshold: 0.5` (no per-model override).

**Confidence:** Uses `max(prob_non, prob_dup)` — raw softmax confidence.

**Known problems:**
- ❌ **No `id2label` in config.json** — label order is assumed [non-duplicate, duplicate] but never verified against training.
- Week 3 notebook (`transformer_model.ipynb`) training details not fully auditable from config alone.
- Model has `transformers_version: 5.13.0` which is old (actual env likely newer) — config loading still works forward-compatibly.

### 2.3 Improved DistilBERT Week 4 (`week4`)

**Artifacts on disk:**
- `models/week4_improved_model/config.json` — identical architecture to Week 3
- `models/week4_improved_model/model.safetensors` — 256MB

**Loading:** ✅ Same as Week 3.

**Preprocessing:** Same as Week 3.

**Label mapping:** SAME issue as Week 3 — no `id2label` in config.json.

**Threshold:** `default_threshold: 0.5` — BUT the Week 4 notebook performed threshold tuning as part of the improvement. The tuned threshold was NOT captured in `inference.yaml`. This means the "Improved" DistilBERT uses the same default threshold as the non-improved one.

**Known problems:**
- ❌ Same label mapping risk as Week 3.
- ❌ **Tuned threshold from training not captured** — the threshold tuning from Week 4's ablation study was lost. The config still says 0.5 for both week3 and week4.
- The config says `recommended_use: "When Week 3 is too conservative; tuned threshold needed"` but no tuned threshold is configured.

### 2.4 BGE-base-en-v1.5 (`bge`)

**Artifacts on disk:**
- `models/bge_base_en_v1_5/` — ❌ **DOES NOT EXIST** (config path but dir missing)
- Hub name: `BAAI/bge-base-en-v1.5`
- `models/bge_lr_head.pkl` — exists (13147 bytes)

**Loading:** ⚠️ Auto-downloads from HuggingFace on first use. Registry reports status=`DOWNLOADING` if cached, else `MISSING`.

**Preprocessing:** `normalize_question()` with `expand_abbrevs=True, fix_typos=True`. No E5 prefix (not an E5 model).

**Label mapping:** {0: "Non-Duplicate", 1: "Duplicate"}.

**Threshold:** `"BGE-base-en-v1.5": 0.30` from `inference.yaml`.

**Confidence:** Sigmoid calibration: `steepness=15.6755, midpoint=0.8591`. Applied to cosine similarity.

**LR head:** Available at `models/bge_lr_head.pkl` — LogisticRegression with C=10.0, 42 iterations. **BUT this is a separate prediction path** (classifier_head.py: `predict_with_lr()`). The dispatcher (`_predict_bi_encoder`) uses cosine similarity + sigmoid, NOT the LR head. The LR head operates on concatenated embedding features [emb1, emb2, |emb1-emb2|, emb1*emb2] (3072-dim). These two paths produce different predictions.

**Known problems:**
- ❌ **LR head for BGE and MPNet are THE SAME FILE.** `bge_lr_head.pkl` and `all_mpnet_base_v2_lr_head.pkl` have the same md5 hash (36d74bca8f1383ebc2160e176b600444), same file size (13147 bytes), same coefficients and intercept. This means one is a literal copy of the other — the MPNet LR head was never trained on MPNet embeddings.
- ❌ **Local model directory doesn't exist** — first inference will trigger a download (~1.4GB).
- Influential parameters "BGE-quora-finetuned" exist in `inference.yaml` but the corresponding model directory `models/bge-quora-finetuned/` does NOT exist.

### 2.5 E5-base-v2 (`e5`)

**Artifacts on disk:**
- `models/e5_base_v2/` — ❌ **DOES NOT EXIST**
- Hub name: `intfloat/e5-base-v2`
- `models/e5_base_v2_lr_head.pkl` — exists (13147 bytes, **different** from BGE/MPNet)

**Loading:** ⚠️ Auto-downloads from HuggingFace.

**Preprocessing:** `normalize_question()` + E5-specific prefix: `"query: {q1_norm}"`, `"passage: {q2_norm}"`. This is critical — the dispatcher uses `use_e5_prefix=True` when "e5" is in `internal_id`.

**Threshold:** `"E5-base-v2": 0.35` from `inference.yaml`.

**Confidence:** Sigmoid calibration: `steepness=8.0, midpoint=0.82`.

**LR head:** Actually trained: C=100.0, 65 iterations, coef_.shape=(1,3072). This is the real deal.

**Known problems:**
- ❌ Local model directory doesn't exist — first inference downloads.
- The E5 prefix requirement means the LR head prediction path (classifier_head.py) must also use prefixes. It does (`is_e5` check), but this is a subtle duplication of logic between dispatcher and classifier_head.

### 2.6 E5-quora-finetuned (`e5_ft`)

**Artifacts on disk:**
- `models/e5-quora-finetuned/config.json` — BertModel architecture (underlying BERT)
- `models/e5-quora-finetuned/model.safetensors` — exists (trained weights)
- `models/e5-quora-finetuned/1_Pooling/config.json` — mean pooling, embed_dim=768

**Loading:** ✅ Loads from local directory via SentenceTransformer.

**Training:** Actually trained via `tools/train_e5_quora.py` using MultipleNegativesRankingLoss with query/passage prefixes. Up to 200K training samples, up to 3 epochs.

**Preprocessing:** Same E5 prefix approach as base E5.

**Threshold:** `"E5-quora-finetuned": 0.40` from `inference.yaml`.

**Confidence:** Sigmoid calibration: `steepness=10.0, midpoint=0.73`.

**Known problems:**
- No LR head exists specifically for the fine-tuned E5 — only the base E5 has one.
- The fine-tuning script trains on BERT architecture but the base model is SentenceTransformer. The saved model preserves the SentenceTransformer structure (including 1_Pooling/).
- Training outputs directory (`outputs/`) doesn't exist, so training metrics are lost.

### 2.7 MPNet-base-v2 (`mpnet`)

**Artifacts on disk:**
- `models/mpnet_base_v2/` — ❌ **DOES NOT EXIST**
- Hub name: `sentence-transformers/all-mpnet-base-v2`
- `models/all_mpnet_base_v2_lr_head.pkl` — exists (13147 bytes)

**Loading:** ⚠️ Auto-downloads from HuggingFace.

**Preprocessing:** `normalize_question()` — no prefix.

**Threshold:** `"MPNet-base-v2": 0.36` from `inference.yaml`.

**Confidence:** Sigmoid calibration: `steepness=11.5976, midpoint=0.8133`.

**Known problems:**
- ❌ **LR head is a COPY of BGE's LR head.** `all_mpnet_base_v2_lr_head.pkl` is byte-for-byte identical to `bge_lr_head.pkl`. This means the MPNet LR head has BGE weights, not MPNet weights. Predictions via `predict_with_lr("sentence-transformers/all-mpnet-base-v2")` are actually BGE-based predictions.
- ❌ Local model directory doesn't exist.

### 2.8 DeBERTa-v3 Cross-Encoder (`deberta`)

**Artifacts on disk:**
- `models/deberta_v3_cross_encoder/` — ❌ **DOES NOT EXIST**

**Loading:** ⚠️ Auto-downloads from HuggingFace.

**Preprocessing:** `normalize_question()` with `expand_abbrevs=True, fix_typos=True`.

**Special behavior:** Returns 3 scores [contradiction, neutral, entailment]. The dispatcher computes `prob_dup = entailment / (contradiction + entailment)` (entailment ratio). This is an NLI model, not a duplicate detection model.

**Threshold:** No per-model threshold configured — uses `default_threshold: 0.5`.

**Confidence:** Derived from entailment ratio.

**Known problems:**
- ❌ **Not trained for duplicate detection.** This is an NLI (natural language inference) model. Using entailment ratio for duplicate detection is a clever heuristic but not validated against Quora data.
- ❌ Local model directory doesn't exist — 1.4GB download on first use.
- The registry claims `recommended_use: "When accuracy is critical; works best in ensemble"` but the NLI→duplicate mapping has never been validated.

### 2.9 Cross-Encoder-Quora Trained (`ce_quora`)

**Artifacts on disk:**
- `models/cross-encoder-quora/config.json` — DebertaV2ForSequenceClassification, 184M params
- `models/cross-encoder-quora/model.safetensors` — **737MB** (largest artifact)

**Loading:** ✅ Loads from local directory via CrossEncoder.

**Training:** Actually trained via `tools/train_cross_encoder.py` — fine-tunes `microsoft/deberta-v3-base` on Quora pairs with 2 labels. Uses class-weighted loss (handles imbalance). Training script has early stopping, optimal threshold grid search.

**Preprocessing:** `normalize_question()` with `expand_abbrevs=True`.

**Threshold:** `"Cross-Encoder-Quora (Trained)": 0.10` from `inference.yaml`. This is extremely low.

**Confidence:** Returns 2 scores (softmax over 2 classes). `prob_dup = scores[1]`.

**Known problems:**
- ❌ **Threshold of 0.10 seems wrong.** The training script finds optimal thresholds via grid search over [0.1, 0.9]. The found threshold should be higher (typically 0.4-0.6). A threshold of 0.10 means almost everything gets classified as "duplicate", which would produce very high recall but very low precision. This needs investigation.
- ❌ The training script saves results to `outputs/embedding_models/cross_encoder_metrics.json` but `outputs/` doesn't exist, so the actual optimal threshold from training is lost.
- 737MB — slowest model to load.

### 2.10 Semantic Ensemble (`ensemble`)

**Loading:** Built-in. Doesn't load as a single model — routes through `FusionEngine`.

**Behavior:** Runs all available models and combines predictions with dynamic feature-based weighting and trimmed mean.

**Threshold:** No per-model threshold.

**Known problems:**
- ❌ Depends on ALL sub-models being loadable. If a HuggingFace model hasn't been downloaded yet, the ensemble will trigger multiple simultaneous downloads.
- The ensemble's quality is directly bounded by the worst sub-model.

---

## 3. Cross-Cutting Issues

### 3.1 Label Mapping (CRITICAL)

**All models** use the hardcoded `InferenceDispatcher._label_mapping = {0: "Non-Duplicate", 1: "Duplicate"}`. This is never verified against actual model training labels.

**Risk:** If any model was trained with reversed labels (common in HuggingFace: 0=positive, 1=negative), predictions would be inverted without any error signal.

**Evidence:**
- DistilBERT config.json files do NOT contain `id2label` field.
- Cross-Encoder config.json does NOT contain `id2label` field.
- The `training.yaml` says `num_labels: 2` but doesn't specify the label mapping.
- The `train_cross_encoder.py` uses `AutoModelForSequenceClassification.from_pretrained(..., num_labels=2)` which uses default label order [0, 1], and Quora labels are [0, 1] — so this is likely correct for the cross-encoder. But NOT verified for DistilBERT models.

⚠️ **This should be validated with test predictions.**

### 3.2 LR Head Duplication (CRITICAL)

| File | MD5 | Actual Content |
|------|-----|----------------|
| `e5_base_v2_lr_head.pkl` | `21a126c3...` | E5-trained LR (C=100.0, 65 iterations) |
| `bge_lr_head.pkl` | `36d74bca...` | BGE / MPNet-trained LR (C=10.0, 42 iterations) |
| `all_mpnet_base_v2_lr_head.pkl` | `36d74bca...` | **SAME as BGE** — binary identical copy |

**Impact:** `predict_with_lr("sentence-transformers/all-mpnet-base-v2")` uses BGE weights, producing MPNet-embeddings + BGE-classifier predictions. This is a mixture that may degrade accuracy.

### 3.3 Threshold Configuration

| Model | Configured Threshold | Source |
|-------|---------------------|--------|
| Week 2 LR | 0.5 (default) | inference.yaml |
| Week 2 SVM | 0.5 (default) | inference.yaml |
| Week 3 DistilBERT | 0.5 (default) | inference.yaml |
| Week 4 Improved DistilBERT | 0.5 (default) | ❌ **Tuned threshold not captured** |
| BGE-base-en-v1.5 | 0.30 | inference.yaml |
| E5-base-v2 | 0.35 | inference.yaml |
| E5-quora-finetuned | 0.40 | inference.yaml |
| MPNet-base-v2 | 0.36 | inference.yaml |
| DeBERTa-v3 Cross-Encoder | 0.5 (default) | inference.yaml |
| Cross-Encoder-Quora (Trained) | **0.10** | ❌ **Suspiciously low** |
| Semantic Ensemble | 0.5 (default) | inference.yaml |

### 3.4 Missing Artifacts / Phantom Paths

Paths referenced in configs that do NOT exist on disk:

| Config Path | Expected Location | Status |
|-------------|-------------------|--------|
| `paths.bge_model_dir` | `models/bge_base_en_v1_5/` | ❌ Missing (auto-download) |
| `paths.e5_model_dir` | `models/e5_base_v2/` | ❌ Missing (auto-download) |
| `paths.mpnet_model_dir` | `models/mpnet_base_v2/` | ❌ Missing (auto-download) |
| `paths.deberta_model_dir` | `models/deberta_v3_cross_encoder/` | ❌ Missing (auto-download) |
| `paths.finetuned_bge_dir` | `models/bge-quora-finetuned/` | ❌ Missing + referenced in inference.yaml thresholds |
| `paths.data_dir` | `data/` | ❌ Missing entirely |
| `paths.results_dir` | `outputs/` | ❌ Missing entirely |

### 3.5 Preprocessing Consistency

**Path:** `normalize_question()` in `src/duplicate_question_app/_preprocessing/text.py`

**Parameters used by dispatcher:**
- All backends: `expand_abbrevs=True, fix_typos=True`

**Note:** The `fix_typos=True` was added in a recent session but may not match the preprocessing used during training. The training scripts use `normalize_question(q, expand_abbrevs=True)` without `fix_typos=True`. This means **inference-time preprocessing differs from training-time preprocessing** for all Week2, Week3, and Week4 models (the courses models).

**Impact:** Predictions may differ slightly from training behavior due to additional typos fixing at inference time.

**LR head path (classifier_head.py)** also uses `expand_abbrevs=True` without `fix_typos=True` — so LR head predictions use yet another preprocessing variant.

### 3.6 `backends/` Directory

The `src/ares/inference/backends/` directory is EMPTY. The actual backend logic lives in `dispatcher.py` as private functions. This directory appears to be vestigial.

---

## 4. Training vs. Inference Discrepancies Summary

| Model | Trained With | Inference Preprocessing | Match? |
|-------|-------------|------------------------|--------|
| Week 2 LR/SVM | TF-IDF on combined text | Same + `fix_typos` | ⚠️ Slight mismatch |
| Week 3 DistilBERT | `transformer_model.ipynb` | `fix_typos` added at inference | ⚠️ Slight mismatch |
| Week 4 DistilBERT | `week4_improvement.ipynb` | `fix_typos` added at inference | ⚠️ Slight mismatch |
| Cross-Encoder-Quora | `train_cross_encoder.py` | Same | ✅ Match |
| E5-quora-finetuned | `train_e5_quora.py` | Same | ✅ Match |
| LR heads | `classifier_head.py` | Same (no `fix_typos`) | ✅ Match (but different from dispatcher!) |

---

## 5. Recommendations for Next Steps

1. **Verify label order** for DistilBERT models by running test inferences and checking if "Duplicate" pairs get high probability in index 1.
2. **Remove duplicate LR head** — replace `all_mpnet_base_v2_lr_head.pkl` with a properly trained MPNet version or delete it.
3. **Investigate Cross-Encoder threshold of 0.10** — likely a bug. Should be closer to 0.4 based on typical optimal thresholds from training.
4. **Capture Week 4's tuned threshold** — set `"Improved DistilBERT (Week 4)": <tuned_value>` in `inference.yaml`.
5. **Align preprocessing across all paths** — either add `fix_typos=True` everywhere or remove it everywhere.
6. **Clean up phantom config paths** — remove `"BGE-quora-finetuned"` thresholds from `inference.yaml` since the model doesn't exist.
7. **Decide which models to keep** — the primary model path is unclear with 11 models. Consider which 2-3 models are the true "production" path.
