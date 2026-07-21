# Recommendation Engine -- ARES Phase 8 RTEE

## Overview

`RecommendationEngine` evaluates trust, confidence, auditor assessments, consistency warnings, and evidence completeness to produce a list of actionable `RecommendationType` values for each prediction. The output guides downstream automated or human workflows.

## Recommendation Types

```python
class RecommendationType(Enum):
    ACCEPT                      = "accept"
    LOW_CONFIDENCE_WARNING      = "low_confidence_warning"
    HUMAN_REVIEW                = "human_review"
    RE_RUN_FULL                 = "re_run_full"
    RE_RUN_DIFFERENT_ROUTING    = "re_run_different_routing"
    MEMORY_REFRESH_SUGGESTED    = "memory_refresh_suggested"
```

## Generation Logic

`generate()` evaluates conditions in the order below and appends matching recommendations.

| # | Condition | Recommendation |
|---|---|---|
| 1 | `trust_score >= 80.0 AND confidence >= 0.8` | `ACCEPT` |
| 2 | `confidence < low_confidence_threshold (0.6)` | `LOW_CONFIDENCE_WARNING` |
| 3 | `trust_score < human_review_threshold (40.0)` | `HUMAN_REVIEW` |
| 4 | `reasoning_assessment.score < 0.4` | `RE_RUN_FULL` |
| 5 | `routing_assessment.score < 0.4` | `RE_RUN_DIFFERENT_ROUTING` |
| 6 | `memory_assessment.score < 0.3` | `MEMORY_REFRESH_SUGGESTED` |
| 7 | `len(consistency_warnings) >= max_warnings_before_review (3)` | `HUMAN_REVIEW` (if not already added) |
| 8 | `evidence_completeness < evidence_completeness_threshold (0.3)` | `LOW_CONFIDENCE_WARNING` (if not already added) |

### Fallback: Default Accept

If no condition matches, `ACCEPT` is appended as a safe default.

```python
if not recommendations:
    recommendations.append(RecommendationType.ACCEPT)
```

## Configuration-Driven Thresholds

| Parameter | Default | Used In |
|---|---|---|
| `low_confidence_threshold` | 0.6 | Condition 2 |
| `human_review_threshold` | 40.0 | Condition 3 |
| `max_warnings_before_review` | 3 | Condition 7 |
| `evidence_completeness_threshold` | 0.3 | Condition 8 |

All are set in `ReflectionConfig` and passed to `RecommendationEngine` on construction.

## Output

Returns a `list[RecommendationType]`. Multiple recommendations per prediction are common. Examples:

- **High-quality prediction:** `[ACCEPT]`
- **Moderate quality:** `[LOW_CONFIDENCE_WARNING]`
- **Low quality:** `[HUMAN_REVIEW, RE_RUN_FULL]`
- **Memory-degraded:** `[LOW_CONFIDENCE_WARNING, MEMORY_REFRESH_SUGGESTED]`

## Integration

Called from `ReflectionEngine.reflect()` after trust computation. Recommendations are stored in `ReflectionResult.recommendations` and serialised as string values in `to_dict()`.

Downstream consumers:
- `HumanReviewDecider` checks for `HUMAN_REVIEW` in recommendations.
- `ReflectionReportGenerator` displays recommendations per prediction.
- The application layer can branch on `ACCEPT` vs `HUMAN_REVIEW` for automated vs manual workflows.
