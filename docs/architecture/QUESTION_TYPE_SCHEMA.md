# Question Type Schema

*Version 1.0.0 — Phase 12.1*

---

## `QuestionTypeResult`

The `QuestionTypeResult` dataclass stores per-question and pair-level type metadata.

### Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `question_1_type` | `str` | `"other"` | Semantic type of question 1 |
| `question_2_type` | `str` | `"other"` | Semantic type of question 2 |
| `pair_type` | `str` | `"unknown"` | Relationship between the two questions |
| `classification_confidence` | `float` | `0.0` | Mean confidence across both questions and pair analysis |
| `classification_reason` | `str` | `""` | Trace string showing which rules fired |

### Valid `question_[12]_type` Values

```
definition    how_to         comparison    explanation
reason_why    opinion        factoid       yes_no
numeric       temporal       location      person
organization  procedure      recommendation  troubleshooting
code          list           other
```

### Valid `pair_type` Values

```
same_type              different_type        complementary
potential_paraphrase   potential_reformulation  unknown
```

---

## `QueryAnalysis` Extension

Phase 12.1 adds the `question_type` field to `QueryAnalysis`:

### New Field

| Field | Type | Default | Description |
|---|---|---|---|
| `question_type` | `QuestionTypeResult` | `QuestionTypeResult()` | Full type classification result |

### Serialization

```python
result = analyzer.analyze(q1, q2)

# Dict includes question_type as nested dict
d = result.to_dict()
# d["question_type"] = {
#     "question_1_type": "how_to",
#     "question_2_type": "definition",
#     "pair_type": "complementary",
#     ...
# }

# JSON roundtrip preserves all type data
j = result.to_json()
restored = QueryAnalysis.from_dict(json.loads(j))
restored.question_type.question_1_type  # "how_to"
```

### Example JSON Output

```json
{
  "original_question_1": "How to learn Python?",
  "original_question_2": "What is Python?",
  "question_type": {
    "question_1_type": "how_to",
    "question_2_type": "definition",
    "pair_type": "complementary",
    "classification_confidence": 0.8333,
    "classification_reason": "q1:how_to:how_to_pattern:how to | q2:definition:first_word:what_short | pair:complementary:complementary:how_to+definition"
  },
  "version": "1.0.0"
}
```

---

## Using QuestionTypeResult Directly

```python
from ares.query_understanding import QuestionTypeDetector, QuestionTypeResult

detector = QuestionTypeDetector()

# Standalone classification (no QueryAnalysis wrapper)
result = detector.detect("How to code?", "What is coding?")

# Access individual fields
print(result.question_1_type)          # "how_to"
print(result.question_2_type)          # "definition"
print(result.pair_type)                # "complementary"

# Export
data = result.to_dict()

# Reconstruct
restored = QuestionTypeResult.from_dict(data)
```

---

## Integration Example

```python
from ares.query_understanding import QueryPipeline
import pandas as pd

pipeline = QueryPipeline()

pairs = [
    ("What is Python?", "What is Java?"),
    ("How to learn Python?", "Best way to learn Python?"),
    ("Why is the sky blue?", "What causes rainbows?"),
]

results = pipeline.run_batch(pairs)

for r in results:
    qt = r.question_type
    print(f"{qt.question_1_type:16} | {qt.question_2_type:16} | {qt.pair_type:22} | {qt.classification_confidence:.2f}")

# Output:
# definition        | definition        | potential_paraphrase    | 0.87
# how_to            | how_to            | potential_paraphrase    | 0.82
# reason_why        | reason_why        | same_type               | 0.70

# To DataFrame (flattened)
df = pipeline.to_dataframe(results)
print(df[["question_type_question_1_type", "question_type_pair_type"]].head())
```
