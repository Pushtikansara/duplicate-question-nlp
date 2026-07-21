# Research Hypotheses

## 18 Testable Hypotheses for the ARES Architecture

---

Each hypothesis is structured as: **H_N: Statement.** Followed by Rationale, Test Method, Success Criteria, and References to the relevant ARES module. All hypotheses are falsifiable through empirical evaluation on held-out test data using appropriate statistical tests.

---

### H1: Adaptive Routing Outperforms Static Averaging

**Statement.** The ARES adaptive ensemble (V2 dynamic confidence routing) achieves higher F1 and lower ECE than (a) any individual model, (b) simple unweighted averaging, and (c) fixed-weight averaging, on the complete test set.

**Rationale.** Input-dependent weighting allows the ensemble to exploit the strengths of different model classes for different question types. Individual models have fixed inductive biases that cause systematic errors on certain inputs. Static averaging cannot adjust for these biases.

**Test Method.** Compare 5 methods on a held-out test set of ≥10,000 question pairs: (1) best individual model, (2) unweighted average, (3) fixed weights (optimized on validation set), (4) ARES V1, (5) ARES V2. Use McNemar's test for label predictions and paired bootstrap for probability estimates.

**Success Criteria.** ARES V2 achieves statistically significant (p < 0.01) improvement over all baselines in F1 and ECE. Minimum improvement: +1.5% F1, -20% relative ECE.

**Relevant Module.** `_ensemble/v2.py:compute_dynamic_weights()`

---

### H2: Linguistic Penalties Reduce False Positives

**Statement.** The ARES V2 linguistic penalty framework (entity, intent, negation, contradiction, lexical penalties) reduces the false positive rate by at least 25% relative to V1 (feature-based weighting without explicit penalties), with no more than a 5% increase in false negative rate.

**Rationale.** False positives in duplicate detection disproportionately arise from surface-level similarities that mask underlying semantic differences — precisely the cases that symbolic linguistic engines are designed to catch.

**Test Method.** Ablation study: compare ARES V2 full system against ARES V2 with all linguistic penalties zeroed. Measure FP rate, FN rate, F1, and precision on full test set. Further decompose by error category using `_evaluation/metrics.py:find_hard_examples()`.

**Success Criteria.** ≥25% relative reduction in FP rate. FN rate increase ≤5%. Precision improves by ≥3 points.

**Relevant Module.** `_ensemble/v2.py:adaptive_ensemble_predict()` (lines 371–382)

---

### H3: Entity Detection Reduces Entity-Mismatch False Positives

**Statement.** On question pairs where the two questions refer to different named entities (programming languages, frameworks, technologies), the Entity Engine reduces the false positive rate by at least 40% compared to the ensemble without entity detection.

**Rationale.** Transformer bi-encoders represent entities in continuous embedding space, where "PyTorch" and "TensorFlow" are close. The Entity Engine performs discrete symbolic matching, enabling exact entity comparison that embeddings cannot reliably perform.

**Test Method.** Construct a test subset of ≥500 entity-mismatched pairs (e.g., identical question structure with different languages/frameworks). Compare FP rate with and without `get_entity_penalty()`. Use stratified bootstrap to assess significance.

**Success Criteria.** ≥40% relative FP reduction on entity-mismatched subset. No significant degradation on non-entity pairs.

**Relevant Module.** `_linguistics/entity.py:get_entity_penalty()`

---

### H4: Intent Incompatibility Predicts Non-Duplicate Status with High Precision

**Statement.** When two questions have incompatible intents (e.g., Definition vs. Installation), the pair is non-duplicate with precision ≥0.95.

**Rationale.** Intent category reflects the underlying information need. If one question asks "What is X?" and the other asks "How do I install X?", they cannot be expressing the same need, even if they share vocabulary.

**Test Method.** On the test set, identify all pairs with incompatible intents per `_INTENT_CONFLICTS` in `intent.py`. Compute precision (fraction that are true non-duplicates). Compare against a baseline of random non-duplicate precision.

**Success Criteria.** Precision ≥0.95. Lower bound of 95% CI ≥0.90.

**Relevant Module.** `_linguistics/intent.py:intent_mismatch_penalty()`

---

### H5: Model Disagreement Predicts Error Better Than Individual Confidence

**Statement.** The agreement score (fraction of models agreeing with the majority) is a better predictor of prediction error than any single model's confidence score, as measured by the area under the ROC curve (AUC) for the error prediction task.

**Rationale.** When models disagree, it signals genuine ambiguity in the input. Individual model confidence reflects only that model's internal state, which may be miscalibrated. Disagreement is an emergent property of the ensemble that captures irreducible uncertainty.

**Test Method.** For each prediction, compute (a) agreement score, (b) confidence of the best-calibrated model, (c) confidence of the ensemble. Treat error (binary: correct/incorrect) as the target. Compute AUC for each predictor.

**Success Criteria.** Agreement score AUC ≥ 0.75. Agreement score AUC > best-individual-model confidence AUC by ≥0.05.

**Relevant Module.** `_ensemble/agreement.py:analyze_agreement()`

---

### H6: Adaptive Routing Shifts Weights Optimally Per Input Type

**Statement.** The dynamic weights computed by ARES V2 differ systematically across input types: lexical weight is highest on high-overlap pairs, cross-encoder weight is highest on contradiction pairs, and embedding weight is highest on paraphrase pairs.

**Rationale.** The routing rules in `compute_dynamic_weights()` are designed to increase weight on model classes whose inductive bias matches the input characteristics. If the rules are effective, these weight shifts should be observable in aggregate.

**Test Method.** Cluster the test set by input characteristics (lexical overlap, semantic depth, entity mismatch, contradiction score). For each cluster, compute the mean dynamic weights. Compare against random permutation baseline.

**Success Criteria.** Statistically significant (p < 0.01) differences in mean weights across clusters. At least 3 clusters show the expected weight pattern.

**Relevant Module.** `_ensemble/v2.py:compute_dynamic_weights()`

---

### H7: Cross-Encoder Dominates on Contradiction-Heavy Inputs

**Statement.** On question pairs with high contradiction scores (≥0.5), the DeBERTa cross-encoder's prediction agrees with the ground truth more often than any bi-encoder or TF-IDF model, by a margin of at least 10 percentage points in accuracy.

**Rationale.** Cross-encoders are trained on NLI data and can perform explicit entailment/contradiction classification. Bi-encoders and TF-IDF models represent similarity, not contradiction. The routing rules increase cross-encoder weight on contradiction-heavy inputs.

**Test Method.** Identify all test pairs where contradiction score ≥0.5 (via `get_contradiction_penalty()`). Compute per-model accuracy on this subset.

**Success Criteria.** DeBERTa accuracy ≥ 80%. Margin over best bi-encoder ≥ 10 points.

**Relevant Module.** `_linguistics/contradiction.py:detect_contradiction()` and `_ensemble/v2.py` rule 6

---

### H8: Negation Mismatch Is a Stronger Predictor Than Lexical Overlap

**Statement.** On question pairs where one question contains a negation and the other does not (negation mismatch), the negation penalty contributes more to error reduction than lexical features alone, as measured by feature importance ablation.

**Rationale.** Negation flips the meaning of a question. A single "not" or "un-" prefix can change "install" to "uninstall." Lexical overlap is near 100% for such pairs, making it a poor discriminator.

**Test Method.** On negation-mismatch test pairs, compare error rates of (a) ensemble without any penalty, (b) ensemble with lexical penalty only, (c) ensemble with negation penalty only, (d) ensemble with both.

**Success Criteria.** Condition (c) significantly outperforms (b) (p < 0.05). Condition (d) is not significantly better than (c).

**Relevant Module.** `_linguistics/negation.py:get_negation_penalty()`

---

### H9: Calibration Improves from Individual to Ensemble Level

**Statement.** The ensemble's calibration (ECE) is better than the average individual model's calibration by at least 0.03 ECE points, and better than the best-calibrated individual model.

**Rationale.** Ensembling reduces variance and smooths out individual miscalibration patterns. The trimmed mean and adaptive weighting both contribute to improved calibration.

**Test Method.** Compute ECE for each individual model and for the ARES V2 ensemble. Use paired bootstrap to compare.

**Success Criteria.** Ensemble ECE ≤ 0.05 and better (lower) than every individual model's ECE.

**Relevant Module.** `_calibration/v2.py:evaluate_calibration()`

---

### H10: Temperature Scaling Is the Most Effective Calibration Method for This Ensemble

**Statement.** Temperature scaling achieves lower ECE on held-out calibration data than Platt scaling, isotonic regression, or no calibration, for the majority of models in the registry.

**Rationale.** Temperature scaling is a single-parameter method that preserves the order of predictions. It is less prone to overfitting than isotonic regression and more suitable for the probability distributions produced by transformer models.

**Test Method.** For each of the 11 models, split data into calibration fit/validation sets. Fit temperature scaling, Platt scaling, isotonic regression, and no calibration. Compare ECE on validation set.

**Success Criteria.** Temperature scaling achieves lowest ECE for ≥6 of 11 models. Average ECE across all models is lowest for temperature scaling.

**Relevant Module.** `_calibration/v1.py:temperature_scale()` and `_calibration/v2.py:find_optimal_temperature()`

---

### H11: The Decision Trace Improves Error Diagnosis

**Statement.** Human evaluators given ARES DecisionTraces can identify the cause of prediction errors (entity mismatch, negation, contradiction, etc.) more accurately and more quickly than evaluators given only raw model probabilities.

**Rationale.** The DecisionTrace provides structured, category-specific information. Raw probabilities require the evaluator to infer the cause from a single scalar.

**Test Method.** Human evaluation study: N=20 participants, each evaluates 50 error cases. Randomly assign to DecisionTrace or raw probability condition. Measure error classification accuracy and time-per-case.

**Success Criteria.** DecisionTrace group achieves ≥30% higher classification accuracy and ≥20% faster evaluation time.

**Relevant Module.** `_explainability/trace.py:DecisionTrace` and `_explainability/text.py:generate_explanation()`

---

### H12: Counterfactual Explanations Are More Actionable Than Feature Attributions

**Statement.** When shown a non-duplicate prediction, users presented with counterfactual explanations (e.g., "Change 'Python' to 'JavaScript' to make this a duplicate") can more successfully modify questions to change the prediction than users shown feature attribution weights.

**Rationale.** Counterfactuals provide concrete, actionable changes. Feature attributions show importance weights but not how to achieve the opposite outcome.

**Test Method.** User study: N=30 participants perform a question modification task. Measure success rate and time-to-success.

**Success Criteria.** Counterfactual group achieves ≥40% higher modification success rate.

**Relevant Module.** `_explainability/text.py:generate_counterfactual_explanation()`

---

### H13: LRU Caching Reduces Latency Without Accuracy Loss

**Statement.** The ARES LRU cache (max_size=10,000) reduces mean inference latency by at least 40% on repeated question pairs, with no statistically significant difference in accuracy.

**Rationale.** Inference latency is dominated by embedding computation and model loading. Caching eliminates repeated computation for identical inputs.

**Test Method.** Simulate a workload with 50% repeated question pairs. Measure latency with and without caching. Compare predictions for identical cache hits.

**Success Criteria.** ≥40% latency reduction. Zero accuracy difference on cached predictions.

**Relevant Module.** `_inference/cache.py:LRUCache` and `_inference/cache.py:cached_embedding()`

---

### H14: Automated Error Categories Correlate with Human Judgments

**Statement.** The error categories assigned by ARES's automated hard example mining (`find_hard_examples()`) agree with human-assigned categories with Cohen's κ ≥ 0.70, indicating substantial agreement.

**Rationale.** The error categorization uses simple heuristics (language mismatch via keyword matching, framework mismatch via keyword matching, negation mismatch via boolean detection). If these heuristics are well-designed, they should match human judgment.

**Test Method.** Sample 200 error cases. Have 3 NLP researchers independently assign error categories. Compute inter-rater agreement among humans and between humans and the automated system.

**Success Criteria.** Cohen's κ ≥ 0.70 between automated system and majority human judgment.

**Relevant Module.** `_evaluation/metrics.py:find_hard_examples()`

---

### H15: The Ensemble Is More Robust to Adversarial Perturbations

**Statement.** ARES V2 maintains higher accuracy on adversarial question pairs (constructed to exploit individual model weaknesses) than any individual model, with a minimum accuracy advantage of 15 percentage points.

**Rationale.** Adversarial examples typically target a specific model class. The ensemble's diversity provides robustness: an example that fools the bi-encoders may be caught by the cross-encoder or by a linguistic penalty, and vice versa.

**Test Method.** Construct 5 types of adversarial pairs: (1) negation minimal pairs, (2) entity-swap pairs, (3) contradiction pairs, (4) paraphrase pairs with low lexical overlap, (5) syntactic but not semantic variants. Test all individual models and the ensemble.

**Success Criteria.** Ensemble accuracy ≥ 15 points above the best individual model on each adversarial category. Overall ensemble accuracy ≥ 75%.

**Relevant Module.** Full ARES V2 pipeline (`_ensemble/v2.py:adaptive_ensemble_predict()`)

---

### H16: The Marginal Benefit of Adding Models Diminishes After 7 Models

**Statement.** Adding models to the ARES ensemble beyond 7 models yields less than 0.5% F1 improvement on the full test set, establishing a point of diminishing returns.

**Rationale.** The first few models provide diverse inductive biases. As more models are added, new models increasingly correlate with existing ones, providing less marginal information.

**Test Method.** Greedy ablation: starting from the best single model, iteratively add the model that most improves ensemble F1. Record cumulative F1 after each addition.

**Success Criteria.** F1 improvement from 7 to 11 models < 0.5%. The optimal 7-model subset achieves ≥ 98% of full-ensemble F1.

**Relevant Module.** `_ensemble/agreement.py:collect_all_votes()`

---

### H17: Confidence Spread Predicts Borderline Predictions

**Statement.** High confidence spread (max - min confidence across models) has a positive correlation (Pearson's r ≥ 0.6) with borderline predictions (ensemble probability within 0.15 of 0.5).

**Rationale.** When models strongly disagree on confidence, the true answer is likely ambiguous. High spread indicates that at least one model is highly confident in a direction opposed by others.

**Test Method.** Compute correlation between confidence spread and distance from 0.5 threshold across all test set predictions.

**Success Criteria.** Pearson's r ≥ 0.6. 95% CI excludes r < 0.4.

**Relevant Module.** `_explainability/agreement_dashboard.py:AgreementDashboard.confidence_spread`

---

### H18: Dynamic Calibration (Agreement-Aware) Outperforms Static Calibration

**Statement.** Adjusting a model's calibration temperature based on whether it agrees or disagrees with the ensemble majority reduces ECE by at least 15% compared to using a single global temperature for that model.

**Rationale.** A model that disagrees with the majority is more likely to be wrong; its confidence should be systematically lowered. A model that agrees with the majority should maintain or increase its confidence.

**Test Method.** For each model, fit two temperatures: T_agree (when model agrees with majority) and T_disagree (when model disagrees). Compare against single-temperature calibration. Use 5-fold cross-validation.

**Success Criteria.** Agreement-aware calibration achieves ≥15% lower ECE. Both conditions show significant calibration improvement over no calibration.

**Relevant Module.** `_calibration/v1.py:get_model_calibration_params()` (proposed extension for agreement-aware parameters)

---

### Summary Table

| Hypothesis | Area | Key Metric | Target | Module |
|---|---|---|---|---|
| H1 | Routing | F1, ECE | +1.5% F1, -20% ECE | `_ensemble/v2.py` |
| H2 | Linguistic Penalties | FP rate | -25% relative | `_ensemble/v2.py` |
| H3 | Entity Detection | FP rate | -40% on entity pairs | `_linguistics/entity.py` |
| H4 | Intent Prediction | Precision | ≥0.95 | `_linguistics/intent.py` |
| H5 | Disagreement Signal | AUC | ≥0.75 | `_ensemble/agreement.py` |
| H6 | Weight Patterns | Cluster means | p < 0.01 | `_ensemble/v2.py` |
| H7 | Cross-Encoder Dominance | Accuracy | ≥80% on contradiction | `_linguistics/contradiction.py` |
| H8 | Negation vs. Lexical | FP reduction | Negation > Lexical | `_linguistics/negation.py` |
| H9 | Calibration Improvement | ECE | ≤0.05 | `_calibration/v2.py` |
| H10 | Best Calibration Method | ECE | Temperature best | `_calibration/v1.py` |
| H11 | Decision Trace Utility | Accuracy | +30% human | `_explainability/trace.py` |
| H12 | Counterfactual Utility | Success rate | +40% | `_explainability/text.py` |
| H13 | Cache Latency | Latency | -40% | `_inference/cache.py` |
| H14 | Error Categorization | Cohen's κ | ≥0.70 | `_evaluation/metrics.py` |
| H15 | Adversarial Robustness | Accuracy | +15 points | `_ensemble/v2.py` |
| H16 | Diminishing Returns | F1 delta | <0.5% | `_ensemble/agreement.py` |
| H17 | Confidence Spread | Pearson's r | ≥0.6 | `_explainability/agreement_dashboard.py` |
| H18 | Dynamic Calibration | ECE | -15% | `_calibration/` |

---

*All hypotheses are designed to be tested using the existing evaluation infrastructure in `_evaluation/`, the error analysis tools in `_evaluation/metrics.py`, and the hard example mining capability in `find_hard_examples()`. The experimental framework is fully reproducible.*
