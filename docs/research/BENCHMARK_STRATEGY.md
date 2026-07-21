# Benchmark Strategy for ARES: Beyond Accuracy

## Benchmark Philosophy

ARES rejects the reduction of system quality to a single accuracy number. In production duplicate detection, stakeholders care about whether the system is **fast enough**, **calibrated enough**, **explainable enough**, **robust enough**, and **cheap enough** — not just whether it achieves the highest F1 score on a held-out set.

Our benchmark philosophy is **multi-dimensional fitness assessment**. We define 12 evaluation dimensions, each with its own rationale, metric, measurement protocol, and existing system capability. The goal is not a single leaderboard but a **12-axis radar profile** that reveals the system's strengths, weaknesses, and trade-offs.

---

## Dimension 1: Accuracy

### Rationale
Accuracy remains the foundational dimension. It measures whether the system assigns the correct binary label (duplicate vs. non-duplicate). Without baseline accuracy, all other dimensions are moot.

### Metrics
- **F1 score**: primary metric (harmonic mean of precision and recall).
- **Precision**: TP / (TP + FP). Measures false positive cost.
- **Recall**: TP / (TP + FN). Measures false negative cost.
- **ROC-AUC**: area under the ROC curve. Threshold-independent measure.
- **PR-AUC**: area under precision-recall curve. Informative under class imbalance.

### Measurement Protocol
1. Load the QQP test split (or held-out dataset).
2. For each model in the registry, predict on all pairs.
3. Compute metrics via `_evaluation/metrics.py:evaluate_model()`.
4. Report with 95% bootstrap confidence intervals.

### Existing System Capability
- Full implementation in `_evaluation/metrics.py:evaluate_model()`.
- Per-model accuracy metadata tracked in `_models/registry.py:ModelRegistryEntry.accuracy` and `f1_score`.
- Model comparison table via `compare_models()` in `_evaluation/metrics.py`.

---

## Dimension 2: Latency

### Rationale
In real-world deployment, users expect sub-second responses. Latency determines whether the system can serve interactive traffic or must be restricted to batch/offline use.

### Metrics
- **p50 inference time**: median latency (milliseconds).
- **p95 inference time**: 95th percentile — captures tail latency under load.
- **p99 inference time**: 99th percentile — captures worst-case behaviour.
- **Component breakdown**: preprocessing, embedding, cross-encoder, ensemble aggregation.

### Measurement Protocol
1. Warm up all caches (run 10 sample predictions).
2. Execute 1,000 individual predictions, measuring wall-clock time per prediction.
3. Report percentiles. Include breakdown by model type.
4. Measure with cold cache (first prediction) and warm cache (steady-state).

### Existing System Capability
- Instrumentation via `time.perf_counter()` in `_inference/optimizer.py:benchmark_inference()`.
- Latency tracking per model vote in `_ensemble/agreement.py:ModelVote.latency_ms`.
- Latency aggregator in `_explainability/agreement_dashboard.py:ModelLeaderboard.by_speed`.

---

## Dimension 3: Calibration

### Rationale
A system that predicts "duplicate" with 90% confidence should be correct roughly 90% of the time. Calibration measures the alignment between predicted confidence and empirical accuracy. Poor calibration undermines trust and makes threshold tuning unreliable.

### Metrics
- **ECE (Expected Calibration Error)**: primary metric. Lower is better.
- **MCE (Maximum Calibration Error)**: worst-case bin misalignment.
- **Brier Score**: mean squared error of probabilities vs. binary labels.
- **NLL (Negative Log Likelihood)**: proper scoring rule.

### Measurement Protocol
1. Collect all predicted probabilities from the test set.
2. Bin probabilities into 10 equal-width bins [0–0.1, 0.1–0.2, ..., 0.9–1.0].
3. For each bin, compute accuracy and mean predicted probability.
4. ECE = Σ bin<sub>size</sub> · |bin<sub>acc</sub> − bin<sub>conf</sub>| / N.
5. Generate reliability diagram (calibration curve).
6. Repeat before and after calibration (temperature, Platt, isotonic).

### Existing System Capability
- ECE, MCE, Brier, NLL implemented in `_calibration/v2.py:evaluate_calibration()`.
- Three calibration methods: `temperature_scale`, `platt_scale`, `isotonic_regression`.
- Automatic best-method selection via `select_best_calibration()`.
- Calibration curve data via `get_calibration_curve_data()`.
- Plotting in `_evaluation/metrics.py:plot_calibration_curve()`.

---

## Dimension 4: Explainability

### Rationale
Users and auditors need to understand *why* a prediction was made. Explainability builds trust, enables debugging, and is increasingly required for regulatory compliance.

### Metrics
- **Trace completeness**: fraction of 9 per-model scores populated (tfidf, bge, e5, mpnet, cross-encoder, w3, w4, lr, svm). Target: ≥ 90%.
- **Feature attribution faithfulness**: rank correlation between feature importance and ablation impact (future work).
- **Human evaluation score**: domain experts rate trace quality on a Likert scale (future work).

### Measurement Protocol
1. For a random sample of 200 test pairs, generate `DecisionTrace` objects via `_explainability/trace.py:generate_decision_trace()`.
2. Compute trace completeness as (populated fields / total fields).
3. For false positives and false negatives, verify that the trace explains the error (the relevant feature is present and weighted appropriately).

### Existing System Capability
- `DecisionTrace` dataclass in `_explainability/trace.py` with 30+ fields covering per-model scores, lexical features, semantic features, adaptive weights, agreement metrics.
- `generate_decision_trace()` is the main entry point.
- Feature extraction: `extract_lexical_features()`, `extract_semantic_features()`.
- Agreement dashboard: `analyze_model_agreement()` in `_explainability/agreement_dashboard.py`.

---

## Dimension 5: Robustness

### Rationale
Real-world questions contain typos, abbreviations, synonyms, and variations unseen during training. Robustness measures the system's ability to maintain accuracy under input perturbations.

### Metrics
- **Accuracy on adversarial pairs**: synthetically constructed hard examples.
- **Typo tolerance**: F1 on pairs where one question contains introduced typos (Levenshtein distance 1–3).
- **Abbreviation handling**: F1 on pairs where one question uses abbreviations (e.g., "NLP" vs. "Natural Language Processing").
- **Synonym robustness**: F1 on pairs where core terms are replaced with synonyms.

### Measurement Protocol
1. Build adversarial test sets by applying transformations to QQP test pairs:
   - Typo injection: randomly perturb 1–3 characters in one question.
   - Abbreviation substitution: replace known terms with abbreviations.
   - Synonym substitution: replace content words with WordNet synonyms.
2. Evaluate the system on each transformed set.
3. Report ΔF1 = F1<sub>adversarial</sub> − F1<sub>original</sub>.

### Existing System Capability
- Abbreviation detection: `_ensemble/v1.py:_detect_abbreviations()`.
- Synonym detection: `_ensemble/v1.py:_detect_synonyms()`, synonym pairs in `_synonym_pairs` table.
- Preprocessing expands known abbreviations: `_preprocessing/`.
- Error categorisation labels abbreviation and synonym failures: `_evaluation/error_analysis.py`.

---

## Dimension 6: Cost

### Rationale
Each prediction consumes compute resources. Cost determines economic viability at scale.

### Metrics
- **Compute cost per prediction**: estimated as (latency × compute unit cost). Reported in micro-dollars (µ$).
- **Memory footprint**: peak RAM usage during inference (MB).
- **Model size**: disk footprint (MB per model).
- **Energy per prediction**: estimated using RAPL or TDP (mJ per prediction).

### Measurement Protocol
1. Use `sys.getsizeof()` or `psutil` to measure peak memory during a batch of 100 inferences.
2. Compute per-model disk size using directory traversal in `_models/registry.py:_get_directory_size_mb()`.
3. Estimate energy using CPU TDP × runtime.

### Existing System Capability
- Model size tracking: `_models/registry.py:ModelRegistryEntry.size_mb`.
- Latency tracking: `ModelVote.latency_ms`.
- Cache statistics: `get_cache_stats()` in `_ensemble/v2.py`.

---

## Dimension 7: Trust

### Rationale
Trust is the user's subjective confidence that the system behaves appropriately. It is operationalised through agreement signals, calibration honesty, and contradiction awareness.

### Metrics
- **Agreement score**: fraction of models agreeing with the final prediction (0.0–1.0). Higher = more trustworthy.
- **Confidence calibration**: ECE as a measure of whether stated confidence matches empirical accuracy.
- **Contradiction awareness**: for pairs flagged as contradictory by the contradiction engine, what fraction are correctly predicted as non-duplicate?
- **Graceful uncertainty**: for borderline predictions (probability 0.4–0.6), does the system explicitly signal low confidence?

### Measurement Protocol
1. For each test pair, compute `AgreementDashboard` via `_explainability/agreement_dashboard.py:analyze_model_agreement()`.
2. For high-agreement predictions (>80%), verify accuracy exceeds 95%.
3. For low-agreement predictions (<50%), verify the confidence mean is appropriately low (<0.7).
4. For contradictory pairs, verify the ensemble penalty reduces the duplicate probability below 0.5.

### Existing System Capability
- Agreement analysis: `_ensemble/agreement.py`, `_explainability/agreement_dashboard.py`.
- Contradiction detection: `_linguistics/contradiction.py`.
- Borderline detection: `is_borderline` flag in `EnsembleFeatures` and `AgreementReport`.
- Confidence signalling: `DecisionTrace.confidence`, `AgreementReport.confidence_mean`.

---

## Dimension 8: Generalisation

### Rationale
A system that performs well on QQP but fails on other datasets or languages has limited scientific value. Generalisation measures cross-domain transfer.

### Metrics
- **Cross-dataset F1**: train on QQP, evaluate on StackExchange, WikiQA, or other question pair datasets.
- **Cross-domain F1**: F1 on question pairs from programming, medicine, finance, or other specialised domains.
- **Cross-language transfer**: zero-shot performance on non-English question pairs using multilingual embeddings.

### Measurement Protocol
1. Load a non-QQP dataset with identical binary duplicate labels.
2. Run the full ARES pipeline (all models + ensemble) without any fine-tuning.
3. Report ΔF1 = F1<sub>target</sub> − F1<sub>QQP</sub>.
4. Analyse which models generalise best (typically the bi-encoders from HuggingFace).

### Existing System Capability
- Dataset configuration: `configs/dataset.yaml` supports multiple dataset paths.
- Model registry includes general-purpose HuggingFace models (BGE, E5, MPNet, DeBERTa).
- Transformation inference service in `_inference/transformer.py` operates on arbitrary text pairs.

---

## Dimension 9: Energy

### Rationale
Energy consumption is an increasingly important sustainability metric for NLP systems.

### Metrics
- **Energy per prediction**: millijoules (mJ) per inference.
- **Energy per F1 point**: normalised metric = total energy / F1 score.
- **CO₂ per 1M predictions**: grams CO₂ using regional grid intensity.

### Measurement Protocol
1. Use `codecarbon` or `intel-rapl` to measure energy during benchmark execution.
2. Record energy per prediction as total energy / number of predictions.
3. Compare across model types (TF-IDF is near zero; DeBERTa is most expensive).

### Existing System Capability
No dedicated energy measurement module yet. The latency and model size infrastructure (`_inference/optimizer.py`, `_models/registry.py`) provides the inputs needed for energy estimation via TDP × runtime.

---

## Dimension 10: Memory & Caching

### Rationale
Memory constraints affect deployment on edge devices, serverless functions, and shared infrastructure. Efficient caching reduces redundant computation.

### Metrics
- **Cache hit rate**: fraction of embedding and preprocessing lookups served from cache.
- **Memory usage**: peak RAM during inference (MB).
- **Model load time**: time to load each model from disk (seconds).
- **Cache eviction rate**: items evicted from LRU cache per 1K predictions.

### Measurement Protocol
1. Run a sequence of 1,000 predictions with increasing overlap (duplicate questions appear multiple times).
2. Track cache hits/misses via `LRUCache.stats()` from `_inference/cache.py`.
3. Measure model load time via `ModelLoader.get_load_time()`.
4. Report steady-state memory usage after warm-up.

### Existing System Capability
- LRU cache with hit/miss/eviction tracking: `_inference/cache.py:LRUCache`.
- Embedding cache: `EmbeddingCache` in `_inference/optimizer.py` (10K entries max).
- Preprocessing cache: `PreprocessingCache` (10K entries max).
- Cache statistics: `CacheManager.stats()`, `get_cache_stats()`.

---

## Dimension 11: Failure Recovery

### Rationale
No system is perfect. Failure recovery measures the system's ability to detect when it cannot make a reliable prediction and to degrade gracefully.

### Metrics
- **Detection rate of low-confidence predictions**: fraction of errors where confidence is below a threshold (e.g., <0.7) and the system can flag them.
- **Abstention precision**: when the system abstains (refuses to predict), what fraction of those would have been errors?
- **Graceful fallback accuracy**: when a primary model fails, what is the accuracy of the backup model?

### Measurement Protocol
1. Define an abstention policy: abstain if ensemble agreement < 60% or confidence < 0.6.
2. Measure the fraction of errors that would be caught.
3. Measure the false abstention rate (correct predictions that would be rejected).

### Existing System Capability
- Borderline detection: `is_borderline` in `EnsembleFeatures` and `AgreementReport`.
- Model disagreement: `agreement_score` in `AgreementReport`.
- Error detection during inference: `ModelVote.error` captures per-model failures.
- Graceful degradation: if the ensemble fails, fall back to trimmed mean (`_explainability/trace.py` line 351–358).

---

## Dimension 12: Agreement

### Rationale
Inter-model agreement is a proxy for prediction reliability. When all models agree, the prediction is likely correct. When models disagree, additional scrutiny is warranted.

### Metrics
- **Agreement-accuracy correlation**: Pearson r between agreement score and correctness.
- **Unanimous prediction accuracy**: accuracy on pairs where all models agree.
- **Split vote accuracy**: accuracy on pairs where the vote is evenly split.
- **Pairwise agreement matrix**: K × K matrix of inter-model agreement rates (K = number of models).
- **Model leaderboard**: models ranked by agreement with ensemble, accuracy, calibration, speed, and influence.

### Measurement Protocol
1. For each test pair, compute `AgreementReport` via `_ensemble/agreement.py:analyze_agreement()`.
2. Aggregate across the entire test set to compute agreement-accuracy correlation.
3. Identify the most and least agreeable models.
4. Generate heatmap of pairwise agreement.

### Existing System Capability
- Full agreement pipeline: `collect_all_votes()` → `analyze_agreement()` → `AgreementReport`.
- Agreement dashboard: `analyze_model_agreement()` with agreement %, confidence stats, entropy, variance.
- Model leaderboard: `compute_model_leaderboard()` with 6 ranking criteria.
- Agreement summary: `generate_agreement_summary()` with natural-language interpretation.
- Visualisation: `agreement_dashboard.py` provides all structured data for plotting.

---

## Summary: 12-Axis Benchmark Profile

| Dimension | Primary Metric | Module | Status |
|---|---|---|---|
| Accuracy | F1, ROC-AUC | `_evaluation/metrics.py` | ✅ Full |
| Latency | p50/p95/p99 (ms) | `_inference/optimizer.py` | ✅ Full |
| Calibration | ECE, Brier | `_calibration/v2.py` | ✅ Full |
| Explainability | Trace completeness | `_explainability/trace.py` | ✅ Full |
| Robustness | ΔF1 adversarial | (adversarial sets needed) | ⚠️ Partial |
| Cost | µ$ per prediction | `_models/registry.py` | ⚠️ Partial |
| Trust | Agreement-accuracy r | `_ensemble/agreement.py` | ✅ Full |
| Generalisation | ΔF1 cross-dataset | `configs/dataset.yaml` | ⚠️ Planned |
| Energy | mJ per prediction | (new module needed) | ❌ Planned |
| Memory | Cache hit rate | `_inference/cache.py` | ✅ Full |
| Failure Recovery | Abstention F1 | `_ensemble/agreement.py` | ⚠️ Partial |
| Agreement | Pairwise agreement matrix | `_explainability/agreement_dashboard.py` | ✅ Full |

---

## Benchmark Execution Protocol

### Standard Benchmark Run

```bash
# 1. Run full evaluation on all models
python -m duplicate_question_app._evaluation.metrics \
  --dataset qqp_test \
  --output /tmp/ares_benchmark

# 2. Generate comparison report
# Output: metrics JSON, ROC/PR/calibration plots, error analysis, agreement matrix
```

### Benchmark Report Structure

```
benchmark/
├── metadata.yaml              # Seed, environment, timestamps
├── dimensions/
│   ├── accuracy.json          # Per-model F1, PR-AUC, ROC-AUC
│   ├── latency.json           # p50/p95/p99 per model
│   ├── calibration.json       # ECE, MCE, Brier per model
│   ├── agreement.json         # Agreement matrix, leaderboard
│   ├── explainability.json    # Trace completeness stats
│   └── ...
├── plots/
│   ├── roc_comparison.png
│   ├── pr_comparison.png
│   ├── calibration_comparison.png
│   ├── latency_breakdown.png
│   ├── agreement_heatmap.png
│   └── radar_profile.png      # 12-axis radar chart
├── artifacts/
│   ├── hard_examples.json
│   ├── decision_traces.json
│   └── error_categories.json
└── summary.md                 # Human-readable report
```
