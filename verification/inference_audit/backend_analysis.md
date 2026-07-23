# Backend Analysis — Complete

## Inference Backend Inventory

### Backend 1: HuggingFace Transformers (PyTorch)
**Files:** `_inference/transformer.py`, `ares/_engine.py`
**Dependency:** `transformers`, `torch`, `safetensors`
**Models served:** DistilBERT (Week 3), Improved DistilBERT (Week 4)
**Loading mechanism:**
```python
AutoModelForSequenceClassification.from_pretrained(local_path)
AutoTokenizer.from_pretrained(local_path)
```
**Inference:**
```python
with torch.no_grad():
    outputs = model(**inputs)
    probs = F.softmax(outputs.logits, dim=-1)
```
**Device:** Always CPU (hardcoded `_resolve_device()`)
**Batch size:** 32
**Max sequence length:** 128
**Strengths:** Reliable, well-tested, handles the two DistilBERT models correctly
**Weaknesses:** Does not support Phase 2 models; ignores `model_name` parameter when loading

### Backend 2: scikit-learn / joblib
**Files:** `_models/week2.py`
**Dependency:** `scikit-learn`, `joblib`, `scipy`
**Models served:** TF-IDF + Logistic Regression (Week 2), TF-IDF + Linear SVM (Week 2)
**Loading mechanism:**
```python
joblib.load("models/week2_models/tfidf_vectorizer.joblib")
joblib.load("models/week2_models/logistic_regression.joblib")
```
**Inference:**
```python
features = hstack([tfidf.transform([q1]), tfidf.transform([q2])])
probs = lr.predict_proba(features)  # or svm decision_function + sigmoid
```
**Device:** CPU only (scikit-learn)
**Strengths:** Fast, small footprint, well-tested
**Weaknesses:** Limited expressiveness (TF-IDF bag-of-words)

### Backend 3: sentence-transformers (SentenceTransformer)
**Files:** `_models/embeddings.py`, `_inference/optimizer.py`
**Dependency:** `sentence-transformers`, `torch`, `numpy`
**Models served:** BGE-base-en-v1.5, E5-base-v2, E5-quora-finetuned, MPNet-base-v2
**Loading mechanism:**
```python
SentenceTransformer("BAAI/bge-base-en-v1.5", device="cuda" if torch.cuda.is_available() else "cpu")
SentenceTransformer(local_path, device=...)  # for fine-tuned models
```
**Inference:**
```python
emb1 = model.encode(q1, normalize_embeddings=True, show_progress_bar=False)
emb2 = model.encode(q2, normalize_embeddings=True, show_progress_bar=False)
similarity = np.dot(emb1, emb2)  # cosine similarity (normalized vectors)
prob = 1 / (1 + np.exp(-steepness * (similarity - midpoint)))  # sigmoid calibration
```
**Device:** Auto-detected (CUDA if available, else CPU). Config says `auto_device: true` but `default_device: "cpu"`.
**Batch size:** 64 (embedding_inference), 256 (lr_head_inference)
**E5 prefixes:** Query: `"query: {text}"`, Passage: `"passage: {text}"`
**Strengths:** Rich semantic embeddings, GPU acceleration available, flexible
**Weaknesses:** Dual inference paths with different calibration values; LR heads not used in production

### Backend 4: sentence-transformers (CrossEncoder)
**Files:** `_models/embeddings.py`, `_inference/optimizer.py`
**Dependency:** `sentence-transformers`, `torch`
**Models served:** DeBERTa-v3 Cross-Encoder, Cross-Encoder-Quora (Trained)
**Loading mechanism:**
```python
CrossEncoder("cross-encoder/nli-deberta-v3-base", device=...)
CrossEncoder("models/cross-encoder-quora", device=...)  # local
```
**Inference (DeBERTa NLI):**
```python
scores = model.predict([(q1, q2)], apply_softmax=True)
# scores = [contradiction, neutral, entailment]
prob_dup = scores[2] / (scores[0] + scores[2])  # entail / (contra + entail)
```
**Inference (Cross-Encoder-Quora):**
```python
scores = model.predict([(q1, q2)], apply_softmax=True)
# scores = [non_duplicate_prob, duplicate_prob] (binary)
prob_dup = scores[1]
```
**Device:** Auto-detected
**Batch size:** 128 (cross_encoder_inference)
**Strengths:** State-of-the-art cross-encoder quality
**Weaknesses:** Slower than bi-encoders (quadratic); CE-Quora uses 0.10 threshold (very low); transformers_version mismatch

### Backend 5: Custom Ensemble
**Files:** `_ensemble/v1.py`, `_ensemble/v2.py`
**Dependency:** All above backends + `_linguistics` modules
**Models served:** Semantic Ensemble
**Inference:**
```python
# Collect votes from all 10 sub-models
# Compute 10 feature rules
# Assign adaptive weights
# Weighted probability → final decision
```
**Strengths:** Leverages all available models, robust to individual failures
**Weaknesses:** Complex, depends on all sub-models, can be slow

### Backend 6: ARES Reflection Engine
**Files:** `_reflection/reflection_engine.py`, `ares/_engine.py`
**Dependency:** Custom (no external ML framework)
**Models served:** Reflection layer (post-prediction)
**Inference:**
```python
ref = ReflectionEngine.reflect(prediction=raw_prediction)
# Runs 6 auditors, computes trust score (0-100), generates recommendations
```
**Strengths:** Adds trust scoring, risk assessment, human review flags
**Weaknesses:** Not integrated with Phase 2 models; trust score normalization needed (fixed in Phase 10.5.2)

## Dual Inference Path Problem

There are TWO separate inference paths for sentence-transformer models:

### Path A: Production (embeddings.py)
**Caller:** `app/utils/constants.py:get_model_prediction()`
**Sigmoid params:** From `configs/inference.yaml`:
| Model | Steepness | Midpoint |
|-------|-----------|----------|
| E5-quora-finetuned | 10.0 | 0.73 |
| E5-base-v2 | 8.0 | 0.82 |
| BGE-quora-finetuned | 12.0 | 0.88 |
| BGE-base-en-v1.5 | 15.6755 | 0.8591 |
| MPNet-base-v2 | 11.5976 | 0.8133 |

### Path B: Optimizer (optimizer.py)
**Caller:** `_inference/optimizer.py:InferenceOptimizer`
**Sigmoid params (hardcoded):**
| Model | Steepness | Midpoint |
|-------|-----------|----------|
| e5 | 18.0 | 0.72 |
| bge | 14.0 | 0.60 |
| mpnet | 14.0 | 0.58 |
| default | 15.0 | 0.50 |

**Result:** Same input produces different probabilities on Path A vs Path B. The optimizer path parameters appear to be initial/exploratory values while the embeddings.py path has validated parameters from evaluation.

## Device Strategy

| Loader | Strategy | Config | Actual |
|--------|----------|--------|--------|
| Transformer | `_resolve_device()` → always "cpu" | `default_device: "cpu"` | CPU |
| Week 2 | N/A (sklearn) | N/A | CPU |
| SentenceTransformer | `resolve_device()` → CUDA if available | `auto_device: true` | GPU if available |
| CrossEncoder | Same as SentenceTransformer | same | GPU if available |
| InferenceOptimizer | `resolve_device()` | same | GPU if available |
| ARES | CPU only | N/A | CPU |

## Dependency Summary

| Backend | Python Package | Required | Version |
|---------|---------------|----------|---------|
| HuggingFace Transformers | `transformers` | Yes | ^4.x (but saved models say 5.13.0) |
| PyTorch | `torch` | Yes | ^2.x |
| safetensors | `safetensors` | Yes (transitive) | — |
| scikit-learn | `scikit-learn` | Yes | ^1.x |
| joblib | `joblib` | Yes (transitive) | — |
| sentence-transformers | `sentence-transformers` | Yes | ^3.x |
| huggingface_hub | `huggingface_hub` | Yes (transitive) | — |
| numpy | `numpy` | Yes | — |
| scipy | `scipy` | Yes | — |
