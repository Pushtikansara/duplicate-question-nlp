# ARES Explainability Metrics

## Overview

The explainability module quantifies how transparent and interpretable each
ARES cognitive subsystem is. Four component scores are computed and combined
into a single weighted overall score.

## Component Scores

### Reasoning Completeness

Measures how thoroughly the reasoning module formed logical structures.

- Checks number of premises (capped at 5, normalized to [0,1])
- Checks number of hypotheses (capped at 3, normalized to [0,1])
- Checks amount of supporting evidence (capped at 5, normalized to [0,1])
- Returns average of available sub-scores
- Returns 0.0 if no reasoning result is available

```python
from duplicate_question_app._evaluation import compute_reasoning_completeness

score = compute_reasoning_completeness(reasoning_result)
```

### Evidence Completeness

Measures the depth of evidence collected during reasoning.

- Counts total evidence items (supporting + contradicting)
- Capped at 10, normalized to [0,1]
- Returns 0.0 if no reasoning result is available

```python
from duplicate_question_app._evaluation import compute_evidence_completeness

score = compute_evidence_completeness(reasoning_result)
```

### Debate Completeness

Measures how comprehensively the multi-agent debate explored perspectives.

- Checks number of agents used (capped at 8, normalized to [0,1])
- Checks if consensus was reached (1.0 if present)
- Checks number of votes cast (capped at 8, normalized to [0,1])
- Returns average of available sub-scores
- Returns 0.0 if no debate result is available

```python
from duplicate_question_app._evaluation import compute_debate_completeness

score = compute_debate_completeness(debate_result)
```

### Memory Usage Score

Measures how much episodic memory is populated.

- Retrieves `total_entries` from memory manager statistics
- Capped at 1000, normalized to [0,1]
- Returns 0.0 if no memory manager is available

```python
from duplicate_question_app._evaluation import compute_memory_usage

score = compute_memory_usage(memory_manager)
```

## Overall Explainability Score

```python
from duplicate_question_app._evaluation import compute_explainability_score

result = compute_explainability_score(
    reasoning_result=reasoning_result,
    debate_result=debate_result,
    memory_manager=memory_manager,
    weights={"reasoning": 0.3, "evidence": 0.3, "debate": 0.3, "memory": 0.1},
)
```

### Default Weights

| Component | Weight |
|---|---|
| Reasoning | 0.3 |
| Evidence | 0.3 |
| Debate | 0.3 |
| Memory | 0.1 |

### Return Value

```python
{
    "overall": 0.725,           # Weighted combination
    "reasoning_completeness": 0.8,
    "evidence_completeness": 0.7,
    "debate_completeness": 0.75,
    "memory_usage": 0.5,
    "weights_used": {"reasoning": 0.3, "evidence": 0.3, "debate": 0.3, "memory": 0.1},
}
```

All scores are rounded to 4 decimal places.

## Interpretation

- **0.0 - 0.3**: Low explainability; module outputs lack transparency
- **0.3 - 0.6**: Moderate explainability; some structure is visible
- **0.6 - 0.8**: Good explainability; most reasoning steps are traceable
- **0.8 - 1.0**: High explainability; fully transparent decision process

## Reports

`ReportGenerator.generate_explainability_report()` produces a markdown
document listing each component score and the overall metric.
