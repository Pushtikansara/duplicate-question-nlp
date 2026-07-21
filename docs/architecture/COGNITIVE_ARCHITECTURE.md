# Cognitive Architecture — ARES (Adaptive Reasoning Engine for Semantic Understanding)

**Version:** 1.0
**Status:** Architecture Specification

---

## Abstract

ARES implements a neurologically inspired cognitive architecture organized into ten specialized processing layers: Perception, Understanding, Reasoning, Agent Collaboration, Memory, Reflection, Trust, Decision, Learning, and Analytics. Each layer corresponds to a distinct cognitive function observed in human semantic processing, from low-level text normalization through high-level metacognitive reflection. The architecture supports 11 heterogeneous NLP models operating within a multi-agent voting framework, with adaptive routing, confidence calibration, online learning, and full explainability tracing. This document specifies the complete architecture, inter-layer protocols, and the cognitive cycle that governs system operation.

---

## 1. System Architecture Overview

```
                              ARES COGNITIVE ARCHITECTURE
  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                                                                                     │
  │  INPUT ──▶ PERCEPTION ──▶ UNDERSTANDING ──▶ REASONING ──▶ DECISION ──▶ OUTPUT       │
  │               │                 │                 │              │                   │
  │               ▼                 ▼                 ▼              ▼                   │
  │          Normalization    Linguistic Analysis  Multi-Model    Ensemble Fusion        │
  │          Feature Extract  Intent Detection     Inference      Penalty Apply         │
  │          Embedding Gen.   Entity Recognit.     Adaptive       Threshold Opt.        │
  │                                               Routing                              │
  │               │                 │                 │              │                   │
  │               └─────────────────┴─────────────────┴──────────────┘                   │
  │                                        │                                             │
  │                                        ▼                                             │
  │                        ┌───────────────────────────────┐                            │
  │                        │     COLLABORATION LAYER       │                            │
  │                        │  Model Voting  Debate  Judge  │                            │
  │                        └──────────┬────────────────────┘                            │
  │                                   │                                                  │
  │               ┌───────────────────┼───────────────────┐                             │
  │               ▼                   ▼                   ▼                             │
  │        ┌────────────┐     ┌────────────┐     ┌────────────┐                        │
  │        │ REFLECTION │     │   MEMORY   │     │   TRUST    │                        │
  │        │ Calibration │     │  Semantic  │     │  Scoring   │                        │
  │        │ Contradict. │     │  Failure   │     │ Agreement  │                        │
  │        │ Error Detect│     │  Exper.Rep │     │ Confidence │                        │
  │        └────────────┘     └─────┬──────┘     └────────────┘                        │
  │                                 │                                                    │
  │                                 ▼                                                    │
  │                        ┌────────────┐                                               │
  │                        │  LEARNING  │                                               │
  │                        │ Adaptation │                                               │
  │                        │ Weight Upd │                                               │
  │                        │ Model Sel. │                                               │
  │                        └────────────┘                                               │
  │                                                                                     │
  │                        ┌────────────┐                                               │
  │                        │ ANALYTICS │                                               │
  │                        │ Traces     │                                               │
  │                        │ Perf. Mon. │                                               │
  │                        │ Drift Det. │                                               │
  │                        └────────────┘                                               │
  └─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer Specification

### 2.1 Perception Layer

**Purpose:** Transform raw text into a normalized, feature-rich representation suitable for downstream processing.

**Implementation:** `src/duplicate_question_app/_preprocessing/text.py`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                          PERCEPTION LAYER                                │
  │                                                                          │
  │  Raw Input (q1, q2)                                                      │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                   NORMALIZATION PIPELINE                          │    │
  │  │                                                                   │    │
  │  │  1. Whitespace Strip     ──▶  "  Hello World!  "                  │    │
  │  │  2. Unicode NFKC Normal. ──▶  Quotes, dashes → ASCII              │    │
  │  │  3. HTML Stripping       ──▶  <p>Hello</p> → Hello                │    │
  │  │  4. URL/Email Removal    ──▶  [url] / [email] placeholders        │    │
  │  │  5. Emoji Removal        ──▶  Unicode pictographs → space        │    │
  │  │  6. Special Char Norm.   ──▶  "!!!" → "!", "..." → "..."         │    │
  │  │  7. Abbreviation Expand  ──▶  "AI" → "AI (Artificial Intelligence)"│   │
  │  │  8. Typo Correction      ──▶  "algorithim" → "algorithm"          │    │
  │  │  9. Whitespace Collapse  ──▶  Multiple spaces → single space     │    │
  │  │ 10. Lowercase            ──▶  "Hello" → "hello"                   │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                  FEATURE EXTRACTION                               │    │
  │  │                                                                   │    │
  │  │  Abbreviation   Typo      Length    Token     Char-ngram          │    │
  │  │  Vector         Vector    Diff      Overlap   Overlap             │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  Normalized Text + Feature Vector                                         │
  └──────────────────────────────────────────────────────────────────────────┘
```

**Key characteristics:**
- Abbreviation expansion appends full forms in parentheses (preserves original tokens for TF-IDF)
- 97 abbreviation mappings across AI, CS, math, general domains
- 700+ typo corrections targeting technical vocabulary
- LRU caching of normalized results (max 5000 entries)
- Cache keyed by raw text hash for O(1) repeated lookups

---

### 2.2 Understanding Layer

**Purpose:** Extract structured semantic information from normalized text using five specialized linguistic engines.

**Implementation:** `src/duplicate_question_app/_linguistics/`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                        UNDERSTANDING LAYER                               │
  │                                                                          │
  │  Normalized Text (nq1, nq2)                                              │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                  LINGUISTIC ENGINE FIVE-FOLD                      │    │
  │  │                                                                   │    │
  │  │  ┌───────────────┐                                                │    │
  │  │  │ NEGATION      │── not, never, without, remove, disable,        │    │
  │  │  │ DETECTOR      │── can't, won't, uninstall, stop, prevent      │    │
  │  │  └───────┬───────┘  Scope: LOCAL / CLAUSAL / QUESTION            │    │
  │  │          │                                                         │    │
  │  │  ┌───────▼───────┐                                                │    │
  │  │  │ CONTRADICTION │── Direct negation: install↔uninstall           │    │
  │  │  │ DETECTOR      │── Opposite verbs: enable↔disable              │    │
  │  │  └───────┬───────┘── Mutually exclusive: free↔paid               │    │
  │  │          │          -- Temporal: before↔after                     │    │
  │  │  ┌───────▼───────┐  -- NLI cross-encoder scoring                  │    │
  │  │  │ ENTITY        │── 13 entity types: languages, frameworks,      │    │
  │  │  │ DETECTOR      │── OS, companies, technologies, products,       │    │
  │  │  └───────┬───────┘── countries, cities, currencies, units,        │    │
  │  │          │          -- versions, dates, numbers                   │    │
  │  │  ┌───────▼───────┐                                                │    │
  │  │  │ INTENT        │── 10 intent categories: definition, comparison, │   │
  │  │  │ DETECTOR      │── installation, tutorial, troubleshooting,    │    │
  │  │  └───────┬───────┘── recommendation, opinion, debugging,          │    │
  │  │          │          -- translation, math                         │    │
  │  │  ┌───────▼───────┐                                                │    │
  │  │  │ LEXICAL       │── Noun/verb overlap via suffix analysis       │    │
  │  │  │ ANALYZER      │── Software/language/product mismatch          │    │
  │  │  └───────────────┘── Version/number mismatch detection           │    │
  │  │                                                                   │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  Structured Analysis: {negation, contradiction, entity, intent, lexical} │
  └──────────────────────────────────────────────────────────────────────────┘
```

**Key characteristics:**
- 5 engines running in parallel on each question pair
- Contradiction detection uses both pattern-based (100+ opposite verb/adjective pairs) and NLI-based (DeBERTa-v3 cross-encoder) methods
- Intent detection uses 80+ regex patterns across 10 categories with conflict matrices
- Entity detection uses 13 large knowledge bases (500+ programming languages, 400+ companies, 150+ cities, etc.)
- Lexical analysis covers nouns, verbs, entities, software, languages, products, versions, numbers
- Each engine produces a normalized penalty score (0.0–1.0) consumed by the Reasoning Layer

---

### 2.3 Reasoning Layer

**Purpose:** Execute multi-model inference with adaptive routing based on input features.

**Implementation:** `src/duplicate_question_app/_models/`, `src/duplicate_question_app/_inference/`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                          REASONING LAYER                                 │
  │                                                                          │
  │  Input Features (from Perception + Understanding)                        │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                   MODEL DISPATCH MATRIX                          │    │
  │  │                                                                   │    │
  │  │  ┌──────────────┬─────────────┬──────────┬──────────────────┐    │    │
  │  │  │ Model Group  │ Models      │ Runtime  │ Dispatch Cond.    │    │    │
  │  │  ├──────────────┼─────────────┼──────────┼──────────────────┤    │    │
  │  │  │ Classical ML │ LR, SVM     │ <10ms    │ Always (fast)    │    │    │
  │  │  │ Transformer  │ DistilBERT  │ ~500ms   │ Always           │    │    │
  │  │  │ Bi-Encoder   │ BGE, E5,    │ ~200ms   │ Always           │    │    │
  │  │  │              │ MPNet       │          │                  │    │    │
  │  │  │ Cross-Enc.   │ DeBERTa,    │ ~400ms   │ Always           │    │    │
  │  │  │              │ CE-Quora    │          │                  │    │    │
  │  │  │ Memory       │ Memory Agent│ <50ms    │ On retrieval hit │    │    │
  │  │  └──────────────┴─────────────┴──────────┴──────────────────┘    │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                   ADAPTIVE ROUTER                                  │    │
  │  │                                                                   │    │
  │  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐      │    │
  │  │  │ Feature→Wt   │────▶│ Model Group  │────▶│ Weighted     │      │    │
  │  │  │ Mapping      │     │ Selection    │     │ Combination  │      │    │
  │  │  └──────────────┘     └──────────────┘     └──────────────┘      │    │
  │  │                                                                   │    │
  │  │  Dynamic Weight Rules:                                            │    │
  │  │    lexical_overlap < 0.2  → embed_w × 0.5, cross_w × 1.3        │    │
  │  │    entity_penalty > 0.3   → embed_w × 0.5, tfidf_w × 1.2        │    │
  │  │    intent_penalty > 0.3   → embed_w × 0.4, tfidf_w × 1.3        │    │
  │  │    negation_penalty > 0.4 → embed_w × 0.3, tfidf_w × 1.2        │    │
  │  │    contradiction > 0.4    → cross_w × 2.0, embed_w × 0.3        │    │
  │  │    model_agreement < 0.5  → cross_w × 1.4                        │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  Collection of {model_name: (label, prob, confidence)}                     │
  └──────────────────────────────────────────────────────────────────────────┘
```

**Key characteristics:**
- 10 base models + 1 ensemble, all lazily loaded via singleton cache manager
- Adaptive routing uses 9 feature dimensions to compute dynamic weights (10 rules)
- Model registry provides unified metadata for all models
- LRU embedding cache (max 10000 entries) prevents redundant encoding
- Graceful degradation: any model failure produces error vote, not system failure

---

### 2.4 Agent Collaboration Layer

**Purpose:** Enable multi-agent decision-making through voting, agreement analysis, and structured debate.

**Implementation:** `src/duplicate_question_app/_ensemble/agreement.py`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                    AGENT COLLABORATION LAYER                             │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                    VOTE COLLECTION PROTOCOL                       │    │
  │  │                                                                   │    │
  │  │  1. Each model casts {label, prob, confidence, latency}          │    │
  │  │  2. Votes collected into ModelVote dataclass array               │    │
  │  │  3. Invalid/error votes tagged with null confidence              │    │
  │  │  4. Vote set passed to Agreement Engine                          │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                    AGREEMENT ANALYSIS                             │    │
  │  │                                                                   │    │
  │  │  Agreement Score = max(n_dup, n_non) / n_total  [0.0 – 1.0]      │    │
  │  │  Unanimous      = agreement_score == 1.0                         │    │
  │  │  Borderline     = |mean(prob) - 0.5| < 0.15                     │    │
  │  │  Entropy        = -Σ(p_i × log₂(p_i))  over vote distribution   │    │
  │  │  Variance       = var({prob_i})  across all models               │    │
  │  │  Conf Spread    = max(conf) - min(conf)                          │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                    DISAGREEMENT RESOLUTION                        │    │
  │  │                                                                   │    │
  │  │  if agreement < 0.6:                                              │    │
  │  │    1. Identify disagreeing models                                  │    │
  │  │    2. Cross-encoder weight boosted 1.4×                           │    │
  │  │    3. Fall back to trimmed-mean (drop 1 high, 1 low)             │    │
  │  │    4. Flag prediction as "low consensus"                          │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  AgreementReport: {votes, majority, agreement_score, is_borderline,       │
  │                    confidence_stats, models_agreeing, models_disagreeing} │
  └──────────────────────────────────────────────────────────────────────────┘
```

**Key characteristics:**
- 9 models vote simultaneously; ensemble aggregates via weighted average
- Agreement score dynamically adjusts ensemble strategy
- Borderline predictions trigger conservative weight dampening (all weights × 0.9)
- Trimmed mean used as robust ensemble statistic (drops outliers)
- Full vote trace available for explainability

---

### 2.5 Memory Layer

**Purpose:** Store and retrieve past experiences including prediction outcomes, failure cases, calibration data, and linguistic features.

**Implementation:** `src/duplicate_question_app/_logging/error_logger.py`, `src/duplicate_question_app/_inference/cache.py`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                           MEMORY LAYER                                   │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                    MEMORY TYPES                                   │    │
  │  │                                                                   │    │
  │  │  SEMANTIC MEMORY         EPISODIC MEMORY       PROCEDURAL MEMORY  │    │
  │  │  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────┐  │    │
  │  │  │ • Embedding cache│   │ • Error log CSV  │   │ • Calibration │  │    │
  │  │  │ • Model params   │   │ • Hard examples  │   │   params      │  │    │
  │  │  │ • Calibration    │   │ • Prediction     │   │ • Weights     │  │    │
  │  │  │   curves         │   │   traces         │   │ • Thresholds  │  │    │
  │  │  │ • Linguistic     │   │ • Session data   │   │ • Ensemble    │  │    │
  │  │  │   knowledge bases│   │ • Performance    │   │   rules       │  │    │
  │  │  │ • TF-IDF vectors │   │   snapshots      │   │              │  │    │
  │  │  └──────────────────┘   └──────────────────┘   └──────────────┘  │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                   MEMORY OPERATIONS                               │    │
  │  │                                                                   │    │
  │  │  STORE:    append to error buffer, flush to CSV every 100 recs    │    │
  │  │  RETRIEVE: embedding LRU cache hit, config reload, CSV query     │    │
  │  │  UPDATE:   calibration params recomputed, threshold adjusted      │    │
  │  │  FORGET:   log rotation at 100MB, LRU eviction at capacity       │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                  FAILURE MEMORY SCHEMA                            │    │
  │  │                                                                   │    │
  │  │  ErrorExample {                                                   │    │
  │  │    question1, question2,                                          │    │
  │  │    predicted_label, true_label, prob_duplicate, confidence,       │    │
  │  │    error_categories: [ENTITY_MISMATCH, INTENT_MISMATCH, ...],     │    │
  │  │    ensemble_weights, model_votes, model_probs,                   │    │
  │  │    agreement_score, lexical_overlap, semantic_depth,              │    │
  │  │    entity_overlap, intent_q1, intent_q2,                          │    │
  │  │    has_negation_q1, has_negation_q2, contradiction_score,        │    │
  │  │    lexical_penalty, timestamp, session_id                        │    │
  │  │  }                                                                │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  └──────────────────────────────────────────────────────────────────────────┘
```

**Key characteristics:**
- Error logged for every misprediction with full feature vector (25+ fields)
- Buffer-and-flush pattern for thread-safe async writes
- Error categories: ENTITY_MISMATCH, INTENT_MISMATCH, NEGATION_MISMATCH, CONTRADICTION, LEXICAL_MISMATCH, LOW_CONFIDENCE, MODEL_DISAGREEMENT, SYNONYM_CONFUSION, ABBREVIATION_CONFUSION, VERSION_MISMATCH, UNKNOWN
- Log auto-rotates at 100MB to prevent unbounded growth
- Loadable as DataFrame for aggregate error analysis

---

### 2.6 Reflection Layer

**Purpose:** Metacognitive evaluation of model outputs — detect overconfidence, contradictions, and systematic errors.

**Implementation:** `src/duplicate_question_app/_calibration/`, `src/duplicate_question_app/_linguistics/contradiction.py`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                          REFLECTION LAYER                                │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                CONFIDENCE CALIBRATION                             │    │
  │  │                                                                   │    │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
  │  │  │ Temperature  │  │   Platt      │  │   Isotonic   │           │    │
  │  │  │ Scaling      │  │   Scaling    │  │  Regression  │           │    │
  │  │  └──────────────┘  └──────────────┘  └──────────────┘           │    │
  │  │                                                                   │    │
  │  │  Metrics: ECE, MCE, Brier Score, NLL                             │    │
  │  │  Best method selected per model group by minimizing ECE          │    │
  │  │  Per-model parameters pre-computed:                              │    │
  │  │    SVM:   Platt scaling    (a=1.0, b=0.0)                       │    │
  │  │    W3/4:  Temperature=2.0  (conservative)                       │    │
  │  │    BGE:   Temperature=1.3                                        │    │
  │  │    E5:    Temperature=1.8  (high FP rate)                       │    │
  │  │    MPNet: Temperature=1.2                                        │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                CONTRADICTION & ERROR DETECTION                    │    │
  │  │                                                                   │    │
  │  │  • Pattern-based contradiction (opposite verbs/adjectives)       │    │
  │  │  • NLI-based contradiction (DeBERTa cross-encoder)               │    │
  │  │  • Negation mismatch detection (install↔uninstall)              │    │
  │  │  • Model disagreement detection (agreement < 0.6)               │    │
  │  │  • Calibration status: overconfident / underconfident / calib.  │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  Reflection signals fed back to Trust and Learning layers                 │
  └──────────────────────────────────────────────────────────────────────────┘
```

**Key characteristics:**
- Three calibration methods available, selected per-model based on validation ECE
- Temperature scaling parameterizes confidence distribution (T>1 → less confident)
- Reflection signals (contradiction, disagreement, calibration error) propagate to weight adaptation
- NLI-based contradiction detection provides soft signal (0.0–1.0) rather than hard threshold

---

### 2.7 Trust Layer

**Purpose:** Compute calibrated confidence scores that incorporate both model-level calibration and inter-model agreement.

**Implementation:** `src/duplicate_question_app/_calibration/`, `src/duplicate_question_app/_ensemble/agreement.py`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                            TRUST LAYER                                   │
  │                                                                          │
  │  Input: Raw probabilities from each model                                │
  │         Agreement metrics from Collaboration layer                       │
  │         Calibration parameters from Reflection layer                     │
  │      │                                                                   │
  │      ▼                                                                   │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │               CALIBRATION-AWARE CONFIDENCE                        │    │
  │  │                                                                   │    │
  │  │  For each model m:                                                │    │
  │  │    p_m_calibrated = calibrate(p_m_raw, params[m])                 │    │
  │  │    conf_m = max(p_m_calibrated, 1 - p_m_calibrated)              │    │
  │  │    trust_m = conf_m × α + agreement_score × (1-α)               │    │
  │  │                                                                   │    │
  │  │  where α = 0.7 (weight on self-calibration vs agreement)         │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │               AGREEMENT-WEIGHTED CONFIDENCE                       │    │
  │  │                                                                   │    │
  │  │  if unanimous:       confidence = max(conf_mean, 0.95)           │    │
  │  │  if agreement > 0.8: confidence = conf_mean                      │    │
  │  │  if agreement > 0.6: confidence = conf_mean × 0.9                │    │
  │  │  if agreement < 0.6: confidence = conf_mean × 0.7 - flagged     │    │
  │  │  if borderline:      confidence = confidence × 0.8               │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  Trust-calibrated confidence score for final decision                     │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

### 2.8 Decision Layer

**Purpose:** Fuse all signals into a final prediction with optimal thresholding.

**Implementation:** `src/duplicate_question_app/_ensemble/v1.py`, `src/duplicate_question_app/_ensemble/v2.py`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                           DECISION LAYER                                 │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                    ENSEMBLE FUSION                                │    │
  │  │                                                                   │    │
  │  │  Option A: Adaptive Weighted Mean (v1)                            │    │
  │  │    p_ensemble = Σ(w_i × p_i) / Σ(w_i)                           │    │
  │  │    w_i = group_weight / n_models_in_group                        │    │
  │  │                                                                   │    │
  │  │  Option B: Dynamic Confidence Routing (v2)                        │    │
  │  │    p_ensemble = Σ(w_group × μ_group)                            │    │
  │  │    w_group = f(linguistic_features)  [10 adaptive rules]         │    │
  │  │    then: p_ensemble ×= (1.0 - min(0.7, total_penalty))          │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                    PENALTY APPLICATION                            │    │
  │  │                                                                   │    │
  │  │  total_penalty = 0.5×entity + 0.5×intent + 0.6×negation         │    │
  │  │                 + 0.8×contradiction + 0.4×lexical                │    │
  │  │  p_final = p_ensemble × (1.0 - min(0.7, total_penalty))         │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                    THRESHOLD OPTIMIZATION                         │    │
  │  │                                                                   │    │
  │  │  label = 1 if p_final >= threshold else 0                        │    │
  │  │  default threshold = 0.5                                          │    │
  │  │  per-model thresholds from config (F1-maximized on val set):     │    │
  │  │    E5: 0.35,  BGE: 0.30,  MPNet: 0.36,  CE-Quora: 0.10         │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  Final Output: {label, probability, confidence, explanation}              │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

### 2.9 Learning Layer

**Purpose:** Online adaptation of model weights, calibration parameters, and selection based on performance feedback.

**Implementation:** `src/duplicate_question_app/_logging/error_logger.py`, `src/duplicate_question_app/_calibration/v2.py`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                           LEARNING LAYER                                 │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                    ONLINE ADAPTATION                              │    │
  │  │                                                                   │    │
  │  │  Per prediction:                                                  │    │
  │  │    1. Compare prediction with ground truth (if available)        │    │
  │  │    2. Log error with full feature vector                          │    │
  │  │    3. Update error category distribution                          │    │
  │  │                                                                   │    │
  │  │  Per evaluation cycle:                                            │    │
  │  │    1. Load error log as DataFrame                                 │    │
  │  │    2. Compute error category frequencies                          │    │
  │  │    3. Generate recommendations (rule adjustment suggestions)     │    │
  │  │    4. Re-run calibration search on new data                      │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                 WEIGHT UPDATE                                     │    │
  │  │                                                                   │    │
  │  │  Adaptive weight adjustment based on per-model historical perf:  │    │
  │  │    If a model consistently over-predicts on entity mismatch:     │    │
  │  │      → reduce embedding weight for entity-mismatch cases         │    │
  │  │    If a model consistently disagrees with ground truth:          │    │
  │  │      → reduce its global weight contribution                     │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │                 MODEL SELECTION                                   │    │
  │  │                                                                   │    │
  │  │  Leaderboard-driven:                                              │    │
  │  │    by_accuracy, by_confidence, by_calibration (ECE),             │    │
  │  │    by_agreement (with ensemble), by_influence, by_speed          │    │
  │  │                                                                   │    │
  │  │  Strongest model → highest accuracy                              │    │
  │  │  Weakest model  → lowest accuracy / most disagreement            │    │
  │  │  Most influential → highest accuracy × agreement composite       │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

### 2.10 Analytics Layer

**Purpose:** Provide full explainability traces, performance monitoring, and drift detection for every prediction.

**Implementation:** `src/duplicate_question_app/_explainability/`, `src/duplicate_question_app/_evaluation/`

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                          ANALYTICS LAYER                                 │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │               EXPLAINABILITY TRACE (per prediction)              │    │
  │  │                                                                   │    │
  │  │  DecisionTrace {                                                  │    │
  │  │    • Per-model scores: 9 model probabilities + TF-IDF similarity │    │
  │  │    • Lexical features: word/char overlap, count diffs           │    │
  │  │    • Semantic features: abbreviations, synonyms, named entities  │    │
  │  │    • Adaptive weights: per-group weight distribution             │    │
  │  │    • Agreement metrics: agreement%, entropy, variance            │    │
  │  │    • Final decision: prob, label, confidence, threshold          │    │
  │  │  }                                                                │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │              TEXT EXPLANATION (4 levels)                         │    │
  │  │                                                                   │    │
  │  │  Level 1 (Basic):      "Strong duplicate match"                  │    │
  │  │  Level 2 (Standard):   Paragraph with confidence + agreement     │    │
  │  │  Level 3 (Detailed):   Multi-paragraph breakdown by model       │    │
  │  │  Level 4 (Comprehens.): Full report + counterfactuals            │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  │      │                                                                    │
  │      ▼                                                                    │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │              PERFORMANCE MONITORING & DRIFT DETECTION            │    │
  │  │                                                                   │    │
  │  │  • Accuracy, Precision, Recall, F1, MCC (per model + ensemble)  │    │
  │  │  • ROC-AUC, PR-AUC                                               │    │
  │  │  • Calibration curves, ECE, MCE, Brier                          │    │
  │  │  • Confusion matrix, threshold sweep                             │    │
  │  │  • Error category distribution over time                         │    │
  │  │  • Hardness distribution: easy / medium / hard / borderline      │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The Cognitive Cycle

ARES operates on a continuous cognitive cycle adapted from the OODA loop (Observe–Orient–Decide–Act):

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                         ARES COGNITIVE CYCLE                            │
  │                                                                         │
  │                         ┌─────────────────────┐                         │
  │                    ┌────│  1. PERCEIVE         │────┐                    │
  │                    │    │  (normalize, extract)│    │                    │
  │                    │    └─────────────────────┘    │                    │
  │                    │                               │                    │
  │                    ▼                               ▼                    │
  │  ┌─────────────────────┐                   ┌─────────────────────┐      │
  │  │  2. UNDERSTAND       │                   │  6. REFLECT          │      │
  │  │  (linguistic analyze)│                   │  (calibrate, detect)│      │
  │  └──────────┬──────────┘                   └──────────┬──────────┘      │
  │             │                                         │                  │
  │             ▼                                         │                  │
  │  ┌─────────────────────┐                              │                  │
  │  │  3. REASON           │                              │                  │
  │  │  (model inference)   │                              │                  │
  │  └──────────┬──────────┘                              │                  │
  │             │                                          │                  │
  │             ▼                                          │                  │
  │  ┌─────────────────────┐                               │                  │
  │  │  4. COLLABORATE      │                               │                  │
  │  │  (vote, agree)       │                               │                  │
  │  └──────────┬──────────┘                               │                  │
  │             │                                           │                  │
  │             ▼                                           │                  │
  │  ┌─────────────────────┐                               │                  │
  │  │  5. MEMORIZE         │───────────────────────────────┘                  │
  │  │  (store experience)  │                                                  │
  │  └──────────┬──────────┘                                                  │
  │             │                                                              │
  │             ▼                                                              │
  │  ┌─────────────────────┐                                                   │
  │  │  7. TRUST            │                                                   │
  │  │  (score confidence)  │                                                   │
  │  └──────────┬──────────┘                                                   │
  │             │                                                              │
  │             ▼                                                              │
  │  ┌─────────────────────┐                                                   │
  │  │  8. DECIDE           │                                                   │
  │  │  (fuse, threshold)   │                                                   │
  │  └──────────┬──────────┘                                                   │
  │             │                                                              │
  │             ▼                                                              │
  │  ┌─────────────────────┐                                                   │
  │  │  9. ANALYZE          │─────────────────────────────────────────────────►│
  │  │  (trace, report)     │    OUTPUT                                       │
  │  └──────────┬──────────┘                                                   │
  │             │                                                              │
  │             ▼                                                              │
  │  ┌─────────────────────┐                                                   │
  │  │ 10. LEARN            │                                                   │
  │  │  (adapt, improve)    │───► back to step 1 with updated parameters      │
  │  └─────────────────────┘                                                   │
  └─────────────────────────────────────────────────────────────────────────┘
```

The cognitive cycle executes in approximately 2–5 seconds for a complete ensemble prediction on CPU, with each stage pipelined for maximum throughput.

---

## 4. Inter-Layer Communication Protocol

| From Layer | To Layer | Data Passed | Mechanism |
|---|---|---|---|
| Perception | Understanding | Normalized text + feature vector | Direct function call |
| Understanding | Reasoning | Linguistic penalties (5 values) | Dataclass |
| Reasoning | Collaboration | 9 ModelVote structs | Array of dataclasses |
| Collaboration | Decision | AgreementReport | Dataclass |
| Collaboration | Reflection | Agreement metrics | Shared dataclass |
| Reflection | Trust | Calibration params + contradiction scores | Config lookup + computed |
| Trust | Decision | Trust-calibrated confidences | Scalar per model |
| Decision | Analytics | Final decision + all intermediate data | DecisionTrace |
| Analytics | Memory | Error examples (if misprediction) | Async buffer → CSV |
| Memory | Learning | Historical error distribution | DataFrame query |
| Learning | Reasoning | Updated weights/rules | Config reload |

---

## 5. Cognitive Science Foundations

ARES's architectural design draws on established cognitive science theories:

| Cognitive Theory | ARES Implementation |
|---|---|
| **Dual-Process Theory** (Kahneman, 2011) | Fast lexical models (System 1) + slow transformer models (System 2) |
| **Predictive Coding** (Friston, 2010) | Confidence calibration updates based on prediction-error mismatch |
| **Metacognition** (Flavell, 1979) | Reflection layer monitors and evaluates own uncertainty |
| **Memory Consolidation** (McClelland, 1995) | Error examples buffer → episodic CSV → pattern extraction |
| **Bayesian Brain** (Knill & Pouget, 2004) | Temperature scaling as confidence prior; Platt scaling as likelihood |
| **Multi-Agent Systems** (Minsky, 1986) | 9 model agents with distinct knowledge, voting protocol, judge agent |
| **Adaptive Resonance Theory** (Grossberg, 1976) | Dynamic weight adjustment when predictions conflict with linguistic features |

---

## 6. Architectural Constraints

1. **No hard inter-layer dependencies** — Each layer communicates through well-defined dataclass interfaces
2. **Lazy evaluation** — Models loaded on first request; config reloaded at startup only
3. **Graceful degradation** — Any individual model failure produces error-tagged vote, not system crash
4. **Config-driven weight specification** — All adaptive weights, thresholds, and calibration params in YAML
5. **Deterministic traces** — Same input always produces identical decision trace (no randomness in inference)
