# Trust Engine -- ARES Phase 8 RTEE

## Overview

`TrustEngine` computes a weighted composite trust score from eight component scores produced by the audit, explainability, evidence, and (implicitly) benchmark subsystems. It also translates the numeric score into a `TrustLevel` and `RiskLevel`.

## Trust Score Formula

```
TrustScore = (sum of weighted components) / total_weight * 100
```

### Components and Weights

| Component | Weight | Source |
|---|---|---|
| `routing_quality` | 0.10 (10%) | `RoutingAuditor.score` |
| `reasoning_quality` | 0.20 (20%) | `ReasoningAuditor.score` |
| `debate_agreement` | 0.15 (15%) | `DebateAuditor.score` |
| `evidence_completeness` | 0.15 (15%) | `EvidenceAnalyzer.completeness` |
| `confidence_calibration` | 0.15 (15%) | `ConfidenceAuditor.score` |
| `memory_quality` | 0.10 (10%) | `MemoryAuditor.score` |
| `explainability_completeness` | 0.10 (10%) | `ExplainabilityEngine` average contribution |
| `benchmark_consistency` | 0.05 (5%) | Reserved for benchmark-based calibration |

All weights sum to 1.0.

### Normalisation

Each component score (range 0.0 -- 1.0) is multiplied by its weight, summed, then divided by the total available weight to produce a score in the range [0, 100]. This ensures that disabled/missing modules do not penalise the final score -- the denominator only includes weights for configured components.

## Trust Levels

| Level | Score Range | Meaning |
|---|---|---|
| `HIGH` | >= 80.0 | Prediction can be accepted with full confidence |
| `MEDIUM` | >= 60.0 | Prediction is moderately trustworthy; review recommended |
| `LOW` | >= 40.0 | Prediction should be treated with caution |
| `CRITICAL` | < 40.0 | Prediction cannot be trusted without human review |

## Risk Levels

| Level | Score Range | Meaning |
|---|---|---|
| `LOW` | >= 80.0 | Minimal operational risk |
| `MEDIUM` | >= 60.0 | Moderate risk -- monitor outputs |
| `HIGH` | >= 40.0 | Elevated risk -- human oversight required |
| `CRITICAL` | < 40.0 | Critical risk -- do not act on prediction |

Risk level is the inverse of trust level: high trust implies low risk.

## Implementation

`TrustEngine` receives pre-computed `AuditorResult` objects from each auditor plus the raw `explainability_score` and `evidence_completeness` floats. It reads `config.trust_weights` for the weight dictionary. Weights can be reconfigured at the `ReflectionConfig` level without touching engine internals.

### Example

```
routing_quality      = 0.85 * 0.10 = 0.085
reasoning_quality    = 0.90 * 0.20 = 0.180
debate_agreement     = 0.80 * 0.15 = 0.120
confidence_calibrat  = 0.95 * 0.15 = 0.143
memory_quality       = 0.75 * 0.10 = 0.075
explainability       = 0.85 * 0.10 = 0.085
evidence_completeness = 0.80 * 0.15 = 0.120
benchmark            = 0.90 * 0.05 = 0.045
-------------------------------------------
Sum                  = 0.853
Total weight         = 1.00
TrustScore           = 0.853 / 1.00 * 100 = 85.3 -> HIGH
```
