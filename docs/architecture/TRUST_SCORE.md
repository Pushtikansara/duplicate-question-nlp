# Trust Score -- ARES Phase 8 RTEE

## Composite Weighted Formula

The trust score is a weighted composite of eight component scores, normalised to a 0--100 scale.

### Formula

```
raw_sum = Sum(component_score_i * weight_i)
total_weight = Sum(weight_i for configured components)
TrustScore = (raw_sum / total_weight) * 100
```

Each `component_score_i` is a float in [0.0, 1.0].

### Weight Table

| Component | Weight | Symbol | Source Module |
|---|---|---|---|
| Routing Quality | 0.10 | W_r | `RoutingAuditor.score` |
| Reasoning Quality | 0.20 | W_re | `ReasoningAuditor.score` |
| Debate Agreement | 0.15 | W_d | `DebateAuditor.score` |
| Evidence Completeness | 0.15 | W_ev | `EvidenceAnalyzer.completeness` |
| Confidence Calibration | 0.15 | W_c | `ConfidenceAuditor.score` |
| Memory Quality | 0.10 | W_m | `MemoryAuditor.score` |
| Explainability Completeness | 0.10 | W_e | Avg of module contributions |
| Benchmark Consistency | 0.05 | W_b | Reserved for future use |

All weights sum to **1.00**.

### Normalisation Rationale

When an auditor is disabled or a module is unavailable, its component is omitted from both the numerator and the denominator. This prevents missing data from artificially punishing the final score while ensuring that the reported score is always on the [0, 100] scale.

## Worked Example

Given the following assessments:

| Module | Score |
|---|---|
| Routing | 0.92 |
| Reasoning | 0.87 |
| Debate | 0.74 |
| Memory | 0.95 |
| Confidence | 0.81 |
| Explainability | 0.88 |
| Evidence | 0.79 |
| Benchmark | 1.00 (default) |

### Step 1: Weighted Sum

```
Routing       = 0.92 * 0.10 = 0.092
Reasoning     = 0.87 * 0.20 = 0.174
Debate        = 0.74 * 0.15 = 0.111
Memory        = 0.95 * 0.10 = 0.095
Confidence    = 0.81 * 0.15 = 0.122
Explainability = 0.88 * 0.10 = 0.088
Evidence      = 0.79 * 0.15 = 0.119
Benchmark     = 1.00 * 0.05 = 0.050
---------------------------------------
raw_sum       = 0.851
```

### Step 2: Normalise

```
total_weight = 1.00
TrustScore = 0.851 / 1.00 * 100 = 85.1
```

### Step 3: Classify

- **Trust Level:** HIGH (>= 80)
- **Risk Level:** LOW (>= 80)

## Level Thresholds

| Trust Level | Range | Risk Level |
|---|---|---|
| HIGH | [80, 100] | LOW |
| MEDIUM | [60, 80) | MEDIUM |
| LOW | [40, 60) | HIGH |
| CRITICAL | [0, 40) | CRITICAL |
