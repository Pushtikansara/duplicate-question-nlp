# Decision Support

## Overview

The DecisionSupport component translates a `SemanticAssessment` into a final
recommendation: DUPLICATE, NOT_DUPLICATE, or UNCERTAIN.

It considers:
- Overall semantic similarity
- Holistic confidence
- Conflict severity
- Component-level scores

## Recommendation Logic

```
effective_similarity = semantic_similarity × (1.0 - max_conflict_severity × 0.5)

if effective_similarity >= duplicate_threshold AND confidence >= 0.5:
    → DUPLICATE
elif effective_similarity < uncertain_threshold OR max_conflict_severity > 0.7:
    → NOT_DUPLICATE
else:
    → UNCERTAIN
```

## Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duplicate_threshold` | 0.7 | Minimum effective similarity for DUPLICATE |
| `uncertain_threshold` | 0.4 | Maximum effective similarity for NOT_DUPLICATE |

Thresholds are configurable via constructor injection.

## Reason Generation

Each recommendation includes a human-readable reason:

### DUPLICATE reasons
- "concept overlap 80%"
- "intent matches"
- "domain matches"
- "entity overlap 75%"

### NOT_DUPLICATE reasons
- "strong conflicts detected"
- "domain mismatch"
- "intent differs significantly"
- "low concept overlap"

### UNCERTAIN reasons
- "N conflict(s) present"
- "similarity 55% in ambiguous range"
- "insufficient evidence"

## Customization

```python
from duplicate_question_app._semantic_intelligence.decision_support import DefaultDecisionSupport

# Custom thresholds
decision = DefaultDecisionSupport(
    duplicate_threshold=0.6,
    uncertain_threshold=0.3,
)
```

## Conflict Reduction

Conflicts reduce the effective similarity, making the system more conservative
when contradictions are present. A conflict with severity 1.0 halves the
effective similarity.

## Usage

```python
from duplicate_question_app._semantic_intelligence import (
    SemanticIntelligenceEngine,
    SemanticAssessment,
)

engine = SemanticIntelligenceEngine()
assessment = engine.assess(rep_a, rep_b)

print(assessment.recommendation)      # Recommendation.DUPLICATE
print(assessment.recommendation_reason)  # "Likely duplicate: concept overlap 67%, intent matches"
```
