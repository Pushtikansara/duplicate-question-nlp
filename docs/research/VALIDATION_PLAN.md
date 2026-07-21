# Validation Plan for ARES

## Validation Philosophy

ARES is validated across four orthogonal dimensions: **engineering**, **research**, **user**, and **scientific**. Each dimension answers a distinct question:

| Dimension | Question | Stakeholder |
|---|---|---|
| Engineering | Does the system work correctly and efficiently? | Developers, DevOps |
| Research | Do the methods produce statistically sound results? | Researchers, ML scientists |
| User | Does the system meet user needs and build trust? | End users, product managers |
| Scientific | Is the work publishable, reproducible, and compliant? | Peer reviewers, conference committees |

A system may pass engineering validation (code runs, tests pass) but fail research validation (effects are not statistically significant) or user validation (explanations are not trusted). All four dimensions must be satisfied for the system to be considered production-ready.

---

## 1. Engineering Validation

Engineering validation ensures that ARES is correct, reliable, performant, and maintainable. It is the foundation upon which all other validation rests.

### 1.1 Unit Tests

**Scope**: Every module in `src/duplicate_question_app/` has corresponding unit tests.

| Module | Test Location | Coverage Target | Key Tests |
|---|---|---|---|
| `_linguistics/contradiction.py` | `tests/test_contradiction.py` | ≥ 90% | Opposite verb detection, NLI integration, penalty computation |
| `_linguistics/entity.py` | `tests/test_entity.py` | ≥ 90% | Programming language extraction, version parsing, mismatch scoring |
| `_linguistics/negation.py` | `tests/test_negation.py` | ≥ 90% | Negation word detection, contraction expansion, scope classification |
| `_linguistics/intent.py` | `tests/test_intent.py` | ≥ 90% | Question type classification, intent mismatch scoring |
| `_linguistics/lexical.py` | `tests/test_lexical.py` | ≥ 90% | Overlap computation, n-gram similarity |
| `_calibration/v1.py`, `v2.py` | `tests/test_calibration.py` | ≥ 85% | ECE accuracy on synthetic distributions, temperature scaling correctness |
| `_ensemble/agreement.py` | `tests/test_agreement.py` | ≥ 85% | Vote collection, majority calculation, unanimous/split detection |
| `_ensemble/v1.py`, `v2.py` | `tests/test_ensemble.py` | ≥ 85% | Weight normalisation, feature computation, penalty aggregation |
| `_evaluation/metrics.py` | `tests/test_metrics.py` | ≥ 85% | Confusion matrix extraction, ROC-AUC against known values |
| `_inference/cache.py` | `tests/test_cache.py` | ≥ 90% | LRU eviction order, thread safety, hit/miss accounting |
| `_inference/optimizer.py` | `tests/test_optimizer.py` | ≥ 80% | Batch encoding equivalence, cache warm-up, performance monitoring |
| `_models/registry.py` | `tests/test_registry.py` | ≥ 80% | Registry construction, model path resolution, status detection |
| `_preprocessing/text.py` | `tests/test_preprocessing.py` | ≥ 95% | Abbreviation expansion, normalisation correctness |

**Tools**: pytest, pytest-cov, hypothesis (property-based testing for edge cases).

**Pass criterion**: ≥ 80% line coverage per module; 100% coverage for critical paths (calibration computation, ensemble scoring, penalty aggregation).

### 1.2 Integration Tests

**Scope**: End-to-end pipelines that exercise multiple modules together.

| Test | Scenario | Pass Criterion |
|---|---|---|
| Full ensemble prediction | Two complete questions → final label, probability, trace | Prediction matches expected label |
| All 11 models respond | `collect_all_votes()` returns votes from every available model | No errors; ≥ 9 models respond |
| Penalty pipeline | Question pair with known contradiction → penalty > 0.3 | Entity/negation/contradiction engines fire correctly |
| Calibration end-to-end | Probabilities → temperature scaling → calibrated probs | ECE decreases (or remains same for well-calibrated input) |
| Agreement report | Known unanimous pair → agreement_score = 1.0 | Unanimous flag is true |
| Error categorisation | Known FP → error analysis labels it correctly | FP category matches expected type |

**Tools**: pytest (via test fixtures that load real or mock models).

### 1.3 Performance Benchmarks

**Scope**: Latency, throughput, and resource usage are benchmarked against defined thresholds.

| Benchmark | Threshold | Measurement |
|---|---|---|
| Ensemble p50 latency | < 2,000 ms | `_inference/optimizer.py:benchmark_inference()` |
| Ensemble p95 latency | < 5,000 ms | Batch of 100 predictions after warm-up |
| Single-model p50 latency | < 500 ms | Fastest model (TF-IDF) through slowest (DeBERTa) |
| Cache hit rate (steady state) | ≥ 60% | `CacheManager.stats()` after 1K predictions |
| Memory usage (peak) | < 4 GB | `psutil` during 1K prediction batch |
| Model load time (any) | < 30 s | `ModelLoader.get_load_time()` |

**Tools**: pytest-benchmark, custom benchmark scripts in `tools/`.

### 1.4 Regression Tests

**Scope**: Every change to the ensemble logic, penalty engines, or calibration pipeline must be regression-tested.

- A regression test suite captures the predictions of the current system on a frozen set of 1,000 canonical test pairs.
- Any code change that alters predictions on >5% of these pairs triggers a mandatory review.
- Key outputs tracked: final probability, ensemble weights, penalty values, agreement score.

**Tools**: Custom regression harness in `tests/test_regression.py` with JSON output diffing.

### 1.5 CI/CD Validation

**Pipeline** (`.github/workflows/`):

```
┌─────────────┐
│   Commit    │
└──────┬──────┘
       ↓
┌─────────────┐
│  Lint &     │  ruff, pyright
│  Type Check │
└──────┬──────┘
       ↓
┌─────────────┐
│  Unit Tests │  pytest (no GPU, no HF downloads)
│  (Fast)     │
└──────┬──────┘
       ↓
┌─────────────┐
│ Integration │  pytest (with HF model caching)
│  Tests      │
└──────┬──────┘
       ↓
┌─────────────┐
│ Performance │  pytest-benchmark (comparison with baseline)
│  Benchmarks │
└──────┬──────┘
       ↓
┌─────────────┐
│  Regression │  Diff against frozen canonical predictions
│  Tests      │
└──────┬──────┘
       ↓
    [Merge]
```

**Pass criteria**: All stages must pass. Performance regressions >10% compared to the baseline commit trigger a warning. Regression deviations >5% require sign-off.

---

## 2. Research Validation

Research validation verifies that the scientific claims made about ARES are statistically sound, reproducible, and correctly attributed to the proposed innovations rather than confounding factors.

### 2.1 Hypothesis Testing

Every experiment in the Evaluation Plan is subject to formal hypothesis testing.

**Procedure**:

1. **Pre-register**: Before running the experiment, specify the hypothesis, dependent variable, independent variable, statistical test, and effect size threshold in a research log (`docs/research/prereg/`).
2. **Run**: Execute the experiment using the standardised benchmark protocol.
3. **Test**: Apply the specified statistical test with α = 0.05 (Bonferroni-corrected for multiple comparisons).
4. **Report**: Accept or reject the hypothesis. Report effect size, confidence interval, and p-value.

**Tooling**: Statistical tests use `scipy.stats`. Results are logged to structured JSON files in `_artifacts/`.

### 2.2 Statistical Significance

**Minimum standards**:

- **Classification metrics** (F1, precision, recall): 95% bootstrap confidence intervals must be reported. Overlapping intervals between treatment and control are considered non-significant.
- **Calibration metrics** (ECE, MCE): paired Wilcoxon signed-rank test across 10 bootstrap samples.
- **Latency metrics**: independent t-test (or Mann-Whitney U for non-normal distributions) on log-transformed latency values.
- **Correlation metrics** (agreement-accuracy, attribution faithfulness): Spearman ρ with 95% bootstrap CI.

### 2.3 Ablation Studies

All ablation studies follow the **leave-one-out** protocol:

1. Start with the full system (all components enabled).
2. Disable exactly one component at a time.
3. Measure Δ in the dependent variable.
4. The component with the largest |Δ| is the most impactful.

**Caveats**:
- Ablation effects may be non-additive (interactions exist). Two-factor ablations (remove A, remove B, remove A+B) are used when interactions are suspected.
- The order of ablation is counterbalanced when the metric is sensitive to the removal sequence.

### 2.4 Comparative Evaluation

**Baseline selection criteria**:

1. **Individual models**: each of the 10 base models serves as a natural baseline.
2. **Simple ensembles**: uniform average, majority vote, median.
3. **Published results**: we compare against the best reported QQP F1 scores from literature (e.g., BERT-base fine-tuned on QQP: F1 ≈ 0.89).

**Fair comparison**:
- All models are evaluated on the identical test split.
- No model receives any evaluation-specific tuning (e.g., threshold optimisation on the test set).
- Latency comparisons are conducted on identical hardware after identical cache warm-up.

### 2.5 Reproducibility Verification

Before results are considered valid, an independent reproduction is conducted:

1. A second researcher (or automated script) checks out the git commit tagged for the experiment.
2. Runs the experiment using the provided seed and environment.
3. Confirms that all metrics match the original report within floating-point precision (≤ ±0.001).

**Artifacts required for reproducibility**:
- Git commit hash (`git rev-parse HEAD`).
- `pip freeze` output or conda environment export.
- Seed value.
- Evaluation script command line.
- Hardware specification (CPU model, RAM).

---

## 3. User Validation

User validation ensures that ARES meets the needs of its end users — developers and content moderators who make decisions based on its predictions.

### 3.1 Usability Testing with Streamlit App

**Application**: The ARES Streamlit interface at `app/` provides the primary user interaction point.

**Test protocol**:

1. **Task-based testing** (N = 10–15 participants per round):
   - Participants are given 20 question pairs and asked to determine duplicate status.
   - They use the ARES interface to view predictions, confidence, decision traces, and model agreement.
   - After each prediction, they rate: "How confident are you in the system's prediction?" (Likert 1–5).
2. **Metrics collected**:
   - Task completion time (seconds per pair).
   - Agreement with system (fraction of cases where the user accepts the system's prediction).
   - Trust score (mean Likert rating across all predictions).
   - Explanation usefulness (users rate: "The explanation helped me understand why the system made this prediction").
3. **Minimum pass criteria**:
   - Task completion time < 30 s per pair (average).
   - User-system agreement > 75%.
   - Mean trust score ≥ 3.5/5.

### 3.2 Expert Review of Explainability Traces

**Participants**: 3–5 NLP researchers or experienced engineers.

**Protocol**:

1. Experts review 30 decision traces sampled from:
   - 10 unanimous predictions (all models agree).
   - 10 split predictions (models disagree).
   - 10 false predictions (error cases).
2. For each trace, experts answer:
   - "Does the trace correctly identify why the prediction was made?" (Yes/No/Partial).
   - "Is there any important factor missing from the trace?" (Free text).
   - "If you were debugging this error, would the trace be helpful?" (Likert 1–5).
3. **Minimum pass criteria**:
   - Trace correctness ≥ 80% (fraction of traces rated "Yes").
   - Debugging usefulness mean ≥ 3.5/5.

### 3.3 Confidence in Predictions

**Research question**: Does the system's stated confidence correlate with user trust?

**Protocol**:

1. Show users 40 predictions varying systematically in:
   - Confidence level (high: >90%, medium: 70–90%, low: <70%).
   - Agreement level (high: >80%, low: <50%).
   - Prediction correctness (correct vs. incorrect, revealed after rating).
2. For each prediction, users rate their trust (Likert 1–5) before seeing the answer.
3. **Analysis**: Linear mixed-effects model: trust ~ confidence + agreement + (1|participant).
4. **Minimum pass criterion**: Significant positive coefficient for confidence (β > 0, p < 0.05).

### 3.4 Trust Calibration

**Definition**: Trust calibration is the alignment between the user's trust and the system's actual reliability. A well-calibrated user trusts the system when it is correct and doubts it when it is wrong.

**Measurement**:

- **Trust calibration index**: correlation between user trust (Likert) and system correctness (binary).
- **Over-trust**: fraction of cases where user trust ≥ 4 but system is wrong.
- **Under-trust**: fraction of cases where user trust ≤ 2 but system is correct.

**Minimum pass criteria**:
- Trust calibration index > 0.3 (moderate positive correlation).
- Over-trust rate < 20%.
- Under-trust rate < 30%.

---

## 4. Scientific Validation

Scientific validation prepares ARES for publication, peer review, and community adoption.

### 4.1 Peer Review Readiness

**Checklist** for each research claim:

- [ ] Claim is stated as a falsifiable hypothesis.
- [ ] Experimental design is described (IV, DV, controlled variables).
- [ ] Statistical test and α threshold are pre-specified.
- [ ] Effect size and confidence interval are reported.
- [ ] Negative results are included (not only positive findings).
- [ ] Ablation studies quantify component contributions.
- [ ] Results are reproducible (see Section 2.5).

### 4.2 Publication Standards

ARES papers target the following standards:

| Venue | Typical Length | Format | Key Requirements |
|---|---|---|---|
| ACL / EMNLP / NAACL | 8 pages | PDF (ACL template) | Reproducibility checklist, ethical considerations |
| NeurIPS Datasets & Benchmarks | 4 pages | NeurIPS template | Dataset documentation, intended use |
| JMLR / TACL | 12+ pages | Journal format | Full proofs, extended related work |
| Workshop papers | 4 pages | Varies | Preliminary results, position papers |

**Publication artifacts**:
- Paper (PDF).
- Code repository (GitHub, MIT License).
- Model weights (HuggingFace Hub).
- Evaluation datasets (HuggingFace Datasets).
- Reproducibility capsule (Docker + Makefile + evaluation script).

### 4.3 Artifact Availability

All artifacts are released under open licenses:

| Artifact | Location | License |
|---|---|---|
| Source code | `github.com/<org>/duplicate-question-nlp` | MIT |
| Model weights | HuggingFace Hub (`duplicate-question-nlp-*`) | Apache 2.0 |
| Evaluation datasets | HuggingFace Datasets | CC-BY-SA 4.0 |
| Evaluation scripts | `tools/evaluate.sh` | MIT |
| Benchmark results | `docs/research/benchmarks/` | CC-BY 4.0 |
| Decision traces (sample) | `docs/research/traces/` | CC-BY 4.0 |

**Documentation requirements**:
- `README.md`: system overview, installation, quickstart.
- `CONTRIBUTING.md`: how to contribute code, report bugs, propose changes.
- `CHANGELOG.md`: version history with notable changes.
- `LICENSE`: MIT (code), CC-BY (documentation).
- Model cards for each model (in `models/` or HuggingFace Hub).
- Dataset cards for each evaluation dataset.

### 4.4 Open-Source Release

**Repository requirements**:
- [ ] `.gitignore` excludes all model weights > 10 MB (use Git LFS or external hosting).
- [ ] `pyproject.toml` with all dependencies pinned.
- [ ] `requirements.txt`, `requirements-dev.txt`, `requirements-test.txt`, `requirements-docs.txt`.
- [ ] `.github/workflows/ci.yml` with full test pipeline.
- [ ] `pre-commit` hooks for linting and formatting.
- [ ] Code of conduct (`CODE_OF_CONDUCT.md`).
- [ ] Issue templates (bug report, feature request, question).
- [ ] Pull request template.

### 4.5 Benchmark Compliance

ARES benchmarks comply with the following standards:

**Reporting guidelines**:

- **CLIP (CheckList for NLP evaluation)**: all experiments report results across the full CheckList matrix (capability tests, robustness tests, fairness tests).
- **Reproducibility Checklist (ACL/NeurIPS)**: all checklist items are addressed in the paper supplement.
- **Dome (Data Oasis for Model Evaluation)**: evaluation datasets are documented with provenance, preprocessing, splits, and intended use.

**Registered benchmarks**:

| Benchmark | Status | Notes |
|---|---|---|
| QQP (Quora Question Pairs) | Active | Primary evaluation dataset, 400K pairs |
| QQP Challenge subset | Active | 1,000 linguistically challenging pairs |
| QQP adversarial subsets | Planned | Typo, abbreviation, synonym variants |
| StackExchange duplicates | Planned | Cross-domain evaluation |
| MedQuAD | Planned | Medical domain transfer |
| Multi-lingual QQP | Future | Machine-translated variants |

---

## Validation Summary Matrix

| Validation Dimension | Method | Frequency | Pass Criterion | Responsible |
|---|---|---|---|---|
| **Engineering** | Unit tests | Per commit | ≥ 80% coverage | Developer |
| Engineering | Integration tests | Per commit | All pass | Developer |
| Engineering | Performance benchmarks | Per PR | Within 10% of baseline | Developer |
| Engineering | Regression tests | Per PR | ≤ 5% prediction change | Reviewer |
| Engineering | CI/CD | Per commit | All stages green | CI system |
| **Research** | Hypothesis testing | Per experiment | p < α, pre-registered | Researcher |
| Research | Statistical significance | Per experiment | Non-overlapping CIs | Researcher |
| Research | Ablation studies | Per major change | Component contribution quantified | Researcher |
| Research | Reproducibility | Pre-publication | Independent reproduction matches | Second researcher |
| **User** | Usability testing | Per major release | Task time < 30 s, trust > 3.5/5 | UX researcher |
| User | Expert review | Per milestone | Trace correctness > 80% | Domain expert |
| User | Trust calibration | Per release | Calibration index > 0.3 | UX researcher |
| **Scientific** | Peer review readiness | Pre-submission | All checklist items complete | Lead author |
| Scientific | Artifact availability | Pre-publication | All artifacts released | Research team |
| Scientific | Benchmark compliance | Pre-submission | CLIP, reproducibility checklist | Lead author |

---

## Validation Cadence

```
Daily (CI):
  - Unit tests
  - Integration tests
  - Lint + type check

Weekly (Developer):
  - Performance benchmarks (compare with last week)
  - Regression tests

Per Milestone (Research team):
  - Pre-register experiments
  - Run evaluation plan experiments
  - Statistical significance analysis
  - Ablation studies

Per Major Release (Cross-functional):
  - Usability testing (N ≥ 10)
  - Expert review (N ≥ 3)
  - Trust calibration study
  - Reproducibility verification
  - Full benchmark suite execution

Pre-Publication:
  - Peer review readiness checklist
  - Artifact packaging and release
  - Benchmark compliance verification
```
