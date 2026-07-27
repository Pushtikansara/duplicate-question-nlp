# Reflection Validation — Phase 10.5.5

## Consistency Mapping

| Confidence Range | Trust Level | Risk Level | Human Review | Recommendations |
|---|---|---|---|---|
| 95-100% | HIGH | LOW | No | (none) |
| 70-95% | MEDIUM | MEDIUM | No | (none) |
| 50-70% | LOW | HIGH | Yes | review_manually |
| 30-50% | LOW | HIGH | Yes | review_manually, recheck_similarity |
| 0-30% | LOW | HIGH | Yes | review_manually, recheck_similarity, flag_for_expert_review |

## Dynamic Recommendation Generation

`_generate_recommendations(trust_score_100)` generates recommendations from thresholds:

```python
if trust_score_100 >= 95.0:  → []
if trust_score_100 < 70.0:   → ["review_manually"]
if trust_score_100 < 50.0:   → ["recheck_similarity"]
if trust_score_100 < 30.0:   → ["flag_for_expert_review"]
```

## Dual Reflection Fix

**Root Cause**: `ARES.predict()` ran reflection internally (via `_lazy_load`), and `DemoEngine.run_demo()` ran it again in Phase 5.

**Fix**: `engine = ARES().with_reflection(False)` — disabled internal reflection in the demo engine call. Reflection runs exactly once in Phase 5.

**Regression**: 28 tests verify all 5 confidence bands and edge cases.

## Consistency Enforcer

`_ensure_consistent_reflection()` overrides inconsistent trust/risk/review fields to match the confidence-based rules.
