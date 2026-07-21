# Human Review Decision -- ARES Phase 8 RTEE

## Overview

`HumanReviewDecider` evaluates whether a prediction requires manual human oversight before downstream action. It applies a configurable threshold check plus several conditional triggers, returning a boolean flag and a concatenated reason string.

## Configuration

| Parameter | Default | Purpose |
|---|---|---|
| `human_review_threshold` | 40.0 | Trust score below this triggers review |
| `low_confidence_threshold` | 0.6 | Prediction confidence below this triggers review |
| `max_warnings_before_review` | 3 | Consistency warnings at or above this count trigger review |

All parameters are set in `ReflectionConfig` and passed to `HumanReviewDecider` via constructor injection.

## `should_review()` Method

```python
def should_review(
    self,
    trust_score: float,
    confidence: float,
    routing_assessment: Any,
    reasoning_assessment: Any,
    debate_assessment: Any,
    consistency_warnings: list[Any],
    recommendations: list[RecommendationType],
    explainability_score: float,
) -> tuple[bool, str]
```

Returns `(False, "")` when no conditions are met, or `(True, "reason1; reason2")` when one or more conditions trigger.

## Flagging Conditions

Checked in order; all matching reasons are accumulated.

| # | Condition | Trigger | Reason String |
|---|---|---|---|
| 1 | Trust score below threshold | `trust_score < human_review_threshold` | "Trust score below threshold ({s} < {t})" |
| 2 | Low prediction confidence | `confidence < low_confidence_threshold` | "Low prediction confidence ({c})" |
| 3 | High agent disagreement | `debate_assessment.score < 0.4` | "High agent disagreement (debate score: {s})" |
| 4 | Low reasoning quality | `reasoning_assessment.score < 0.4` | "Low reasoning quality ({s})" |
| 5 | Excessive consistency warnings | `len(consistency_warnings) >= max_warnings_before_review` | "Excessive consistency warnings ({n})" |
| 6 | Recommendation engine already flags | `HUMAN_REVIEW in recommendations` | "Recommendation engine flags human review" |

Note: Condition 6 is only added if no other reason already contains "Human review".

## Example Decision

Input:
- trust_score = 35.0, confidence = 0.55
- debate_score = 0.30, reasoning_score = 0.90
- consistency_warnings = 2, recommendations = [HUMAN_REVIEW]

Triggers: Conditions 1, 2, 3, 6

Output: `(True, "Trust score below threshold (35.0 < 40.0); Low prediction confidence (0.55); High agent disagreement (debate score: 0.30); Recommendation engine flags human review")`

## Integration

`HumanReviewDecider` is called at the end of `ReflectionEngine.reflect()`, after trust computation and recommendation generation. The result is stored in `ReflectionResult.human_review_required` and `ReflectionResult.human_review_reason`.
