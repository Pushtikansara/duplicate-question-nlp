# Consistency Checker -- ARES Phase 8 RTEE

## Overview

`ConsistencyChecker` evaluates three dimensions of internal consistency after inference, producing a list of `ConsistencyWarning` objects. Each warning carries a `warning_type`, `description`, `severity` (0.0 -- 1.0), and `details` dict.

## ConsistencyWarning

```python
@dataclass
class ConsistencyWarning:
    warning_type: str
    description: str
    severity: float      # 0.0 - 1.0
    details: dict
```

## Method: `check()`

```python
def check(
    self,
    reasoning_result: Any,
    debate_result: Any,
    prediction: dict[str, Any],
) -> list[ConsistencyWarning]
```

Returns an empty list when all checks pass.

---

## Check 1: Reasoning Consistency (Conflicting Evidence)

**Method:** `_check_reasoning_consistency()`

Evaluates whether contradicting evidence undermines supporting evidence within the reasoning module.

**Condition:** Both `supporting_evidence` and `contradicting_evidence` are non-empty, and the ratio `contradicting / max(supporting, 1)` exceeds 0.5.

**Warning produced:**
```python
ConsistencyWarning(
    warning_type="conflicting_evidence",
    description=f"Contradicting evidence ({n_contra}) is significant vs supporting ({n_support})",
    severity=min(ratio, 1.0),
    details={"supporting": n, "contradicting": n},
)
```

---

## Check 2: Debate Consistency (Vote Disagreement / High Conflict)

**Method:** `_check_debate_consistency()`

Two sub-checks:

### 2a. High Debate Conflict
**Condition:** `conflict_reports` length > 3.

**Warning:**
```python
ConsistencyWarning(
    warning_type="high_debate_conflict",
    description=f"Debate produced {n} conflicts",
    severity=min(n / 10.0, 1.0),
    details={"conflict_count": n},
)
```

### 2b. Vote Disagreement
**Condition:** Agents produce more than one distinct recommendation (e.g., some vote "duplicate", others "not_duplicate").

**Warning:**
```python
ConsistencyWarning(
    warning_type="vote_disagreement",
    description=f"Agents disagree on recommendation: {unique_recs}",
    severity=0.6,
    details={"recommendations": list(unique_recs)},
)
```

---

## Check 3: Cross-Module Consistency

**Method:** `_check_cross_module_consistency()`

Compares the final decision across three sources:
- `reasoning_result.decision`
- `debate_result.consensus.decision`
- `prediction.predicted_label` (mapped: 1 -> "duplicate", 0 -> "not_duplicate", else -> "unknown")

**Condition:** The set of distinct decisions across the three sources has more than one element.

**Warning:**
```python
ConsistencyWarning(
    warning_type="cross_module_inconsistency",
    description=f"Modules disagree: Reasoning={r}, Debate={d}, Final={f}",
    severity=0.7,
    details={"reasoning": r, "debate": d, "final": f},
)
```

---

## Integration

Called from `ReflectionEngine.reflect()` after all audits complete. Warnings feed into:
- **RecommendationEngine:** `len(consistency_warnings) >= max_warnings_before_review` triggers `HUMAN_REVIEW`.
- **HumanReviewDecider:** Same threshold check for flagging.
- **QualityEstimator:** Each warning applies a 0.05 penalty to the quality score.
- **ReflectionResult:** Warnings included in output and serialisation.
