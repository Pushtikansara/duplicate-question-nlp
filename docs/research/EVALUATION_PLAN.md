# Evaluation Plan for ARES

## Overview

This document defines every future experiment for the ARES system. Each experiment is specified with its research question, hypothesis, variables, datasets, baselines, statistical tests, and expected plots. The plan is designed to be executed in order, with each experiment building on the findings of prior ones.

---

## Experiment 1: Adaptive Routing vs. Static Ensemble

### Research Question
Does dynamic feature-based model routing (V2) outperform static uniform weighting (V1)?

### Hypothesis
**H1**: Adaptive routing achieves higher F1 and lower ECE than static weighting, with the largest gains on linguistically challenging pairs (low lexical overlap, entity mismatch, negation mismatch).

### Variables
- **Independent**: ensemble strategy (V1 static vs. V2 adaptive).
- **Dependent**: F1 score, ECE, p95 latency, macro-averaged F1 across error categories.
- **Controlled**: test set, random seed, model versions, preprocessing pipeline.

### Datasets
- QQP test split (40K pairs).
- QQP challenge subset: pairs with entity mismatch, negation, low lexical overlap, abbreviations.

### Baselines
- Uniform-weighted average (all models weight = 1/N).
- V1 adaptive ensemble (`_ensemble/v1.py`).
- Best individual model (single-model baseline).

### Statistical Tests
- McNemar's test for paired classification accuracy.
- Bootstrapped 95% CI for ΔF1.
- Wilcoxon signed-rank for paired ECE differences.

### Expected Plots
| Plot | Description |
|---|---|
| **ROC comparison** | V2 vs. V1 vs. best single model on full test set |
| **PR comparison** | Precision-recall for all conditions |
| **F1 by error category** | Grouped bar chart: V2 vs. V1 on abbreviation, synonym, negation, entity mismatch subsets |
| **Calibration comparison** | V2 reliability diagram vs. V1 reliability diagram |
| **Latency breakdown** | Stacked bar: preprocessing, embedding, cross-encoder, ensemble for V1 vs. V2 |
| **Ablation waterfall** | Bar chart: F1 with each component removed (→ identifies key contributors) |

### Implementation
- `_evaluation/metrics.py:compare_models()` with predictions_dict containing V1 and V2 predictions.
- `_evaluation/metrics.py:generate_model_comparison_plots()` for ROC/PR/calibration comparison.
- Hard example mining via `find_hard_examples()` for category-level analysis.

---

## Experiment 2: Linguistic Penalty Effectiveness

### Research Question
What is the marginal contribution of each linguistic penalty engine to overall system performance?

### Hypothesis
**H2**: The contradiction penalty has the largest marginal impact on F1, followed by the entity penalty. The lexical penalty has the smallest marginal impact.

### Variables
- **Independent**: penalty engine enabled/disabled (binary: 6 conditions in a leave-one-out design).
- **Dependent**: ΔF1 (relative to full system), ΔECE, penalty application rate (fraction of pairs where penalty > 0).
- **Controlled**: all other ensemble parameters, model weights, calibration.

### Datasets
- QQP test split.
- QQP negation subset (pairs with negation words).
- QQP entity mismatch subset.
- QQP low-overlap subset.

### Baselines
- Full ARES system (all 6 penalties enabled).
- ARES with no penalties (penalty coefficient = 0 for all engines).

### Statistical Tests
- One-way ANOVA on F1 scores across 7 conditions (full + 6 ablated).
- Post-hoc Tukey HSD for pairwise comparisons.
- Cohen's d for each ablation's effect size.

### Expected Plots
| Plot | Description |
|---|---|
| **Ablation bar chart** | F1 for full system vs. each leave-one-out condition |
| **ECE ablation** | ECE for each condition |
| **Penalty activation rates** | Bar chart: fraction of test pairs where each penalty is applied |
| **Penalty magnitude distribution** | Histogram of penalty values per engine |
| **Conditional accuracy** | Accuracy on pairs where a given penalty was applied |

### Implementation
- Modify `_ensemble/v2.py:adaptive_ensemble_predict()` to accept a `disabled_penalties` parameter.
- Run 6 ablation conditions + 1 full condition + 1 zero-penalty condition.
- Use the existing metrics pipeline in `_evaluation/metrics.py`.

---

## Experiment 3: Calibration Improvement

### Research Question
Which calibration method (temperature scaling, Platt scaling, isotonic regression) produces the best-calibrated predictions for the ARES ensemble?

### Hypothesis
**H3**: Temperature scaling achieves the lowest ECE on the ensemble output, while isotonic regression achieves the lowest MCE. The choice of calibration method does not significantly affect accuracy (F1).

### Variables
- **Independent**: calibration method (none, temperature, Platt, isotonic).
- **Dependent**: ECE, MCE, Brier score, NLL, F1 (for monitoring unintended accuracy shifts).
- **Controlled**: calibration fitting set (20% of training data), seed, bin count (10 bins).

### Datasets
- QQP training set (fit calibration).
- QQP validation set (select best method).
- QQP test set (final evaluation).

### Baselines
- No calibration (raw ensemble probabilities).
- Default temperature (T = 1.0).

### Statistical Tests
- Paired t-test on ECE differences across 100 bootstrap replicates.
- Effect size reporting (Cohen's d).

### Expected Plots
| Plot | Description |
|---|---|
| **Calibration curves (reliability diagrams)** | One curve per method, overlaid |
| **ECE comparison** | Bar chart with 95% CI |
| **MCE comparison** | Bar chart |
| **Brier score comparison** | Bar chart |
| **Histogram of calibrated probabilities** | Distribution shift from before to after calibration |
| **NLL per bin** | Per-bin log loss to identify where calibration helps most |

### Implementation
- `_calibration/v2.py:calibrate_predictions()` for each method.
- `_calibration/v2.py:select_best_calibration()` for automatic selection.
- `_calibration/v2.py:get_calibration_curve_data()` for reliability diagram data.
- `_evaluation/metrics.py:plot_calibration_curve()` for visualisation.

---

## Experiment 4: Agreement-Aware Confidence

### Research Question
Can inter-model agreement be used to produce more reliable confidence estimates?

### Hypothesis
**H4**: Predictions with high agreement (≥ 80%) are more accurate and better calibrated than predictions with low agreement (< 50%). Agreement-conditional ECE is significantly lower for high-agreement predictions.

### Variables
- **Independent**: agreement quartile (Q1: 0–50%, Q2: 50–70%, Q3: 70–90%, Q4: 90–100%).
- **Dependent**: accuracy, ECE, mean confidence, precision, recall within each quartile.
- **Controlled**: ensemble method, test set, model versions.

### Datasets
- QQP test split.

### Baselines
- Overall (unconditional) accuracy and ECE.
- Individual model accuracy (for comparison with ensemble agreement).

### Statistical Tests
- Chi-square test for independence between agreement quartile and correctness.
- Pearson r between agreement score and confidence.
- Spearman ρ between agreement score and probability standard deviation.

### Expected Plots
| Plot | Description |
|---|---|
| **Agreement vs. accuracy** | Scatter plot: agreement score (x) vs. binary correctness (y, with smoothed curve) |
| **Accuracy by agreement quartile** | Bar chart with error bars |
| **ECE by agreement quartile** | Bar chart showing calibration improves with agreement |
| **Agreement distribution** | Histogram of agreement scores across test set |
| **Agreement-accuracy matrix** | Heatmap: agreement score (x) vs. confidence (y), coloured by accuracy |

### Implementation
- `_ensemble/agreement.py:AgreementReport` provides `agreement_score` and `majority_ratio`.
- `_explainability/agreement_dashboard.py:analyze_model_agreement()` provides full dashboard.
- Aggregate over test set using the `_evaluation/metrics.py` pipeline.

---

## Experiment 5: Model Routing Decisions

### Research Question
How do the adaptive routing weights change as a function of input features?

### Hypothesis
**H5**: The routing rules in V2 produce systematically different weight distributions for different semantic pair types. The cross-encoder weight is highest for contradiction pairs; the TF-IDF weight is highest for high-overlap pairs.

### Variables
- **Independent**: pair type (abbreviation, synonym, negation, entity mismatch, contradiction, high overlap, low overlap).
- **Dependent**: weight assigned to each model group (TF-IDF, transformer, embedding, cross-encoder).
- **Controlled**: feature computation pipeline, test set.

### Datasets
- QQP test split with semantic categorisation labels.

### Baselines
- Uniform weight distribution (0.25 each).
- V1 fixed weights.

### Statistical Tests
- MANOVA on weight vectors across pair types.
- Post-hoc pairwise Hotelling's T² tests.

### Expected Plots
| Plot | Description |
|---|---|
| **Weight radar chart** | Spider plot of 4 weights for each pair type |
| **Weight heatmap** | Pair type (y) vs. model group (x), coloured by mean weight |
| **Feature vs. weight scatter** | lexical_overlap (x) vs. tfidf_weight (y) with regression line |
| **Weight evolution** | Parallel coordinates plot of weight vectors |
| **Decision boundary analysis** | 2D PCA projection of feature space, coloured by dominant model group |

### Implementation
- `_ensemble/v2.py:compute_dynamic_weights()` returns `AdaptiveWeightsV2` with all 4 group weights.
- `_ensemble/v2.py:compute_ensemble_features()` provides feature vector.
- Log weights and features for every prediction during evaluation.

---

## Experiment 6: Memory-Augmented Inference

### Research Question
Does the LRU embedding cache improve inference speed without degrading accuracy?

### Hypothesis
**H6**: The embedding cache achieves a hit rate of ≥ 60% for repeated or similar questions, reducing p95 latency by at least 40% with no measurable effect on accuracy.

### Variables
- **Independent**: caching strategy (no cache, LRU cache with sizes 1K / 5K / 10K / 50K).
- **Dependent**: cache hit rate, p50/p95/p99 latency, F1 (to verify no accuracy regression).
- **Controlled**: test set, model versions, preprocessing pipeline.

### Datasets
- QQP test split.
- QQP test split with shuffled order (to measure cold-cache performance).

### Baselines
- No caching (compute every embedding from scratch).
- Simple in-memory dictionary (no eviction).

### Statistical Tests
- Independent t-test on latency distributions (cache vs. no-cache).
- Equivalence test on F1 (TOST procedure) to verify accuracy is preserved.

### Expected Plots
| Plot | Description |
|---|---|
| **Cache hit rate vs. cache size** | Line plot |
| **Latency CDF** | Cumulative distribution: no cache vs. 1K vs. 10K |
| **Latency reduction by percentile** | Bar chart showing p50/p95/p99 improvement |
| **Cache composition** | Pie chart: what is being cached (preprocessing vs. embeddings vs. model objects) |
| **Accuracy vs. cache size** | Scatter plot (should be flat) |

### Implementation
- `_inference/cache.py:LRUCache` with configurable `max_size`.
- `_inference/optimizer.py:EmbeddingCache` and `PreprocessingCache`.
- `get_cache_stats()` in `_ensemble/v2.py` for hit/miss/eviction statistics.
- Modify `cache_size` parameter in `_inference/optimizer.py`.

---

## Experiment 7: Cross-Domain Generalisation

### Research Question
How well does the ARES system, trained on QQP, generalise to out-of-domain question pairs?

### Hypothesis
**H7**: The HuggingFace bi-encoders (BGE, E5, MPNet) generalise better across domains than the fine-tuned DistilBERT models. The ensemble retains higher cross-domain F1 than any single model.

### Variables
- **Independent**: target domain (programming, medicine, finance, customer support).
- **Dependent**: F1, ROC-AUC, ECE per domain.
- **Controlled**: model checkpoints (zero-shot, no fine-tuning on target), ensemble method.

### Datasets
- **Source**: QQP train/test (160K pairs).
- **Target domains**:
  - StackExchange duplicate questions (programming).
  - MedQuAD medical question pairs.
  - Finance FAQ pairs.
  - Customer support ticket pairs.

### Baselines
- QQP test performance (in-domain reference).
- Best individual model on each target domain.

### Statistical Tests
- Two-way ANOVA: domain × model type on F1.
- Tukey HSD for cross-domain pairwise comparisons.
- Generalisation gap = F1<sub>QQP</sub> − F1<sub>target</sub>.

### Expected Plots
| Plot | Description |
|---|---|
| **Cross-domain F1 matrix** | Domain (y) vs. model (x), coloured by F1 |
| **Generalisation gap** | Bar chart: ΔF1 for each domain |
| **Per-model cross-domain radar** | Spider chart: one line per model |
| **Domain similarity embedding** | t-SNE of target domain embeddings, coloured by accuracy |
| **Calibration shift** | ECE on each domain — does calibration degrade? |

### Implementation
- Dataset loading via `_config/settings.py` and `configs/dataset.yaml`.
- Zero-shot inference via existing `_inference/transformer.py` and `_models/embeddings.py`.
- Metrics pipeline in `_evaluation/metrics.py` is domain-agnostic.

---

## Experiment 8: Latency-Accuracy Tradeoff

### Research Question
What is the Pareto frontier of the latency-accuracy tradeoff across models and ensemble configurations?

### Hypothesis
**H8**: There exists a subset of models (≈4–5) that achieves >95% of full ensemble F1 at <50% of the latency. The optimal subset depends on the query's linguistic features.

### Variables
- **Independent**: model subset (2^10 = 1,024 possible subsets — evaluated via greedy search).
- **Dependent**: F1 (accuracy), p95 latency (milliseconds).
- **Controlled**: test set, seed, hardware.

### Datasets
- QQP test split.

### Baselines
- Full ensemble (all 10 base models + ensemble).
- Fastest single model (TF-IDF + Logistic Regression).
- Best single model (DeBERTa or MPNet).

### Statistical Tests
- Pareto dominance analysis.
- Elbow detection on the Pareto curve.

### Expected Plots
| Plot | Description |
|---|---|
| **Pareto frontier** | Scatter: latency (x) vs. F1 (y), each point is a model subset |
| **Marginal gain bar chart** | F1 increase per additional model added in greedy order |
| **Latency waterfall** | Stacked bar showing contribution of each model to total latency |
| **Optimal subset by pair type** | What subset is best for abbreviation pairs vs. negation pairs |
| **Cumulative F1 curve** | F1 as models are added in order of accuracy |

### Implementation
- Greedy forward selection: start with best single model, iteratively add models that improve F1 the most.
- Latency measurement via `_inference/optimizer.py:benchmark_inference()`.
- Accuracy measurement via `_evaluation/metrics.py:evaluate_model()`.

---

## Experiment 9: Explainability Faithfulness

### Research Question
Do the feature attributions in the decision trace accurately reflect the model's true decision-making process?

### Hypothesis
**H9**: The adaptive weights in the decision trace are correlated with the actual impact of each model group on the final prediction, as measured by leave-one-out ablation. Spearman ρ ≥ 0.7.

### Variables
- **Independent**: attribution method (trace-based weights vs. leave-one-out ablation).
- **Dependent**: rank correlation (Spearman ρ) between predicted and actual importance.
- **Controlled**: test set (200 stratified examples), seed.

### Datasets
- Random sample of 200 test pairs (stratified by agreement level).

### Baselines
- Uniform importance (all models equal — negative control).
- Random permutation of importance scores.

### Statistical Tests
- Spearman rank correlation.
- Kendall's τ as a robustness check.
- 95% CI via bootstrap.

### Expected Plots
| Plot | Description |
|---|---|
| **Attribution faithfulness scatter** | Predicted importance (x) vs. actual ablation impact (y) per model per example |
| **Faithfulness by model** | Bar chart of Spearman ρ for each model group |
| **Faithfulness by pair type** | Bar chart of ρ for abbreviation, negation, contradiction pairs |
| **Error attribution analysis** | For false predictions, does the trace highlight the correct responsible model? |
| **Calibration of attributions** | Do higher-weight models actually contribute more? |

### Implementation
- `_explainability/trace.py:DecisionTrace` provides predicted attributions.
- Leave-one-out ablation: systematically remove each model and measure ΔF1.
- Spearman correlation computed across all test examples.

---

## Experiment 10: Ensemble Diversity Analysis

### Research Question
How diverse are the 11 models, and what is the relationship between diversity and ensemble accuracy?

### Hypothesis
**H10**: Ensemble accuracy is positively correlated with pairwise model diversity (negative Pearson r between agreement and error correlation). The cross-encoder models contribute the most diversity; the bi-encoders contribute the least.

### Variables
- **Independent**: model pair (55 unique pairs from 11 models).
- **Dependent**: pairwise agreement rate, pairwise error correlation, Q-statistic (Kuncheva's diversity measure).
- **Controlled**: test set, seed.

### Datasets
- QQP test split.

### Baselines
- Maximum possible diversity (two models that never agree on errors).
- Random label generator (upper bound for diversity, lower bound for accuracy).

### Statistical Tests
- Mantel test for correlation between distance matrices.
- Bootstrap CI for diversity-accuracy correlation.

### Expected Plots
| Plot | Description |
|---|---|
| **Pairwise agreement heatmap** | 11 × 11 matrix: agreement rate (warm = high agreement) |
| **Pairwise error correlation heatmap** | Error overlap between model pairs |
| **Diversity vs. accuracy** | Scatter: each model's diversity score (x) vs. its accuracy (y) |
| **MDS of model behaviour** | 2D projection of models based on prediction vectors |
| **Ensemble size vs. diversity** | Line plot: cumulative diversity added as models are included |

### Implementation
- `_ensemble/agreement.py:collect_all_votes()` provides votes for all models.
- `_explainability/agreement_dashboard.py:compute_model_leaderboard()` ranks models by multiple criteria.
- New metrics: pair agreement rate, Q-statistic, correlation of errors.
- Visualisation via `_evaluation/metrics.py` plot infrastructure.

---

## Experiment Execution Order

```
Phase 1: Foundation
  Ex1: Adaptive Routing vs. Static Ensemble   ← validates the core innovation
  Ex2: Linguistic Penalty Effectiveness       ← isolates component contributions

Phase 2: Calibration & Trust
  Ex3: Calibration Improvement               ← improves probability quality
  Ex4: Agreement-Aware Confidence            ← connects agreement to trust

Phase 3: Understanding
  Ex5: Model Routing Decisions               ← explains how the system works
  Ex10: Ensemble Diversity Analysis          ← characterises model relationships

Phase 4: Performance
  Ex6: Memory-Augmented Inference            ← quantifies caching benefit
  Ex8: Latency-Accuracy Tradeoff             ← finds Pareto-optimal configurations

Phase 5: Generalisation
  Ex7: Cross-Domain Generalisation           ← measures transfer capability

Phase 6: Verification
  Ex9: Explainability Faithfulness           ← validates the explanation system
```

---

## Statistical Power Analysis

All experiments use the QQP test set (≈40K pairs). For a medium effect size (Cohen's d = 0.20) at α = 0.05 and β = 0.80:

- **Paired tests** (Ex1, Ex2, Ex3): N ≈ 200 pairs needed → test set is adequate.
- **Correlation tests** (Ex4, Ex9): N ≈ 200 for ρ = 0.20 → stratified sample is adequate.
- **ANOVA** (Ex5, Ex7): N ≈ 1,000 per group for f = 0.10 → test set is adequate.
- **Pareto analysis** (Ex8): descriptive, no power requirement.

---

## Reporting Template

Each experiment produces a standardised report:

```markdown
# Experiment X: [Title]

## Research Question
...

## Hypothesis
...

## Results
| Condition | F1 | ECE | p95 Latency (ms) |
|---|---|---|---|
| Control | ... | ... | ... |
| Treatment | ... | ... | ... |
| Δ | ±X.XX | ±X.XX | ±X.XX |

## Statistical Tests
- McNemar χ² = X.XX, p = 0.XXX
- Cohen's d = X.XX [95% CI: X.XX, X.XX]

## Figures
[links to plots]

## Interpretation
...

## Conclusion
Hypothesis [accepted/rejected]. Next step: ...
```
