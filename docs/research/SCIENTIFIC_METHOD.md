# Scientific Methodology for Adaptive Reasoning Engine for Semantic Understanding (ARES)

## 1. Research Philosophy

ARES adopts a **critical rationalist** philosophy rooted in empirical AI research. The central tenet is that all claims about model performance, ensemble behaviour, and linguistic generalisation must be formulated as falsifiable hypotheses and subjected to rigorous empirical scrutiny. This mirrors the Popperian cycle of conjecture and refutation, adapted for the specific constraints of NLP systems research.

The philosophy manifests through four commitments:

- **Reproducible empiricism**: every experimental result must be independently verifiable via seeded randomness, versioned code, and published artifacts.
- **Comparative evaluation**: no claim of superiority is accepted without a controlled comparison against a well-defined baseline or ablative variant.
- **Mechanistic interpretability**: accuracy numbers alone are insufficient; every prediction must be decomposable into traceable contributions from constituent models, linguistic features, and ensemble logic.
- **Iterative falsification**: each experimental cycle is designed to reject a specific hypothesis, with negative results valued equally to positive ones as sources of scientific insight.

This philosophy is encoded directly in the codebase. The `_evaluation/` module (`src/duplicate_question_app/_evaluation/`) operationalises these commitments through structured metric computation, error analysis, and comparative report generation. The `_ensemble/v2.py` module embodies the adversarial relationship between hypothesis (dynamic routing rules) and evidence (feature values computed per input pair).

---

## 2. Hypothesis Formation

Hypotheses in ARES are derived from three sources: **(a)** theoretical analysis of the NLP duplicate detection task, **(b)** established results in ensemble learning and model calibration literature, and **(c)** observational patterns from error analysis of individual models.

### 2.1 Theory-Driven Hypotheses

Each linguistic penalty engine encodes a theoretical assumption about what features discriminate duplicate from non-duplicate question pairs:

| Hypothesis | Theoretical Basis | Module |
|---|---|---|
| H<sub>entity</sub>: Entity mismatch implies non-duplicate | Questions referencing different named entities cannot be semantically equivalent | `_linguistics/entity.py` |
| H<sub>negation</sub>: Negation polarity mismatch implies non-duplicate | A positively framed question and a negatively framed question have opposite intents | `_linguistics/negation.py` |
| H<sub>contradiction</sub>: Explicit contradiction implies non-duplicate | Opposing predicates (install vs. uninstall) indicate distinct information needs | `_linguistics/contradiction.py` |
| H<sub>intent</sub>: Different interrogative intent implies non-duplicate | "How to X" and "Why X" address fundamentally different questions | `_linguistics/intent.py` |
| H<sub>lexical</sub>: Low lexical overlap with high semantic similarity indicates paraphrase | TF-IDF models underperform on paraphrases; semantic models must be upweighted | `_linguistics/lexical.py` |

### 2.2 Data-Driven Hypotheses

Error analysis from `_evaluation/error_analysis.py` feeds directly into hypothesis generation. The `categorize_error` function identifies eight error types (abbreviation failure, synonym failure, negation mismatch, question type mismatch, entity mismatch, paraphrase, borderline, model disagreement). When a given error type exceeds a prevalence threshold (e.g., >10% of total errors), a targeted hypothesis is formulated:

> "If we introduce an abbreviation expansion pre-processing step, then the false negative rate on abbreviation-containing pairs will decrease by at least 30%."

### 2.3 Hypothesis Registry

Every active hypothesis is tracked in a structured format:

```json
{
  "id": "H-ENS-004",
  "description": "High lexical mismatch should downweight embedding models",
  "source": "theoretical",
  "module": "_ensemble/v2.py",
  "rule": "RULE 1: if lexical_overlap < 0.2, embed_w *= 0.5",
  "prediction": "ECE improves by ≥0.02 on low-overlap pairs",
  "status": "under_test"
}
```

---

## 3. Experimental Design

ARES employs a three-tier experimental design framework: **controlled experiments**, **ablation studies**, and **comparative evaluations**.

### 3.1 Controlled Experiments

Every experiment must specify:

- **Independent variable(s)**: the system component being manipulated (e.g., the number of models in the ensemble, the temperature parameter, the weight assigned to a linguistic penalty).
- **Dependent variable(s)**: the measured outcome (e.g., F1 score, ECE, p99 latency, agreement score).
- **Controlled variables**: all other system parameters held fixed across conditions. These include random seeds, model checkpoint versions, preprocessing pipelines, and evaluation dataset splits.

The `_config/` module provides a centralised configuration system (`settings.py`, `configs/*.yaml`) that enforces reproducibility by versioning all controllable parameters.

### 3.2 Ablation Studies

Ablation studies isolate the marginal contribution of each component:

1. **Linguistic penalty ablation**: One penalty engine at a time is disabled (penalty set to 0.0) while the ensemble operates normally. The delta in F1, ECE, and agreement is attributed to that engine.
2. **Model ablation**: Each of the 11 models is individually removed from the ensemble. The performance degradation quantifies that model's contribution.
3. **Dynamic weight ablation**: The adaptive routing (V2) is replaced with uniform weighting (all groups receive 0.25). The performance gap quantifies the value of dynamic routing.
4. **Calibration ablation**: Calibration is disabled (temperature=1.0, no Platt or isotonic regression). The change in ECE/MCE/Brier score quantifies calibration benefit.

Implementation: `_evaluation/metrics.py` provides the `compare_models` function that generates tabular comparisons across ablative conditions.

### 3.3 Comparative Evaluation

ARES benchmarks against three families of baselines:

- **Individual models**: each of the 10 non-ensemble models evaluated independently.
- **Static ensemble**: uniform-weighted average of all models (no dynamic routing, no linguistic penalties).
- **External baselines**: published results on the Quora Question Pairs (QQP) dataset from the literature.

The `generate_model_comparison_plots` function in `_evaluation/metrics.py` produces overlaid ROC curves, PR curves, and calibration curves for visual comparison across all conditions.

---

## 4. Measurement

### 4.1 Accuracy Metrics

- **F1 score**: harmonic mean of precision and recall, the primary accuracy metric.
- **Precision / Recall**: decomposed separately to analyse precision-recall trade-offs.
- **ROC-AUC**: area under the receiver operating characteristic curve.
- **PR-AUC**: area under the precision-recall curve (more informative for imbalanced QQP splits).

All computed in `_evaluation/metrics.py:evaluate_model()` using scikit-learn primitives.

### 4.2 Calibration Metrics

- **ECE (Expected Calibration Error)**: weighted average of absolute difference between confidence and accuracy across bins.
- **MCE (Maximum Calibration Error)**: maximum bin-wise calibration gap.
- **Brier Score**: mean squared error between predicted probabilities and binary labels.
- **NLL (Negative Log Likelihood)**: cross-entropy loss.

Implemented in `_calibration/v2.py` with binning logic in `compute_ece` and `compute_mce`.

### 4.3 Latency Metrics

- **p50 / p95 / p99 inference time**: percentiles of per-prediction latency, measured in milliseconds.
- **Breakdown by component**: preprocessing time, embedding time, cross-encoder time, ensemble aggregation time.

Measured via `time.perf_counter()` instrumentation throughout the inference pipeline in `_inference/cache.py` and `_inference/optimizer.py`.

### 4.4 Agreement Metrics

- **Agreement score**: fraction of models agreeing with the majority vote (0.0 to 1.0).
- **Confidence variance**: variance of individual model confidences around the ensemble prediction.
- **Probability entropy**: Shannon entropy of the vote distribution.
- **Pairwise agreement matrix**: inter-model agreement rates across all model pairs.

Computed in `_ensemble/agreement.py` and `_explainability/agreement_dashboard.py`.

### 4.5 Explainability Metrics

- **Trace completeness**: fraction of decision factors (per-model scores, lexical features, semantic features, weights) populated in the decision trace.
- **Feature attribution faithfulness**: rank correlation between feature importance and ablation impact (future work).

Captured in `DecisionTrace` objects from `_explainability/trace.py`.

---

## 5. Reproducibility

### 5.1 Seeding

All stochastic processes use a controlled seed. The system reads a seed from `configs/training.yaml` (default: 42) and propagates it to:
- `train_test_split` in `_calibration/v2.py`
- Model weight initialisation in transformer training
- Any sampling operations during hard negative mining in `_evaluation/hard_mining.py`

### 5.2 Environment Control

- **Python environment**: dependencies are pinned exactly in `requirements.txt`, `requirements-dev.txt`, `requirements-test.txt`, and `requirements-docs.txt`.
- **Hardware configuration**: experiments log CPU/GPU type, RAM, and inference device.
- **Framework versions**: PyTorch, transformers, sentence-transformers, scikit-learn versions are recorded.

### 5.3 Artifact Sharing

Every experiment produces:

1. **Metrics JSON**: structured evaluation metrics at `_evaluation/metrics.py`.
2. **Evaluation summary**: JSON with metrics, plot paths, error categorisations at `_evaluation/metrics.py:generate_evaluation_report()`.
3. **Plots**: PNG files for confusion matrix, ROC, PR, calibration, prediction distribution, error analysis.
4. **Hard examples**: top-100 false positives and false negatives with error categories in JSON and CSV.
5. **Decision traces**: per-prediction decision traces for qualitative analysis.

All artifacts are timestamped and versioned. The model registry (`_models/registry.py`) maintains a complete inventory of all models with their paths, sizes, load status, and performance metadata.

---

## 6. Statistics

### 6.1 Significance Testing

When comparing two conditions (e.g., ensemble V2 vs. ensemble V1), statistical significance is assessed via:

- **McNemar's test**: for paired nominal data (correct/incorrect) across two models on the same test set.
- **Bootstrapped confidence intervals**: 10,000 bootstrap replicates of the test set to compute 95% confidence intervals for F1, precision, recall, and ECE.
- **Paired t-test** (or Wilcoxon signed-rank for non-normal distributions): for latency comparisons.

### 6.2 Effect Sizes

- **Cohen's d**: for pairwise accuracy comparisons: d = (μ<sub>1</sub> − μ<sub>2</sub>) / σ<sub>pooled</sub>.
- **Absolute risk reduction**: ARR = |F1<sub>treatment</sub> − F1<sub>control</sub>|.
- **Relative improvement**: (F1<sub>treatment</sub> − F1<sub>control</sub>) / F1<sub>control</sub>.

### 6.3 Confidence Intervals

All reported metrics include 95% confidence intervals computed via:

- **Normal approximation interval**: for large test sets (n > 1000).
- **Bootstrap percentile interval**: for smaller or imbalanced subsets.

---

## 7. Reporting

### 7.1 Structured Evaluation Reports

The `generate_evaluation_report` function in `_evaluation/metrics.py` produces a standardised report containing:

```
Model: <name>
Timestamp: <ISO>
Metrics:
  Accuracy: 0.xxx (±0.00y)
  F1: 0.xxx (±0.00y)
  Precision: 0.xxx
  Recall: 0.xxx
  ROC-AUC: 0.xxx
  PR-AUC: 0.xxx
  ECE: 0.xxx
  MCE: 0.xxx
  Brier: 0.xxx
  Log Loss: 0.xxx
Plots: [confusion_matrix, roc_curve, pr_curve, calibration_curve, prediction_distribution, error_analysis]
Hard Examples: 100 FP, 100 FN with error categories
```

### 7.2 Error Analysis

The `error_analysis.py` module categorises each error into one of eight types and reports:

- Aggregate category distribution across all errors (bar chart).
- Per-category hardness distribution (histogram).
- Top-K hardest examples with full context (Q1, Q2, true label, predicted label, probability, model votes).

### 7.3 Qualitative Analysis

For each experimental cycle, the research team conducts a qualitative review of:

- 50 randomly sampled decision traces from the decision boundary (probability 0.3–0.7).
- All false positives and false negatives where the ensemble's confidence exceeds 90%.
- Cases where model agreement falls below 50% (majority disagreement).

These qualitative reviews feed into the next iteration of hypothesis formation.

---

## 8. Iteration

### 8.1 The ARES Research Cycle

The scientific methodology follows a four-phase iterative cycle:

```
┌────────────────────────────────────────────────────┐
│  Phase 1: OBSERVE                                  │
│  - Run evaluation on current system state          │
│  - Collect metrics, plots, error categories        │
│  - Identify significant error patterns             │
│  Module: _evaluation/metrics.py, error_analysis.py │
└──────────┬─────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────┐
│  Phase 2: HYPOTHESISE                              │
│  - Formulate specific, testable hypothesis         │
│  - Define success criteria (ΔF1, ΔECE thresholds)  │
│  - Design ablation or controlled experiment        │
│  Module: _ensemble/v2.py (new rules),              │
│           _linguistics/ (new penalty engines)      │
└──────────┬─────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────┐
│  Phase 3: EXPERIMENT                               │
│  - Implement the change in a controlled manner     │
│  - Compare against existing system (A/B test)      │
│  - Run statistical significance tests              │
│  Module: _calibration/v2.py, configs/*.yaml        │
└──────────┬─────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────┐
│  Phase 4: LEARN                                    │
│  - Accept or reject the hypothesis                 │
│  - If accepted: merge into production system       │
│  - If rejected: document negative result,          │
│    refine theory, re-enter cycle                   │
│  - Update hypothesis registry                      │
│  Module: docs/research/, _artifacts/               │
└──────────┬─────────────────────────────────────────┘
           ↓
        (repeat)
```

### 8.2 Evidence Accumulation

As the cycle repeats, a growing body of evidence is recorded:

- **Accepted hypotheses**: become permanent system features with provenance documentation.
- **Rejected hypotheses**: recorded in a "negative results" ledger to prevent repeated investigation and to inform future theory development.
- **Ambiguous results**: trigger a refined hypothesis and a second round of experimentation with tighter controls or larger sample sizes.

### 8.3 Concrete Example: V1 → V2 Evolution

The transition from Ensemble V1 (`_ensemble/v1.py`) to Ensemble V2 (`_ensemble/v2.py`) exemplifies the iterative cycle:

1. **Observe**: Error analysis showed V1 underperformed on pairs with high entity mismatch and negation mismatch. The static weights could not adapt to linguistic features.
2. **Hypothesise**: "A rule-based dynamic weighting system that incorporates linguistic penalty signals will improve F1 by at least 0.02 on challenging pairs and reduce ECE by 0.01."
3. **Experiment**: Implemented the 10 routing rules in V2, added the penalty combination pipeline (equations at line 372–382 of `v2.py`), and ran comparison against V1.
4. **Learn**: Accepted. The hypothesis was confirmed with ΔF1 = +0.025 and ΔECE = −0.015 on the held-out test set. The six penalty engines became permanent features.

---

## Appendix A: Mapping Between Methodology and Codebase

| Methodology Component | Codebase Module | Key Files |
|---|---|---|
| Hypothesis encoding | `_linguistics/` | contradiction.py, entity.py, intent.py, lexical.py, negation.py |
| Experimental design | `_ensemble/`, `_evaluation/` | v1.py, v2.py, metrics.py, error_analysis.py |
| Measurement | `_evaluation/metrics.py`, `_calibration/v2.py` | metrics.py, v2.py |
| Reproducibility | `_config/`, `_models/registry.py` | settings.py, registry.py |
| Statistics | `_evaluation/metrics.py` | metrics.py (evaluate_model, compare_models) |
| Reporting | `_evaluation/` | metrics.py (generate_evaluation_report), error_analysis.py |
| Iteration | `_ensemble/v2.py` (versioned improvements) | v1.py → v2.py evolution |
| Explainability traces | `_explainability/` | trace.py, text.py, agreement_dashboard.py |
| Agreement analysis | `_ensemble/agreement.py`, `_explainability/` | agreement.py, agreement_dashboard.py |
| Calibration | `_calibration/` | v1.py, v2.py |
| Inference optimisation | `_inference/` | cache.py, optimizer.py, transformer.py |
| Model registry | `_models/` | registry.py, embeddings.py, week2.py |
