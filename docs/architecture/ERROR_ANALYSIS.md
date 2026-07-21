# ARES Error Analysis

## ErrorAnalyzer Class

`ErrorAnalyzer` wraps the existing `error_analysis.py` module, providing a
convenient object-oriented interface for single-prediction and batch error
analysis.

```python
from duplicate_question_app._evaluation import ErrorAnalyzer

analyzer = ErrorAnalyzer()
```

## Error Categories

`categorize_error()` in `error_analysis.py` detects up to 8 error patterns:

| Category | Description | Detection Method | Confidence |
|---|---|---|---|
| Abbreviation | Questions use unmatched acronyms (e.g., NLP vs NLU) | Regex for 2-5 letter uppercase words | 0.7 |
| Synonym | Questions use semantically equivalent terms (learn/study, tutorial/guide) | 10 predefined synonym pairs | 0.8 |
| Negation | One question contains negation, the other does not | Negation word list (not, no, don't, ...) | 0.9 |
| Question Type Mismatch | Different interrogative types (what vs how vs why) | Regex for 11 question type patterns | 0.6 |
| Entity Mismatch | Different named entities (Python vs Java) | Capitalized word detection | 0.7 |
| Paraphrase / Word Order | High word overlap with different structure | Jaccard similarity > 0.5 | 0.75 |
| Borderline | Probability near 0.5 threshold | abs(prob - 0.5) < 0.15 | dynamic |
| Model Disagreement | Models produce divergent probabilities | std across models > 0.3 | min(1.0, std) |

If no specific error pattern is detected, a `No Error Detected` category is
returned.

## Batch Error Analysis

```python
import pandas as pd

df = pd.DataFrame({
    "q1": ["What is Python?", "How to code?"],
    "q2": ["What is Java?", "How to program?"],
    "predicted_label": [1, 0],
    "prob_duplicate": [0.95, 0.10],
    "true_label": [0, 1],
})

results = analyzer.analyze_batch(df)
# Returns DataFrame with columns: q1, q2, predicted_label, true_label,
#   prob_duplicate, is_error, hardness, error_categories, metadata
```

## Hardness Classification

`classify_hardness()` assigns each prediction to one of 5 categories:

| Category | Condition | Meaning |
|---|---|---|
| easy | confidence > 0.95 and agreement >= 0.6 | Model is certain and correct |
| medium | confidence <= 0.95, not error/borderline/hard | Moderate confidence correct prediction |
| hard | model_agreement < 0.6 | Models disagree substantially |
| borderline | abs(prob - 0.5) < 0.15 | Near decision threshold |
| error | predicted_label != true_label | Prediction is incorrect |

```python
hardness = analyzer.classify_hardness(
    prob_duplicate=0.95,
    confidence=0.95,
    model_agreement=1.0,
    predicted_label=1,
    true_label=1,
)
# Returns "easy"
```

## Finding Errors by Category

```python
by_category = analyzer.find_errors_by_category(df)
# Returns {"Synonym": [0, 5, 12], "Entity Mismatch": [3, 7], ...}
```

## Hard Negative Mining

`mine_hard_examples()` in `error_analysis.py` returns four DataFrames:

- `false_positives`: predicted duplicate, actually non-duplicate
- `false_negatives`: predicted non-duplicate, actually duplicate
- `borderline`: predictions near 0.5 threshold
- `low_agreement`: models disagree

```python
from duplicate_question_app._evaluation import mine_hard_examples

hard = mine_hard_examples(predictions_list, min_count=10)
hard["false_positives"].to_csv("false_positives.csv")
```
