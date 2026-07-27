# Question Type Detection

*Version 1.0.0 — Phase 12.1*

---

## Purpose

Determines the semantic type of each question in a pair (e.g., definition, how-to, comparison, reason/why). Enriches `QueryAnalysis` with per-question and pair-level type metadata before any prediction occurs.

No ML models, no embeddings, no external APIs. Purely deterministic rule-based classification.

---

## Architecture

```
QueryPair
    │
    ▼
QuestionTypeDetector.detect()
    │
    ├── classify_question(q1) ──► type, confidence, reason
    ├── classify_question(q2) ──► type, confidence, reason
    └── _analyze_pair() ────────► pair_type, confidence, reason
                                    │
                                    ▼
                            QuestionTypeResult
```

### Components

| Module | Role |
|---|---|
| `question_type_detector.py` | Orchestrator: calls rules for each question, computes pair type |
| `type_rules.py` | Rule engine: deterministic single-question classification |
| `type_patterns.py` | Pattern library: regex patterns, keyword sets, complementary pair mappings |
| `type_models.py` | Data model: `QuestionTypeResult` dataclass |

---

## Supported Question Types (19)

| Type | Example |
|---|---|
| `definition` | "What is Python?" |
| `how_to` | "How to install pandas?" |
| `comparison` | "What is the difference between X and Y?" |
| `explanation` | "Explain how neural networks work" |
| `reason_why` | "Why is the sky blue?" |
| `opinion` | "What is your opinion on AI?" |
| `factoid` | "Who invented the telephone?" |
| `yes_no` | "Is Python interpreted?" |
| `numeric` | "How many planets exist?" |
| `temporal` | "When did WW2 end?" |
| `location` | "Where is the Eiffel Tower?" |
| `person` | "Who wrote Hamlet?" |
| `organization` | "What company makes the iPhone?" |
| `procedure` | "What are the steps to deploy a web app?" |
| `recommendation` | "What is the best laptop for programming?" |
| `troubleshooting` | "How to fix a segmentation fault?" |
| `code` | "def hello(): pass" |
| `list` | "List the features of Python" |
| `other` | "Hello world" (no matching pattern) |

---

## Pair Type Detection

After classifying each question, the detector analyzes the pair relationship:

| Pair Type | Condition |
|---|---|
| `same_type` | Both questions share the same type |
| `different_type` | Questions have different, non-complementary types |
| `complementary` | Types are semantically related (e.g., definition + how_to) |
| `potential_paraphrase` | Same type + high word overlap (>=80%) |
| `potential_reformulation` | Same type + moderate word overlap (>=40%) |
| `unknown` | One or both inputs empty |

Complementary pairs are defined in `COMPLEMENTARY_PAIRS` in `type_patterns.py`.

---

## Confidence Scoring

Each classification returns a confidence score (0.0–1.0):

- **0.00**: No patterns matched (empty / gibberish)
- **0.30–0.50**: Low confidence (generic match, weak signal)
- **0.60–0.80**: Moderate confidence (pattern match, some ambiguity)
- **0.85–1.00**: High confidence (strong pattern, clear signal)

The final `classification_confidence` in `QuestionTypeResult` is the mean of:
- q1 classification confidence
- q2 classification confidence
- pair analysis confidence

---

## Integration

The type detector is automatically called by `QueryAnalyzer.analyze()` and stored in `QueryAnalysis.question_type`:

```python
from ares.query_understanding import QueryPipeline

pipeline = QueryPipeline()
result = pipeline.run("How to learn Python?", "What is Python?")

print(result.question_type.question_1_type)  # "how_to"
print(result.question_type.question_2_type)  # "definition"
print(result.question_type.pair_type)         # "complementary"
print(result.question_type.classification_confidence)  # 0.83
```

---

## Constraints

- No ML models loaded
- No embeddings computed
- No external API calls
- No prediction engine modification
- No routing decisions made
- Pure string analysis only
