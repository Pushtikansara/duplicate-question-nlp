# Model Failure Analysis — Phase 11.1

## Methodology

Each model was evaluated on n=5000 validation pairs from the Quora dataset.
For each model, false positives (FP) and false negatives (FN) were extracted
and categorized by failure type.

---

## Failure Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Paraphrase (FP)** | Different questions on same topic, not actually duplicates | "saddest suicide story" vs "saddest suicide/death stories" |
| **Paraphrase (FN)** | Same question, differently phrased | "which time can get pregnant" vs "when is she less likely" |
| **Entity/Abbreviation** | Questions differ on entity specifics | "Yahoo permanently" vs "disable Yahoo" |
| **Negation/Missing Modifier** | One question has extra restriction | "Jewish men" vs "white Jewish men" |
| **Numeric/Time Change** | Questions differ on numeric specifics | "lose 15 kilos" vs "lose 15 kilos in 5 months" |
| **Metaphorical/Philosophical** | Abstract or conceptual questions | "live in the matrix" vs "know we don't live in matrix" |
| **Reformulation (FN)** | Same intent, different structure | "how to calculate cash flow" vs "best ways to calculate" |
| **Lexical Overlap (FP)** | High word overlap but different intent | "help with Quora writing" vs "improve writing skills for Quora" |

---

## Model-by-Model Analysis

### 1. TF-IDF + Logistic Regression (Week 2)
**Status: BROKEN** — vectorizer dimension mismatch (5000 → 10000)
Cannot evaluate.

### 2. TF-IDF + Linear SVM (Week 2)
**Status: BROKEN** — same dimension mismatch
Cannot evaluate.

### 3. DistilBERT (Week 3) — F1=0.8967
- **FP Count:** 324 (6.5% of predictions)
- **FN Count:** 75 (1.5% of predictions)
- **Common FP patterns:** High lexical overlap pairs where one question has additional qualifiers. The model is biased toward predicting "duplicate" when word overlap is high.
  - "saddest suicide story" vs "saddest suicide/death stories" (prob=0.993)
  - "delete Yahoo permanently" vs "disable Yahoo" (prob=0.930)
  - "hack WhatsApp message" vs "hack whatsapp messages" (prob=0.997)
- **Common FN patterns:** Reformulation pairs where key words are synonyms rather than exact matches.
  - "which time can get pregnant" vs "when is she less likely" (prob=0.393)
  - "favorite romantic comedy" vs "good romantic comedy movies" (prob=0.153)
  - "Jewish men" vs "white Jewish men" (prob=0.037) — **missing modifier**

### 4. Improved DistilBERT (Week 4) — F1=0.9539
- **FP Count:** 121 (2.4% of predictions) — **75% fewer FP than Week 3**
- **FN Count:** 49 (1.0% of predictions) — **35% fewer FN than Week 3**
- **Common FP patterns:** Similar to Week 3 but much reduced. Still confused by:
  - "saddest suicide story" vs "suicide/death stories" (prob=0.998)
  - "delete Yahoo permanently" vs "disable Yahoo" (prob=0.984)
- **Common FN patterns:** Still misses negations and reformulations:
  - "live in the matrix" vs "know we don't live in matrix" (prob=0.0004) — **metaphorical**
  - "calculate cash flow of company" vs "calculate operating cash flow" (prob=0.005)
  - "best weapon in Fallout 4" vs "get best weapons in Fallout 4" (prob=0.997, this is actually a FP, not FN)

### 5. BGE-base-en-v1.5 — F1=0.7290
- **FP Count:** 993 (19.9% of predictions) — high false positive rate
- **FN Count:** 201 (4.0% of predictions)
- The sigmoid calibration (steepness=15.68, midpoint=0.86) at threshold 0.30 makes it difficult to precisely separate duplicates from non-duplicates.
- **Best calibration of all bi-encoders** (ECE=0.0227) — calibrated confidence matches actual accuracy.

### 6. E5-base-v2 — F1=0.5611
- **FP Count:** 2827 (56.5% of predictions) — **CRITICAL: threshold too low**
- **FN Count:** 0 — predicted every pair as duplicate
- At threshold=0.35 with sigmoid (steepness=8.0, midpoint=0.82), almost all pairs have prob_dup > 0.35.
- **Optimal threshold would be much higher** (~0.8 based on midpoint).
- The model predicts everything as duplicate because the threshold is below the sigmoid midpoint.

### 7. E5-quora-finetuned — F1=0.7323
- **FP Count:** 1226 (24.5% of predictions)
- **FN Count:** 55 (1.1% of predictions)
- Fine-tuning improved recall (0.97 vs 1.0) but precision is still low (0.59).
- **High ECE (0.1317)** — confidence is not well-calibrated.
- The sigmoid params (steepness=10.0, midpoint=0.73) at threshold=0.40 mean the threshold is well below the sigmoid midpoint, producing many FPs.

### 8. MPNet-base-v2 — F1=0.7593
- **FP Count:** 786 (15.7% of predictions)
- **FN Count:** 220 (4.4% of predictions)
- **Best ECE of ALL models (0.0132)** — near-perfect calibration.
- Best bi-encoder overall: highest F1, best calibration, reasonable latency.
- Balanced trade-off between FP (moderate) and FN (moderate).

### 9. DeBERTa-v3 Cross-Encoder — F1=0.6287
- **FP Count:** 1877 (37.5% of predictions)
- **FN Count:** 118 (2.4% of predictions)
- **Worst ECE (0.3722)** — extreme miscalibration.
- The NLI→duplicate mapping (entailment ratio) is NOT effective for this task.
- The model is an NLI model, not trained for duplicate detection, and it shows.
- **High confidence in wrong predictions** (avg_confidence=0.964 but accuracy=0.601).

### 10. Cross-Encoder-Quora (Trained) — F1=0.8536
- **FP Count:** 507 (10.1% of predictions)
- **FN Count:** 84 (1.7% of predictions)
- Despite unusually low threshold (0.10), the model produces reasonable results because its probabilities for non-duplicates are very low.
- **Third-best model** after the two DistilBERT variants.
- Misses reformulation pairs: "What's on ISS for fun" vs "What do ISS astronauts do for leisure" (prob=0.041).

### 11. Semantic Ensemble
- **Status:** TIMEOUT — could not evaluate on full validation set.
- **Per-pair latency:** ~30s due to LRU model cache thrashing (MAX_CACHED_MODELS=3).
- Partial results on n=19: all correct except 1 FP.
- In production, the ensemble runs once per request with all models cached — timing is a benchmark artifact.

---

## Failure Distribution Summary

| Model | FP Rate | FN Rate | Primary Failure Mode |
|-------|---------|---------|---------------------|
| DistilBERT (Week 3) | 6.5% | 1.5% | Lexical overlap FP |
| Improved DistilBERT (Week 4) | **2.4%** | **1.0%** | Negation/missing modifier FN |
| BGE-base-en-v1.5 | 19.9% | 4.0% | Threshold too low (0.30) |
| E5-base-v2 | 56.5% | 0.0% | **Threshold critically low (0.35)** |
| E5-quora-finetuned | 24.5% | 1.1% | Threshold too low (0.40) |
| MPNet-base-v2 | 15.7% | 4.4% | Paraphrase FN with synonyms |
| DeBERTa-v3 Cross-Encoder | 37.5% | 2.4% | **NLI→duplicate mapping broken** |
| Cross-Encoder-Quora (Trained) | 10.1% | 1.7% | Reformulation FN |
| Semantic Ensemble | — | — | Timeout (cache thrashing) |

---

## Recommendations

1. **Primary production model:** Improved DistilBERT (Week 4) — lowest FP+FN combined
2. **Backup/second opinion:** Cross-Encoder-Quora (Trained) — different architecture, similar F1
3. **Best bi-encoder:** MPNet-base-v2 — best calibration, useful as feature extractor
4. **REMOVE:** Week 2 classical models (broken), E5-base-v2 (threshold untuned)
5. **RETRAIN or retune:** E5-base-v2 (needs appropriate threshold/sigmoid)
6. **Benchmark only:** BGE, E5-quora-finetuned, MPNet — useful for comparison but not primary
7. **Research only:** DeBERTa NLI cross-encoder (wrong task), Ensemble (too slow in batch)
