# Threats to Validity — ARES (Adaptive Reasoning Engine for Semantic Understanding)

**Document Version:** 1.0
**Date:** 2026-07-21
**Scope:** Comprehensive analysis of validity threats across the ARES system's data, models, evaluation, deployment, and ethical dimensions.

---

## Table of Contents

1. [Dataset Bias](#1-dataset-bias)
2. [Annotation Noise](#2-annotation-noise)
3. [Overfitting](#3-overfitting)
4. [Evaluation Bias](#4-evaluation-bias)
5. [Domain Shift](#5-domain-shift)
6. [Fairness](#6-fairness)
7. [Ethical Risks](#7-ethical-risks)
8. [Limitations](#8-limitations)
9. [Summary Threat Matrix](#9-summary-threat-matrix)

---

## 1. Dataset Bias

### 1.1 Quora Dataset Characteristics

**Description:** The Quora Question Pairs dataset (404,290 pairs, 37% duplicate) was collected from Quora's platform between 2016–2017. It reflects the linguistic patterns, topic distribution, and user demographics of Quora's English-speaking user base during that period. Questions are primarily factual, informational, and procedural — not conversational, creative, or opinion-driven. The dataset was collected via a heuristic mining process that pairs questions likely to be duplicates based on shared words, which introduces selection bias: the distribution of difficulty in the dataset does not reflect the natural distribution of semantic similarity in the wild.

**Severity:** HIGH

**Mitigation Strategy:**
- Curate supplementary datasets from diverse sources (Stack Exchange, Reddit, customer support tickets, academic Q&A)
- Implement stratified evaluation across question categories (factual, procedural, opinion, conversational)
- Report per-category performance breakdowns
- Develop synthetic data generation for underrepresented question types

**Current ARES Status:** The system operates exclusively on the Quora dataset. No multi-source data strategy is implemented. Topic distribution analysis is available in Week 1 EDA notebooks but not integrated into the evaluation pipeline.

---

### 1.2 Topic Distribution

**Description:** Quora's topic distribution is heavily skewed toward technology, science, business, and life advice. Long-tail topics (e.g., specialized academic domains, regional cultural topics, niche hobbies) are poorly represented. Models trained on this distribution learn topic-specific patterns for duplicate detection that may not generalize. For example, the system may be better at detecting duplicates in "How do I learn Python?" variations than in "What is the significance of the Bantu migration?" variations.

**Severity:** HIGH

**Mitigation Strategy:**
- Annotate the evaluation set with topic labels and report topic-stratified metrics
- Collect topic-balanced evaluation sets
- Use topic-adaptive routing in the ensemble (different model weights per topic cluster)
- Implement few-shot evaluation protocols for zero-resource topics

**Current ARES Status:** No topic taxonomy exists in the system. The `_linguistics/intent.py` engine performs coarse intent classification (7 categories) but this is used for ensemble weighting, not evaluation stratification.

---

### 1.3 Language Bias

**Description:** The Quora dataset is exclusively English. Moreover, it represents a specific register of English — written, edited, formal-to-semi-formal questions. Dialectal variation (AAVE, Indian English, British English spellings), code-switching, and non-native constructions are minimally represented. The preprocessing pipeline (`normalize_question`) hardcodes English-specific abbreviation expansions ("what's" → "what is") and typo corrections, making it language-dependent.

**Severity:** HIGH

**Mitigation Strategy:**
- Develop language-agnostic preprocessing via Unicode-aware normalization without language-specific rules
- Add multilingual evaluation sets (Arabic, Chinese, Spanish, French Q&A datasets)
- Implement language detection and language-specific routing in the ensemble
- Evaluate cross-lingual zero-shot transfer (model trained on English → tested on other languages)

**Current ARES Status:** The system is English-only. All linguistic engines (negation, contradiction, entity, intent, lexical) use English-specific regex patterns and NLTK resources. No multilingual capability exists.

---

### 1.4 Temporal Bias

**Description:** Quora questions from 2016 capture language usage patterns, named entities (companies, products, people), and cultural references from nearly a decade ago. Temporal drift includes: new terminology ("GPT", "blockchain", "metaverse"), changing entity references (pre- and post-acquisition company names), and evolving linguistic conventions. A model trained on 2016 data will misinterpret questions referencing entities that did not exist at training time.

**Severity:** MEDIUM

**Mitigation Strategy:**
- Collect temporally stratified test sets (year-bucketed evaluation)
- Implement temporal generalization metrics (performance gap between in-period and out-of-period test splits)
- Design temporal fine-tuning protocols (continuous learning on time-shifted data)
- Use entity-agnostic representations (mask named entities during encoding)

**Current ARES Status:** No temporal analysis exists. The system does not track data collection dates or evaluate temporal generalization. Entity detection exists in `_linguistics/entity.py` but is regex-based, not capable of temporal entity resolution.

---

## 2. Annotation Noise

### 2.1 Label Quality

**Description:** Quora labels were collected through a heuristic process, not expert annotation. The definition of "duplicate" on Quora is inherently subjective — questions may be semantically identical but ask about different instances ("What is the best laptop under $1000?" vs "What is the best laptop under $800?"). The annotation process used inter-annotator agreement filtering but the exact IAA thresholds and annotation guidelines are not publicly documented. No gold-standard expert re-annotation exists for the test set.

**Severity:** HIGH

**Mitigation Strategy:**
- Conduct expert re-annotation of a 5,000-pair sample with 3 annotators and documented guidelines
- Estimate label noise rate via repeated annotation and EM-based noise estimation
- Implement noise-aware loss functions (e.g., bootstrapping, label smoothing, loss reweighting)
- Report accuracy upper bound estimates given estimated noise floor
- Publish error analysis with confusion categories that distinguish model errors from label errors

**Current ARES Status:** Error analysis (`_evaluation/error_analysis.py`) categorizes errors by linguistic phenomenon but does not differentiate label errors from model errors. No re-annotation has been performed.

---

### 2.2 Inter-Annotator Agreement

**Description:** The original Quora dataset reports using "raters" but does not publish per-pair agreement statistics, annotator counts, or adjudication procedures. Known ambiguous cases (questions that are semantically related but not strictly duplicates, questions differing by a single word that changes meaning) receive unreliable labels. The reported 37% duplicate rate may reflect annotation bias toward labeling pairs as non-duplicate when uncertain.

**Severity:** HIGH

**Mitigation Strategy:**
- Design an ambiguity taxonomy (7+ categories: entity difference, scope difference, intent match but instance mismatch, etc.)
- Obtain multiple annotations per pair for a stratified sample
- Compute agreement statistics (Krippendorff's alpha, Cohen's kappa) per ambiguity category
- Train models to predict annotation uncertainty (learn which pairs are inherently ambiguous)
- Implement abstention mechanisms for high-uncertainty inputs

**Current ARES Status:** Ambiguity categories are used in error analysis output but not as a training signal. No multi-annotator ground truth exists.

---

### 2.3 Ambiguous Pairs

**Description:** Many Quora pairs are genuinely ambiguous. Examples include: questions that differ by negation ("Is X good?" vs "Is X not good?"), questions with plural/singular differences, questions with subtle entity variations. For these pairs, even human judgment shows low agreement. Training a model to produce a single binary label for ambiguous pairs forces the model to learn a hard boundary where none exists. This degrades calibration and produces overconfident predictions.

**Severity:** MEDIUM

**Mitigation Strategy:**
- Convert the task to soft labeling (probability of duplicate based on annotator vote distribution)
- Implement ordinal regression or three-class formulation (duplicate / ambiguous / non-duplicate)
- Design a reject option: defer ambiguous predictions to a separate process (LLM judge, human review)
- Evaluate calibration specifically on the ambiguity-stratified subset

**Current ARES Status:** The system produces binary predictions with calibrated probabilities. Ambiguity is detected implicitly via low ensemble agreement (available in `_explainability/agreement_dashboard.py`) but not elevated to a first-class output.

---

## 3. Overfitting

### 3.1 Model Capacity vs. Dataset Size

**Description:** The ARES ensemble includes models ranging from ~5K parameters (TF-IDF + LR) to 184M parameters (DeBERTa-v3). The 323K training pairs provide approximately 1.75 pairs per parameter for DeBERTa-v3 when trained from scratch (though fine-tuning from a pre-trained checkpoint reduces effective capacity). The ensemble itself has no additional trained parameters (weights are computed dynamically), reducing overfitting risk. However, the bi-encoders (110M–118M parameters) and cross-encoders (184M) face a non-trivial parameter-to-example ratio.

**Severity:** MEDIUM

**Mitigation Strategy:**
- Compute and report effective parameter counts (trainable parameters per model)
- Measure generalization gap (train vs. test performance) for every model
- Implement progressive overfitting checks during training (early stopping on held-out validation)
- Apply stronger regularization (dropout, weight decay, label smoothing) for high-capacity models
- Compare generalization curves across model families

**Current ARES Status:** DistilBERT uses 3 epochs with early stopping. No systematic generalization gap analysis exists across all 11 models. Training scripts set weight decay but values were not tuned per model.

---

### 3.2 Hyperparameter Tuning

**Description:** Hyperparameters across the 11 models were tuned with varying rigor:
- **TF-IDF + LR/SVM:** Default scikit-learn parameters. No grid search conducted.
- **DistilBERT:** Learning rate (2e-5), batch size (32), epochs (3) — standard defaults from DistilBERT literature, not empirically tuned on this dataset.
- **Bi-encoders:** Frozen embeddings with LR heads — only the LR head parameters were tuned.
- **Cross-encoders:** Training scripts use FP16 and fused AdamW with default learning rates.
- **Ensemble:** No hyperparameters (weights are computed, not learned).

The lack of systematic hyperparameter optimization means:
- Reported performance may understate achievable accuracy
- Comparisons between models are confounded by differential tuning effort
- The best hyperparameters for individual models may differ from ensemble-optimal settings

**Severity:** HIGH

**Mitigation Strategy:**
- Implement a unified hyperparameter search framework (Optuna/Ray Tune) with search spaces per model type
- Use nested cross-validation for hyperparameter selection
- Conduct ablation studies on each hyperparameter dimension
- Report sensitivity analyses for critical hyperparameters (learning rate, batch size, warmup steps)
- Freeze search spaces and seeds in experiment tracking

**Current ARES Status:** Research readiness report rates hyperparameter search at 2/10. No search framework exists.

---

### 3.3 Multiple Comparison Problem

**Description:** The ARES system exposes 11 models, 2 ensemble strategies (v1, v2), 2 calibration methods (v1, v2), 4 explanation levels, and configurable thresholds. When reporting results, selecting the best-performing configuration from this combinatorial space inflates reported performance. Without correction, the probability of finding a _spuriously_ good configuration is non-trivial.

**Severity:** MEDIUM

**Mitigation Strategy:**
- Designate a single held-out test set used for _final_ evaluation only
- Use a validation set for all configuration selection; report test performance as the single definitive number
- Apply multiple comparison corrections (Bonferroni, Holm, Benjamini-Hochberg) when reporting multiple model comparisons
- Pre-register evaluation protocols (which models, which thresholds, which metrics)
- Use bootstrap hypothesis testing for pairwise model comparisons

**Current ARES Status:** The system has train/val/test splits and config-driven thresholds, providing partial protection. However, no formal multiple comparison correction is applied, and the same test set may have been used iteratively during development.

---

## 4. Evaluation Bias

### 4.1 Metric Selection

**Description:** Accuracy (83%) is reported as the primary metric, but it is problematic for the Quora dataset: with 37% duplicate prevalence, a trivial "always non-duplicate" baseline achieves 63% accuracy. F1, MCC, and AUC provide more informative comparisons. Additionally, the choice of metric implicitly weights different error types — F1 weights precision and recall equally, but different applications require different trade-offs (e.g., content moderation may prioritize precision; information retrieval may prioritize recall).

**Severity:** MEDIUM

**Mitigation Strategy:**
- Report a standardized metric suite: Accuracy, Precision, Recall, F1, MCC, ROC-AUC, PR-AUC, ECE, Brier Score
- Include cost-sensitive metrics (weighted F-beta with application-specific beta)
- Report all metrics with 95% confidence intervals (bootstrap)
- Pre-specify primary and secondary metrics in evaluation protocols
- Implement utility-based evaluation: given a cost matrix, compute expected cost per application

**Current ARES Status:** `_evaluation/metrics.py` computes a comprehensive metric suite including Accuracy, Precision, Recall, F1, MCC, Specificity, NPV, ROC-AUC, PR-AUC, ECE, MCE, and Brier Score. However, the Streamlit UI primarily displays accuracy. Confidence intervals are not implemented.

---

### 4.2 Threshold Optimization

**Description:** Per-model thresholds in `configs/inference.yaml` were tuned on the validation set to optimize F1. While standard practice, this creates an optimism bias: the selected threshold is optimal for the validation set but not necessarily for the test set or deployment distribution. Different threshold optimization criteria (Youden's J, MCC, F-beta) produce different thresholds and different conclusions about model ranking.

**Severity:** MEDIUM

**Mitigation Strategy:**
- Report threshold-independent metrics (ROC-AUC, PR-AUC) alongside threshold-dependent ones
- Implement threshold optimization via cross-validation (not single validation split)
- Report performance at multiple operating points (threshold sweep)
- Use Platt scaling or isotonic regression for well-calibrated probabilities independent of threshold
- For deployment, design a threshold selection procedure based on application-specific cost-benefit analysis

**Current ARES Status:** Threshold tuning is implemented in `_evaluation/metrics.py` with F1, Youden's J, and MCC optimization. Per-model thresholds are configurable. The system calibrates probabilities but does not evaluate threshold sensitivity.

---

### 4.3 Test Set Leakage

**Description:** The 80/10/10 stratified split is reproducible but risks information leakage in several forms:
- **Data preprocessing:** `normalize_question()` was developed and refined using the full dataset (including test set distribution statistics)
- **Model selection:** The same test set may have been used for error analysis that informed model improvements (iterative, even if unintentional)
- **Ensemble design:** The ensemble v1/v2 design and linguistic feature selection were informed by error patterns observed in the test set
- **Sigmoid calibration parameters:** Calibrated on the validation set, but calibration parameter search may have been informed by test set performance

**Severity:** MEDIUM

**Mitigation Strategy:**
- Implement strict data partitioning: test set is write-once, accessed only for final evaluation
- Use a hidden test set (separate file, loaded only during evaluation)
- If iterative development requires test set access, use a three-way split (train/val/test) with a separate held-out "challenge set"
- Document all points of test set contact in the research notebook
- Implement integrity checks: verify test set has not been used in training features

**Current ARES Status:** The system has a clean train/val/test split but no mechanisms to prevent iterative test set leakage. Calibration parameters are learned on the validation set.

---

## 5. Domain Shift

### 5.1 Generalization from Q&A to Other Text Types

**Description:** ARES is trained on Quora question pairs and its sentence transformers encode questions. The system has never been evaluated on:
- **Customer support tickets:** "My order hasn't arrived" vs "Where is my package"
- **Legal documents:** "The defendant asserts" vs "The accused argues"
- **Medical notes:** "Patient presents with dyspnea" vs "SOB reported by patient"
- **News headlines:** "Markets Rally on Fed Decision" vs "Stock Surge After Rate Announcement"
- **Social media posts:** "omg this is so me" vs "literally me rn"

Each domain has different conventions for semantic equivalence, different vocabulary distributions, and different noise characteristics.

**Severity:** HIGH

**Mitigation Strategy:**
- Curate multi-domain evaluation benchmarks (at minimum 5 domains beyond Q&A)
- Implement domain adaptation protocols: domain-adaptive pre-training, domain-adversarial training
- Evaluate per-domain calibration (ECE varies significantly across domains even with similar accuracy)
- Design domain-agnostic linguistic features (cross-domain entity patterns, generic contradiction detection)
- Build domain classifiers for automatic dataset attribution

**Current ARES Status:** Cross-domain evaluation has not been conducted. The system assumes text input but carries Q&A-specific assumptions (e.g., intent detection categories are question-specific: factual, how-to, opinion, etc.).

---

### 5.2 Cross-Lingual Transfer

**Description:** ARES operates exclusively in English. The linguistic engines use English-specific regex. The sentence transformers (BGE, E5, MPNet, LaBSE) have multilingual variants, but ARES uses English-only versions. Cross-lingual transfer — training on English, testing on other languages — has not been explored. Even with multilingual encoders, the linear classification heads and linguistic engines would fail on non-English input.

**Severity:** HIGH

**Mitigation Strategy:**
- Replace English-only linguistic engines with multilingual alternatives (or language-agnostic features)
- Integrate multilingual sentence encoders (LaBSE, multilingual E5, XLM-R)
- Build cross-lingual evaluation sets: parallel question pairs in 5+ languages
- Evaluate zero-shot cross-lingual transfer (train English → test languages)
- Implement language detection and language-specific routing

**Current ARES Status:** No multilingual capability. The `_preprocessing/text.py` normalization is English-specific. Linguistic engines fail on non-English input.

---

### 5.3 Temporal Drift

**Description:** Language evolves. A model frozen in 2026 will experience:
- **Lexical drift:** New words and phrases enter common usage
- **Entity drift:** Companies, products, people referenced in questions change
- **Semantic drift:** Word meanings shift (e.g., "viral" originally biological, now primarily digital)
- **Pragmatic drift:** Question-asking conventions evolve on platforms
- **Platform drift:** If deployed on a different platform, the distribution shifts

**Severity:** MEDIUM

**Mitigation Strategy:**
- Implement drift detection on prediction distributions (population stability index, PSI)
- Create temporal hold-out sets (evaluate on time-shifted data)
- Design online adaptation protocols (lightweight fine-tuning on fresh data)
- Build a monitoring dashboard for production drift metrics
- Schedule periodic re-training with data freshness weighting

**Current ARES Status:** No drift detection or monitoring. All models are static. No data freshness tracking exists.

---

## 6. Fairness

### 6.1 Performance Disparities Across Topics

**Description:** Different question topics may exhibit different duplicate detection accuracy. Topics with more training examples (technology, science) are expected to outperform low-resource topics (arts, humanities). Moreover, topic-correlated linguistic features (e.g., technical jargon vs. colloquial language) interact differently with the linguistic engines and ensemble weights. Without topic-stratified evaluation, the reported aggregate accuracy may mask significant disparities.

**Severity:** MEDIUM

**Mitigation Strategy:**
- Build a topic taxonomy (at least 10 coarse categories with hierarchical fine-grained labels)
- Annotate the test set with topic labels
- Report per-topic performance (accuracy, F1, ECE) and identify statistically significant disparities
- Implement topic-adaptive inference (different models or thresholds per topic cluster)
- Collect supplementary data for low-performing topics

**Current ARES Status:** Intent detection exists but operates at 7 categories designed for linguistic analysis, not fairness auditing. No topic-stratified evaluation.

---

### 6.2 Performance Disparities Across Languages

**Description:** If ARES were extended to multilingual input (see Section 5.2), performance disparities across languages would be a critical concern. Languages with more training data (English, high-resource) would outperform low-resource languages. Code-switched or dialectal variants would perform worst. Disparities compound when the system is used for content moderation or information access — users of low-resource languages receive inferior service.

**Severity:** HIGH (if multilingual; MEDIUM for current English-only scope)

**Mitigation Strategy:**
- Establish minimum performance standards across all supported languages
- Implement language-specific calibration to equalize confidence calibration across languages
- Use language-identification-based routing to select language-appropriate models
- Prioritize data collection for low-resource languages
- Regularly audit for language-based performance disparities

**Current ARES Status:** Not applicable (English-only). However, this becomes a HIGH-priority threat if multilingual extension is pursued.

---

### 6.3 Performance Disparities Across Demographic Groups

**Description:** Although the Quora dataset does not contain explicit demographic information, proxy variables exist:
- **Named entities:** Questions about different cultural touchstones may correlate with user demographics
- **Register differences:** Formal vs. informal question construction correlates with educational background
- **Dialectal features:** Non-standard grammatical constructions may correlate with dialect or non-native status

Models trained to detect duplicates may systematically underperform on questions from underrepresented linguistic communities, creating differential system quality.

**Severity:** HIGH

**Mitigation Strategy:**
- Partner with sociolinguists to identify dialectal variation in the test set
- Conduct fairness audits using proxy-based disparity measurement
- Implement bias mitigation: re-weight training data, adversarial debiasing, or post-hoc calibration adjustment
- Collect and annotate dialectally diverse question pairs
- Publish fairness statements with every model release

**Current ARES Status:** No fairness analysis exists. Demographic proxy variables are not tracked. No bias mitigation is implemented.

---

## 7. Ethical Risks

### 7.1 Surveillance Applications

**Description:** Semantic duplicate detection can be repurposed for surveillance: monitoring communication channels for repeated content, identifying coordinated messaging, tracking topic propagation across accounts. In authoritarian contexts, such capabilities enable censorship, political repression, and human rights violations. Even benign deployment can lead to unforeseen surveillance use through API access or model replication.

**Severity:** HIGH

**Mitigation Strategy:**
- Include clear use-case restrictions in model licenses (AI2's RAIL license or similar)
- Publish model cards that document intended use and prohibited use cases
- Implement API-level guardrails (rate limiting, content policy enforcement)
- Engage with ethics review boards before deployment in sensitive contexts
- Consider watermarking or fingerprinting models to deter unauthorized use

**Current ARES Status:** No usage restrictions are documented. The MIT License permits unrestricted use. No model card exists.

---

### 7.2 Content Moderation Biases

**Description:** Duplicate detection has direct applications in content moderation: detecting repeated harmful content, spam, coordinated inauthentic behavior. However, duplicate detection can be used to:
- Disproportionately moderate content from marginalized communities (whose questions may be incorrectly flagged as duplicates of each other)
- Suppress protest coordination by identifying repeated organizing messages
- Automate takedowns at scale without human oversight, amplifying algorithmic errors

The system's higher error rates on linguistically diverse input (see Section 6.3) compound these risks.

**Severity:** HIGH

**Mitigation Strategy:**
- Conduct content moderation stress tests: evaluate system behavior on hypothetical moderation scenarios
- Implement human-in-the-loop requirements for any moderation-related use
- Publish system limitations prominently when deploying in moderation contexts
- Ensure transparency: explain why content was flagged (leveraging existing explainability infrastructure)
- Build appeal mechanisms for automated decisions

**Current ARES Status:** Explainability infrastructure exists (4 levels of text explanations) but is designed for debugging, not for due process in moderation.

---

### 7.3 Manipulation Risks

**Description:** Semantic duplicate detection systems can be used to:
- **Generate adversarial duplicates:** Craft questions that evade duplicate detection (adversarial evasion)
- **Detect plagiarism too well:** Identify duplicate questions as a proxy for identifying duplicate content more broadly, enabling unauthorized surveillance
- **Game systems:** Understand duplicate detection patterns to manipulate platform algorithms (e.g., SEO manipulation by generating sufficiently distinct versions of the same question)

**Severity:** MEDIUM

**Mitigation Strategy:**
- Conduct adversarial robustness evaluations (text perturbation attacks, paraphrasing attacks)
- Implement adversarial training or certified defense mechanisms
- Develop system-level safeguards (input validation, anomaly detection)
- Publish a red-teaming report
- Monitor for systematic exploitation patterns

**Current ARES Status:** No adversarial robustness evaluation exists. `_preprocessing/text.py` applies basic normalization that is easily bypassed. No adversarial training.

---

## 8. Limitations

### 8.1 Computational Constraints

**Description:** The ARES system faces several practical computational limitations:
- **Ensemble latency:** Full ensemble inference takes 2–5 seconds per pair (loading 9+ models sequentially)
- **Memory footprint:** Loading all models simultaneously requires 2–4 GB RAM (CPU inference) or 4–8 GB VRAM (GPU inference)
- **Cold start:** First prediction requires loading models from disk (1–10 seconds per model)
- **No GPU acceleration:** Current deployment is CPU-only for the Streamlit app; GPU inference is experimental
- **Scaling:** Single-process architecture cannot handle concurrent requests without queuing

**Severity:** HIGH

**Mitigation Strategy:**
- Implement model distillation (train a smaller student model on ensemble predictions)
- Use model quantization (INT8/FP16) for production deployment
- Implement predictive loading (pre-load models based on predicted usage)
- Separate model serving from application (FastAPI + model workers)
- Benchmark latency-per-model and publish performance budgets

**Current ARES Status:** Latency is measured per-model and reported in inference output. Caching is implemented for embeddings and preprocessing. No quantization, distillation, or distributed serving.

---

### 8.2 Model Scope

**Description:** ARES solves the narrow task of binary duplicate question detection. It does not:
- Generate explanations for _why_ questions are duplicates (only descriptive traces)
- Handle multi-question inputs (threads, conversations)
- Distinguish between exact duplicates, near-duplicates, and topically related pairs
- Operate on non-question text
- Provide graded similarity scores (binary only, though probabilities exist)
- Support incremental predictions (adding new questions to existing analysis)

**Severity:** MEDIUM

**Mitigation Strategy:**
- Extend task formulation to graded similarity (fine-grained duplicate categories)
- Add multi-input capabilities (n-way comparison, cluster detection)
- Develop generative explanation capabilities (natural language justification for predictions)
- Expand to non-Q&A text types
- Build incremental and streaming inference modes

**Current ARES Status:** Binary classification. Probabilities are available but not used for graded decisions. Explainability provides descriptive traces, not generative explanations.

---

### 8.3 Evaluation Scope

**Description:** The current evaluation has several scoping limitations:
- **Single dataset:** All metrics are on the Quora test split
- **Single task:** Binary duplicate detection only
- **Single language:** English only
- **Fixed split:** Single train/val/test split (no cross-validation)
- **No human baseline:** No comparison to human performance on the test set
- **No longitudinal evaluation:** No tracking of performance over time or across model versions
- **Limited robustness testing:** Only standard accuracy/correctness; no adversarial or out-of-distribution evaluation

**Severity:** HIGH

**Mitigation Strategy:**
- Establish multi-dataset evaluation benchmark (5+ datasets)
- Add cross-validation for more robust performance estimates
- Establish human performance baseline (expert annotation of a 2,000-pair test subset)
- Implement continuous evaluation pipeline across model versions
- Add robustness benchmarks (adversarial, OOD, and stress tests)

**Current ARES Status:** Evaluation is comprehensive within its scope (multiple metrics, error analysis, hard mining) but narrow in coverage. No human baseline. No OOD evaluation.

---

### 8.4 Reproducibility Constraints

**Description:** Several factors limit full reproducibility of ARES results:
- **Random seeds:** Configurable but not enforced as deterministic across all operations
- **Library versions:** Broad version ranges in `pyproject.toml` (e.g., `torch>=2.0.0`)
- **GPU non-determinism:** `torch.use_deterministic_algorithms(True)` not enabled
- **Data versioning:** No dataset hash or checksum tracking
- **Environment:** No containerization (Dockerfile does not exist)
- **Model checkpoints:** HuggingFace Hub caching means models may load different checkpoint versions on different machines
- **Experiment tracking:** No MLflow/W&B — results exist in notebooks, console output, and saved artifacts

**Severity:** MEDIUM

**Mitigation Strategy:**
- Add deterministic training mode with seed locking and algorithm constraints
- Pin exact library versions (`pyproject.toml` with locked dependencies)
- Implement Docker containerization (Dockerfile + docker-compose)
- Track data hash, model hash, and experiment config for every run
- Integrate experiment tracking (MLflow or W&B)
- Automate evaluation pipeline with reproducible configuration snapshotting

**Current ARES Status:** Research readiness report rates reproducibility at 4/10. Seeds are configurable but not deterministically enforced. No Docker, no data versioning, no experiment tracking.

---

## 9. Summary Threat Matrix

| Threat | Severity | Current Mitigation | Recommended Priority | Effort |
|---|---|---|---|---|
| Dataset Bias — Characteristics | HIGH | None | P0 — Critical | 3 months |
| Dataset Bias — Topic Distribution | HIGH | Intent detection (partial) | P0 — Critical | 2 months |
| Dataset Bias — Language | HIGH | None | P0 — Critical | 6 months |
| Dataset Bias — Temporal | MEDIUM | None | P1 — High | 1 month |
| Annotation Noise — Label Quality | HIGH | None | P0 — Critical | 3 months |
| Annotation Noise — Inter-Annotator Agreement | HIGH | None | P1 — High | 2 months |
| Annotation Noise — Ambiguous Pairs | MEDIUM | Agreement dashboard | P1 — High | 2 months |
| Overfitting — Model Capacity | MEDIUM | Early stopping, regularization | P2 — Medium | 1 month |
| Overfitting — Hyperparameter Tuning | HIGH | None | P0 — Critical | 2 months |
| Overfitting — Multiple Comparison | MEDIUM | Train/val/test splits | P2 — Medium | 2 weeks |
| Evaluation Bias — Metric Selection | MEDIUM | Comprehensive metric suite | P2 — Medium | 2 weeks |
| Evaluation Bias — Threshold Optimization | MEDIUM | Configurable thresholds | P2 — Medium | 1 month |
| Evaluation Bias — Test Set Leakage | MEDIUM | Clean split (partial) | P1 — High | 2 weeks |
| Domain Shift — Q&A to Other Text | HIGH | None | P0 — Critical | 6 months |
| Domain Shift — Cross-Lingual Transfer | HIGH | None | P0 — Critical | 6 months |
| Domain Shift — Temporal Drift | MEDIUM | None | P1 — High | 3 months |
| Fairness — Topic Disparities | MEDIUM | None | P1 — High | 2 months |
| Fairness — Language Disparities | HIGH | None (English-only) | P0 — Critical | 6 months |
| Fairness — Demographic Disparities | HIGH | None | P0 — Critical | 6 months |
| Ethical Risks — Surveillance | HIGH | None | P0 — Critical | 1 month |
| Ethical Risks — Content Moderation | HIGH | Explainability (partial) | P0 — Critical | 3 months |
| Ethical Risks — Manipulation | MEDIUM | None | P1 — High | 3 months |
| Computational Constraints | HIGH | Caching (partial) | P1 — High | 4 months |
| Model Scope | MEDIUM | Explainability (partial) | P2 — Medium | 6 months |
| Evaluation Scope | HIGH | None | P0 — Critical | 4 months |
| Reproducibility Constraints | MEDIUM | Config-driven design | P1 — High | 2 months |

---

## 10. Future Work to Address Threats

### Near-Term (0–6 Months)
1. **Multi-source data collection:** Curate 3+ additional datasets (Stack Exchange, Reddit, customer support)
2. **Expert re-annotation:** Label 5,000 pairs with 3 annotators and documented guidelines
3. **Hyperparameter search framework:** Implement Optuna-based search for all model types
4. **Confidence intervals:** Bootstrap-based uncertainty for all evaluation metrics
5. **Topic-stratified evaluation:** Build topic taxonomy and annotate test set
6. **Reproducibility infrastructure:** Docker, pinned dependencies, deterministic mode
7. **Human baseline:** Establish expert performance on test subset

### Mid-Term (6–18 Months)
8. **Cross-domain evaluation:** Build and evaluate on 5+ non-Q&A benchmarks
9. **Multilingual linguistic engines:** Replace English-specific regex with multilingual/NLI-based analysis
10. **Adversarial robustness:** Evaluate and improve against text perturbations
11. **Online drift detection:** PSI-based monitoring for deployment shifts
12. **Fairness auditing framework:** Systematic disparity measurement across proxy groups
13. **Model distillation:** Train efficient student model from ensemble
14. **Model cards and ethical documentation:** Publish use-case restrictions

### Long-Term (18–36 Months)
15. **Multilingual extension:** Support 10+ languages with language-specific calibration
16. **Cross-lingual transfer:** Zero-shot and few-shot cross-lingual duplicate detection
17. **Temporal adaptation:** Continuous fine-tuning on fresh data with drift-aware scheduling
18. **Generative explanations:** Natural language justification for predictions using LLMs
19. **Demographic fairness:** Partnership with sociolinguists for dialect-aware evaluation and mitigation
20. **Certified robustness:** Formal verification of behavior on bounded input perturbations
21. **Open challenge benchmark:** Release a multi-domain, multi-lingual duplicate detection benchmark with hidden test set

---

*This document is part of the ARES research documentation suite. Maintained as a living document — threats and mitigations should be updated as the system evolves.*
