# Complexity Estimation in Adaptive Cognitive Routing

**Question Classification for Pipeline Selection**

- **Version:** 1.0.0
- **Module:** `ares.acr.estimation.ComplexityEstimator`

---

## Overview

The `ComplexityEstimator` is the first stage of the Adaptive Cognitive Routing system. It analyzes an incoming question and assigns it to one of four complexity tiers: SIMPLE, MEDIUM, COMPLEX, or UNCERTAIN. This classification drives every downstream routing decision.

The estimator uses a feature-based heuristic model that evaluates the question across multiple dimensions: length, entity density, question type, ambiguity markers, and syntactic structure.

---

## Purpose

1. **Tier assignment**: Map each question to a discrete complexity tier.
2. **Score normalization**: Produce a continuous score in [0.0, 1.0] for threshold-based classification.
3. **Feature transparency**: Expose feature breakdown for debugging and analysis.
4. **Configurability**: Allow threshold tuning without model retraining.
5. **Speed**: Complete classification in sub-millisecond time to minimize routing overhead.

---

## Classification Criteria

### Feature Extraction

The estimator extracts the following features from the question text:

| Feature | Symbol | Range | Description |
|---|---|---|---|
| Character length | L | [1, 4096] | Raw character count |
| Word count | W | [1, 1024] | Whitespace-tokenized word count |
| Entity count | E | [0, inf) | Number of named entities (detected via lightweight NER or regex patterns) |
| Question word type | Q | categorical | what, who, when, where, why, how, which, do/does/did, is/are/was/were, modal (can/could/would), other |
| Ambiguity markers | A | [0, inf) | Count of ambiguous phrases ("maybe", "possibly", "or", "some", "kind of") |
| Conjunction count | C | [0, inf) | Count of coordinating conjunctions (and, but, or, nor, yet, so) |
| Dependency depth | D | [1, inf) | Maximum parse tree depth (estimated via heuristic or dependency parser) |
| Question mark presence | M | {0, 1} | Whether question ends with '?' |
| Comparison markers | P | [0, inf) | Count of comparative words (better, worse, compare, versus, vs, than) |
| Imperative markers | I | [0, inf) | Count of imperative verb forms (list, show, tell, define, explain, describe) |

### Feature Calculation

```
L = len(question_text)
W = len(question_text.split())

E = count_entities(question_text)     # uses NER tagger or pattern matching
A = count_ambiguity_markers(text)     # regex-based matching
C = count_conjunctions(text)          # set lookup against conjunction list
D = estimate_dependency_depth(text)   # approximate via clause count
M = 1 if question_text.strip().endswith('?') else 0
P = count_comparison_markers(text)    # set lookup
I = count_imperatives(text)           # lemma + verb form check
```

---

## Scoring Formula

### Raw Score

The raw complexity score is a weighted linear combination of normalized features:

```
raw_score = w_L * f(L) + w_W * f(W) + w_E * f(E) + w_Q * f(Q_type)
          + w_A * f(A) + w_C * f(C) + w_D * f(D) + w_P * f(P)
          - w_M * f(M) - w_I * f(I)
```

Where each `f(x)` is a feature normalization function that maps the raw feature to [0, 1].

### Normalization Functions

```
f(L) = min(L / L_max, 1.0)                    where L_max = 500
f(W) = min(W / W_max, 1.0)                    where W_max = 100
f(E) = min(E / E_max, 1.0)                    where E_max = 10
f(A) = min(A / A_max, 1.0)                    where A_max = 5
f(C) = min(C / C_max, 1.0)                    where C_max = 5
f(D) = min((D - 1) / D_max, 1.0)              where D_max = 6
f(P) = min(P / P_max, 1.0)                    where P_max = 3
f(M) = 1.0 if M == 1 else 0.0
f(I) = min(I / I_max, 1.0)                    where I_max = 3
```

### Question Type Mapping

`f(Q_type)` maps the question word to a complexity score:

| Question Word | f(Q_type) | Example |
|---|---|---|
| what / who / when / where | 0.1 | "What is the capital of France?" |
| which | 0.3 | "Which version is stable?" |
| do / does / did / is / are / was / were | 0.2 | "Does Python support multi-threading?" |
| how many / how much / how long | 0.4 | "How long does training take?" |
| how (general) | 0.5 | "How do I configure this setting?" |
| why | 0.7 | "Why does the model fail on rare tokens?" |
| can / could / would (modal) | 0.4 | "Can I use this with PyTorch?" |
| no question word / imperative | 0.3 | "Explain the attention mechanism." |

### Default Weights

```
w_L = 0.10    w_W = 0.15    w_E = 0.20    w_Q = 0.15
w_A = 0.15    w_C = 0.10    w_D = 0.10    w_P = 0.10
w_M = 0.05    w_I = 0.05
```

These weights are configurable via `RoutingConfig.complexity_estimator.weights`.

### Final Score and Tier Assignment

```
score = clamp(raw_score, 0.0, 1.0)

tier = UNCERTAIN  if score >= UNCERTAIN_THRESHOLD (0.75)
     = COMPLEX    if score >= COMPLEX_THRESHOLD   (0.50)
     = MEDIUM     if score >= MEDIUM_THRESHOLD    (0.25)
     = SIMPLE     otherwise
```

---

## Tier Definitions and Classification Criteria

### SIMPLE (score: 0.00, 0.25)

**Characteristics:**
- Short factual questions (< 10 words, < 60 characters)
- Single entity or no entity
- Direct question word (what, who, when, where)
- No ambiguity markers
- No conjunctions or comparisons
- Typically ends with '?'

**Examples:**
- "What is Python?"
- "Who created Linux?"
- "Define gradient descent."
- "Is TensorFlow open source?"

### MEDIUM (score: 0.25, 0.50)

**Characteristics:**
- Moderate length (10-25 words, 60-200 characters)
- 1-3 entities
- How-questions, configuration, installation
- Some conjunctions but no deep dependency chains
- Comparisons may be present

**Examples:**
- "How do I install PyTorch on Windows?"
- "Compare Python and JavaScript for web development."
- "What is the difference between L1 and L2 regularization?"
- "Configure NGINX with SSL certificate."

### COMPLEX (score: 0.50, 0.75)

**Characteristics:**
- Long questions (25-75 words, 200-500 characters)
- 3+ entities
- Multi-part reasoning questions
- Ambiguity markers present
- Multiple conjunctions and clauses
- Deep dependency chains
- Why-questions with reasoning requirements

**Examples:**
- "Analyze the comparative effectiveness of transformer-based vs CNN-based approaches for medical image segmentation given limited annotated data."
- "Why does batch normalization work better than layer normalization for CNNs but not for RNNs?"
- "Explain how gradient clipping, learning rate scheduling, and weight decay interact to prevent overfitting in large transformer models."

### UNCERTAIN (score: 0.75, 1.0]

**Characteristics:**
- Very long or rambling questions (75+ words)
- Unclear intent or mixed signals
- High ambiguity marker count
- Multiple question types in one utterance
- Incomplete or grammatically malformed input
- Contradictory requirements

**Examples:**
- "I'm not sure if I should use Python or maybe Java or something else for this project that involves machine learning and maybe web development?"
- "What is... actually I'm not sure how to ask this. Can you help me figure out what model to use?"
- "Probably something about transformers but I don't know the details."

---

## Score Bounds and Normalization

The raw score is clamped to [0.0, 1.0] to ensure consistent threshold comparison. Values below 0.0 are mapped to SIMPLE; values above 1.0 are mapped to UNCERTAIN.

```
final_score = max(0.0, min(1.0, raw_score))
```

The clamping ensures that:

- Extreme short questions (L=1, W=1, E=0) cannot produce negative scores below 0.0
- Extreme long questions (L=4096, W=1024) are capped at 1.0 UNCERTAIN rather than exceeding the range
- All scores are directly comparable across questions

---

## Configuration

```yaml
complexity_estimator:
  thresholds:
    uncertain: 0.75
    complex: 0.50
    medium: 0.25

  weights:
    length_char: 0.10
    word_count: 0.15
    entity_count: 0.20
    question_type: 0.15
    ambiguity_markers: 0.15
    conjunctions: 0.10
    dependency_depth: 0.10
    comparison_markers: 0.10
    question_mark: -0.05
    imperatives: -0.05

  normalization_caps:
    max_length: 500
    max_words: 100
    max_entities: 10
    max_ambiguity_markers: 5
    max_conjunctions: 5
    max_dependency_depth: 6
    max_comparison_markers: 3
    max_imperatives: 3

  question_type_scores:
    what: 0.1
    who: 0.1
    when: 0.1
    where: 0.1
    which: 0.3
    do: 0.2
    does: 0.2
    did: 0.2
    is: 0.2
    are: 0.2
    was: 0.2
    were: 0.2
    how_many: 0.4
    how_much: 0.4
    how_long: 0.4
    how: 0.5
    why: 0.7
    can: 0.4
    could: 0.4
    would: 0.4
    default: 0.3
```

---

## Limitations

1. **No semantic understanding**: The estimator operates on surface-level features only. A question may appear simple but require deep reasoning (e.g., "What is 2+2?" is simple; "What is the meaning of life?" appears simple but is unanswerable).
2. **English-centric**: Feature extraction logic assumes English grammar and question structure. Non-English questions may be misclassified.
3. **No domain adaptation**: A question that is SIMPLE for a domain expert may be COMPLEX for a general model. The estimator does not incorporate domain priors.
4. **Brittle NER**: Entity counting relies on a lightweight NER tagger that may miss or overcount entities, skewing the score.
5. **No negation handling**: Negation ("not", "no") is not penalized, so "Why does this not work?" is treated the same as "Why does this work?"
6. **No cross-lingual support**: Features like question type mapping are language-specific and do not generalize.

---

## Future Work

### Learned Complexity Model

Replace the heuristic feature-based model with a lightweight neural classifier (e.g., DistilBERT with a linear classification head fine-tuned on labeled routing data). The classifier would output complexity logits directly, providing:

- Higher accuracy on edge cases
- Implicit feature learning
- Cross-lingual generalization if trained on multilingual data

### Dynamic Thresholds

Replace static thresholds with percentile-based thresholds that adapt to the observed distribution of scores in production:

```
UNCERTAIN_THRESHOLD = percentile_90(score_distribution, window=1000)
```

### Multi-Language Question Type Mapper

Add language detection and language-specific question type tables (e.g., French "comment" -> 0.5, Mandarin "shenme" -> 0.1).

### Context-Aware Complexity

Incorporate conversation history into complexity scoring. A follow-up question like "How much?" should inherit context from the previous turn rather than being classified as SIMPLE.

### Uncertainty-Aware Score

Add a confidence interval around the score based on feature variance. If features produce conflicting signals (e.g., very short but high ambiguity), widen the confidence band and promote the tier to UNCERTAIN.

---

## References

- `ares.acr.estimation.ComplexityEstimator` source code
- Feature Extraction Utility Module (`ares.acr.features`)
- Question Type Taxonomy Document
- Threshold Tuning Experiment Report, Q4 2024
