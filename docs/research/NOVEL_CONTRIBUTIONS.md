# Novel Contributions

## Defining the Scientific and Technical Contributions of ARES

---

### Preamble: What Counts as Novel

In a research landscape dominated by incremental improvements — larger models, more data, slightly better hyperparameters — it is essential to be precise about what constitutes a genuine contribution. ARES does not claim novelty from using BERT, from training on Quora QQP, or from achieving a marginally better F1 score.

ARES claims novelty in **architecture, methodology, and system-level design**. The contributions described below are novel because they address problems that prior work has either not addressed or has addressed only partially, and because they demonstrate measurable improvements in accuracy, calibration, explainability, or robustness that cannot be attributed to scale alone.

---

### Contribution 1: Adaptive Cognitive Routing

#### The Problem
Standard ensembles apply the same combination strategy to all inputs. Weighted averaging, stacked generalization, and even mixture-of-experts learn a fixed routing function that does not adapt to the linguistic properties of each input pair.

#### The Idea
ARES introduces **Adaptive Cognitive Routing**: a two-stage mechanism that (a) extracts discrete linguistic features from each question pair (lexical overlap, semantic depth, abbreviations, synonyms), and (b) uses these features to compute dynamic model weights via interpretable rules. The routing function is not learned but designed, grounded in linguistic theory and empirical observation.

In V1, four model-group weights (lexical, transformer, embedding, cross-encoder) are adjusted as functions of five input features. In V2, ten explicit routing rules incorporate all five linguistic engines, with the final probability further adjusted by learned penalties.

#### Expected Benefit
- Higher accuracy on diverse input types compared to any fixed-weight ensemble
- Graceful handling of edge cases (contradiction pairs, negation pairs, entity mismatches)
- Interpretable routing decisions that can be explained to users

#### Evaluation Methodology
- Compare against baselines: unweighted average, fixed-weight average (optimized on validation set), stacked meta-classifier, best individual model
- Primary metrics: F1, precision, recall, ROC-AUC
- Secondary metrics: per-category accuracy on linguistically-stratified test subsets
- Statistical test: McNemar's test for paired label comparisons

#### Relation to Existing Work
- **Mixture of Experts (Jacobs et al., 1991)** : Unlike MoE, ARES routing is explicitly designed and interpretable, not learned via a black-box gating network. There is no routing collapse because the routing features are independent of model performance.
- **Dynamic Ensemble Selection (Cruz et al., 2018)** : DES methods select one model per input. ARES computes continuous weights across all models, combining their strengths rather than committing to a single model.
- **Confidence-based weighting** : Standard in ensemble literature. ARES goes beyond confidence to incorporate linguistic features that are orthogonal to confidence.

---

### Contribution 2: Multi-Agent Semantic Debate

#### The Problem
In standard ensembles, models vote independently and their predictions are aggregated. There is no mechanism for one model's output to influence another's, even when disagreement signals a potential error.

#### The Idea
ARES implements **Multi-Agent Semantic Debate** through its agreement analysis engine. Rather than treating models as independent voters, the system:
- Collects predictions from all 11 models
- Computes agreement statistics (majority ratio, confidence spread, prediction entropy, probability variance)
- Adjusts the final confidence based on disagreement patterns
- Routes high-disagreement cases through additional scrutiny (cross-encoder prioritization, linguistic penalty reweighting)

This creates a weak form of debate: models that disagree with the majority are implicitly penalized in the final vote weighting. The disagreement signal is used to calibrate the ensemble's confidence, not just to aggregate predictions.

#### Expected Benefit
- Reduced overconfidence on ambiguous inputs
- Trustworthy confidence estimates that reflect genuine model uncertainty
- Natural mechanism for selective prediction (abstain when disagreement is too high)

#### Evaluation Methodology
- Compare agreement-aware confidence versus raw ensemble probability for error prediction (AUC)
- Measure selective prediction: abstain on bottom X% of agreement, evaluate accuracy on remaining predictions
- Ablation: remove disagreement-based adjustments, measure calibration degradation

#### Relation to Existing Work
- **Bayesian Deep Learning (Gal & Ghahramani, 2016)** : Provides uncertainty estimates from dropout. ARES uncertainty is derived from ensemble disagreement, which captures a different form of uncertainty (structural/model uncertainty rather than parameter uncertainty).
- **Deep Ensembles (Lakshminarayanan et al., 2017)** : Propose ensembles for uncertainty. ARES extends this by making the uncertainty estimate itself a feature for downstream calibration.
- **Prediction Rejection (Hendrickx & Scheunders, 2020)** : Standard selective prediction uses confidence threshold. ARES uses agreement threshold, which our hypothesis predicts is more reliable.

---

### Contribution 3: Semantic Memory Cache

#### The Problem
Virtually all deployed duplicate detection systems are stateless. Every prediction is computed from scratch, even for identical or near-identical question pairs. Repeated computation wastes resources and provides no mechanism for learning from past experience.

#### The Idea
ARES introduces a **Semantic Memory Cache** — a persistent, thread-safe LRU cache that stores:
- Embeddings (keyed by model name + text hash)
- Preprocessing outputs (normalized text)
- Model predictions and their associated features

The cache is not merely a performance optimization. It is the foundation for:
- **Experience-weighted routing**: Models that have been reliable on similar inputs in the past can be prioritized
- **Pattern discovery**: Historical cache statistics reveal which model classes are most consulted and most trusted
- **Continuous improvement**: Cache hit/miss statistics inform system optimization

#### Expected Benefit
- 40%+ latency reduction on workloads with repeated inputs (hypothesis H13)
- Foundation for future learning-based routing improvements
- System telemetry without additional instrumentation

#### Evaluation Methodology
- Synthetic repeated-input workload (50% repetition rate)
- Measure: latency reduction, hit rate, cache miss penalty
- Validate: prediction consistency on cache hits (no accuracy degradation)

#### Relation to Existing Work
- **LRU Caching**: Standard in systems research. ARES applies it to semantic embeddings with model-aware key design and thread-safe access.
- **MemN2N (Sukhbaatar et al., 2015)** : Neural memory networks. ARES memory is symbolic and transparent, not learned.
- **Cache-Augmented Models (Grave et al., 2016)** : Cache for language modeling. ARES caches at the system level, not the model level.

---

### Contribution 4: Cognitive Decision Pipeline

#### The Problem
Most NLP systems are pipelines, but they are *monolithic* pipelines: input → model → output. There is no intermediate representation, no branching, no conditional logic based on intermediate results.

#### The Idea
ARES implements a **Cognitive Decision Pipeline** — a multi-stage architecture where each stage produces structured intermediate representations that inform subsequent stages:

1. **Preprocessing Stage**: Normalize, cache
2. **Linguistic Feature Extraction Stage**: Entity detection, intent classification, contradiction detection, negation detection, lexical analysis → structured feature vectors
3. **Model Inference Stage**: Query all 11 models (with caching) → structured model votes
4. **Agreement Analysis Stage**: Compute agreement statistics from votes
5. **Adaptive Weighting Stage**: Compute dynamic weights from linguistic features + agreement statistics
6. **Penalty Application Stage**: Apply linguistic penalties to weighted probability
7. **Calibration Stage**: Per-model and ensemble-level calibration
8. **Explainability Stage**: Generate decision trace, plain-English explanation, counterfactuals

Each stage produces an inspectable, serializable output. The pipeline can be stopped, inspected, or redirected at any stage.

#### Expected Benefit
- Complete auditability: every intermediate representation is preserved
- Modularity: stages can be improved independently
- Debuggability: errors can be traced to specific stages
- Extensibility: new stages can be inserted without modifying existing ones

#### Evaluation Methodology
- Ablation: remove each stage, measure impact on accuracy and explainability
- Latency profiling: measure per-stage contribution to total latency
- Qualitative: human evaluation of intermediate representations for interpretability

#### Relation to Existing Work
- **Standard ML Pipelines (e.g., sklearn pipelines)** : Fixed sequence of transformations with no conditional logic or feedback. ARES pipeline includes agreement analysis that feeds back into weighting.
- **Neuro-Symbolic Systems**: ARES bridges neural (transformer models) and symbolic (linguistic engines) in a unified pipeline, unlike purely neural or purely symbolic systems.
- **Transformer-only pipelines (e.g., HuggingFace pipelines)** : End-to-end neural. ARES maintains structured intermediate representations for interpretability.

---

### Contribution 5: Trust-Aware Prediction

#### The Problem
Standard systems produce a prediction and a confidence score. The confidence score is typically the raw model probability, which is poorly calibrated and does not reflect model uncertainty.

#### The Idea
ARES introduces **Trust-Aware Prediction**: a prediction is accompanied by a *trust score* that integrates:
- **Ensemble agreement**: How many models agree with the prediction
- **Confidence spread**: How much model confidences vary
- **Prediction entropy**: How evenly votes are distributed
- **Linguistic certainty**: Whether detected linguistic features (entity mismatch, contradiction) are consistent with the prediction

The trust score is a composite measure that serves as a superior alternative to raw confidence for:
- **Selective prediction**: Only return predictions above a trust threshold
- **Human-in-the-loop routing**: Flag low-trust predictions for human review
- **User communication**: Communicate system certainty in natural language ("This is a high-confidence prediction" vs "Our models disagree on this pair")

#### Expected Benefit
- More reliable confidence estimates for production use
- Better human-in-the-loop routing decisions
- Improved user trust through honest uncertainty communication

#### Evaluation Methodology
- Compare trust score vs. raw confidence for error prediction (AUC)
- Measure selective prediction performance: accuracy as function of rejection rate
- User study: does trust-aware communication improve user satisfaction?

#### Relation to Existing Work
- **Conformal Prediction (Vovk et al., 2005)** : Provides prediction sets with coverage guarantees. ARES trust is a continuous score, not a prediction set.
- **Selective Classification (El-Yaniv & Wiener, 2010)** : Standard selective classifiers use confidence. ARES uses a multi-factor trust score.
- **Uncertainty in Deep Learning (Kendall & Gal, 2017)** : Aleatoric vs. epistemic uncertainty. ARES trust score captures both: aleatoric through linguistic features, epistemic through ensemble disagreement.

---

### Contribution 6: Linguistic Penalty Framework

#### The Problem
Neural models encode linguistic information implicitly. They cannot perform exact symbolic matching, cannot detect negation reliably, and cannot recognize contradiction in a compositional way. This leads to characteristic failure modes that are highly predictable but cannot be addressed within the neural paradigm alone.

#### The Idea
ARES introduces the **Linguistic Penalty Framework** — a novel mechanism for incorporating symbolic linguistic knowledge into a neural ensemble:

- **Five penalty sources**: entity mismatch, intent incompatibility, negation mismatch, contradiction, lexical mismatch
- **Each penalty is a function** of symbolic analysis of the input pair, computed by dedicated linguistic engines
- **Penalties are applied multiplicatively** to the ensemble probability, reducing the duplicate score when linguistic evidence contradicts duplicate status
- **Penalties are bounded** (0.0–0.8 cap) and **interpretable** (each penalty includes a natural language explanation)

The framework is designed to be:
- **Extensible**: new penalty sources can be added independently
- **Interpretable**: every penalty has a clear linguistic rationale
- **Composable**: penalties interact multiplicatively, not via learned weights

#### Expected Benefit
- Significant false positive reduction (hypothesis H2: ≥25% reduction)
- Robustness to known neural failure modes (negation, contradiction, entity mismatch)
- Built-in interpretability from penalty explanations

#### Evaluation Methodology
- Ablation: remove each penalty source, measure FP/FN rate impact
- Per-category analysis: evaluate on curated test subsets for each failure mode
- Penalty interaction analysis: are penalties correlated, or do they capture orthogonal signals?

#### Relation to Existing Work
- **NLI-based reranking (Das et al., 2019)** : Use NLI to filter predictions. ARES integrates NLI and symbolic penalties at the ensemble level.
- **Symbolic-Neural Hybrids (Garcez & Lamb, 2020)** : ARES does not train a neuro-symbolic model but orchestrates neural and symbolic components at the system level.
- **Constraint-based NLP (Chang et al., 2007)** : Hard constraints from linguistic structure. ARES penalties are soft (continuous), not hard (binary).

---

### Contribution 7: Agreement-Aware Confidence Estimation

#### The Problem
Standard confidence estimation methods (temperature scaling, Platt scaling) operate on a single model's outputs. They do not condition on the outputs of other models, even though model disagreement is a strong signal of uncertainty.

#### The Idea
ARES introduces **Agreement-Aware Confidence Estimation**: a calibration method that adjusts a model's confidence based on whether it agrees with the ensemble majority.

The intuition is simple:
- If a model agrees with the majority → its confidence is likely well-calibrated → maintain or slightly increase confidence
- If a model disagrees with the majority → its confidence is likely overconfident → reduce confidence via higher temperature

This is operationalized as:
- **Dual-temperature calibration**: fit separate temperatures for agreement and disagreement conditions
- **Agreement-weighted ensemble**: ensemble probability is a function of both model predictions and whether each model agrees with the consensus

#### Expected Benefit
- Reduced ECE compared to single-temperature calibration (hypothesis H18: ≥15% reduction)
- Better separation of high-confidence-correct and high-confidence-incorrect predictions
- More reliable selective prediction

#### Evaluation Methodology
- Fit T_agree and T_disagree per model using agreement labels derived from validation set
- Compare against single-temperature, Platt, and isotonic calibration
- Measure: ECE, MCE, Brier score, reliability diagram

#### Relation to Existing Work
- **Temperature Scaling (Guo et al., 2017)** : Single global temperature. ARES extends this to context-dependent temperature (agreement context).
- **Ensemble Calibration (Mukhoti et al., 2020)** : Calibrate ensemble output directly. ARES calibrates individual models first, conditioned on agreement.
- **Bayesian Model Averaging**: Weight models by posterior probability. ARES agreement-aware weighting is simpler and more interpretable.

---

### Contribution 8: Dynamic Calibration

#### The Problem
Calibration is typically a static post-processing step. A single calibration function is learned and applied to all predictions. However, calibration quality varies across the input space — a model may be well-calibrated on high-overlap pairs but miscalibrated on contradiction pairs.

#### The Idea
ARES introduces **Dynamic Calibration**: calibration that adapts to input characteristics by conditioning on ensemble-level statistics.

The key insight: ensemble disagreement is a proxy for input difficulty. When models disagree, the input is likely challenging, and individual model confidences are less reliable. Dynamic calibration adjusts temperatures accordingly.

This is complementary to Agreement-Aware Confidence Estimation (Contribution 7), which conditions on a specific model's agreement. Dynamic calibration conditions on the **ensemble's aggregate** disagreement level.

#### Expected Benefit
- Input-adaptive calibration that improves over static methods
- Better calibration on difficult inputs where it matters most
- Foundation for continuous calibration in production

#### Evaluation Methodology
- Partition test set by ensemble disagreement level (low/medium/high)
- Compare static vs. dynamic calibration ECE within each partition
- Measure overall ECE improvement

#### Relation to Existing Work
- **Temperature as a function of input**: Some work adjusts temperature based on input difficulty (e.g., Pereyra et al., 2017). ARES uses ensemble disagreement as the conditioning variable.
- **Instance-dependent calibration (Zhao et al., 2021)** : Learn calibration as a function of input features. ARES uses ensemble-level features (agreement), which are more robust than individual input features.

---

### Summary Table

| Contribution | Problem Solved | Key Mechanism | Primary Metric | Novelty Level |
|---|---|---|---|---|
| Adaptive Cognitive Routing | Static ensemble suboptimality | Feature-conditioned dynamic weighting | F1, per-category accuracy | **High** — new paradigm |
| Multi-Agent Semantic Debate | Opaque model disagreement | Agreement analysis + confidence adjustment | Error prediction AUC | **High** — new methodology |
| Semantic Memory Cache | Stateless inference | LRU caching with model-aware keys | Latency reduction | **Medium** — novel application |
| Cognitive Decision Pipeline | Monolithic black-box pipeline | Multi-stage with structured intermediates | Auditability, modularity | **High** — new architecture |
| Trust-Aware Prediction | Unreliable confidence | Multi-factor trust score | Selective prediction accuracy | **High** — new formalism |
| Linguistic Penalty Framework | Neural failure on symbolic patterns | 5 symbolic penalty sources | FP rate reduction | **High** — new framework |
| Agreement-Aware Calibration | Context-independent calibration | Dual-temperature (agree/disagree) | ECE reduction | **Medium-High** — novel extension |
| Dynamic Calibration | Input-independent calibration | Disagreement-conditioned temperature | ECE per difficulty partition | **Medium** — novel application |

---

### Avoiding Common Claims of Novelty

To be clear about what ARES does *not* claim as novel:

| Not Novel | Why |
|---|---|
| "We use BERT/DeBERTa/Transformer models" | These are standard architectures used as components |
| "We achieve state-of-the-art on QQP" | Benchmark results are a function of many factors; SOTA is not claimed without rigorous comparison |
| "We train an ensemble of models" | Ensembles are standard; the adaptation strategy is the novelty |
| "We extract linguistic features" | Feature extraction is standard; the integration with dynamic routing is the novelty |
| "We improve calibration" | Calibration methods are standard; agreement-aware calibration is the novelty |
| "We generate explanations" | Explainability is a known goal; structured decision traces with counterfactuals are the novelty |

---

*These eight contributions define what is genuinely new about ARES. Each is designed to be independently testable, replicable, and improvable. None depend on proprietary data, secret hyperparameters, or unreproducible training procedures.*
