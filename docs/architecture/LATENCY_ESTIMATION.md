# Latency Estimation in Adaptive Cognitive Routing

**Expected Execution Time Modeling for Pipeline Selection**

- **Version:** 1.0.0
- **Module:** `ares.acr.estimation.LatencyEstimator`

---

## Overview

The `LatencyEstimator` provides predictive latency estimates for each pipeline tier given a question's characteristics. These estimates are used by the routing strategy to enforce latency constraints and by the cost-benefit analysis in BALANCED mode.

Latency estimation is crucial because it enables the router to reject a pipeline that would exceed user-facing latency requirements, even if that pipeline would produce the highest accuracy.

---

## Purpose

1. **Latency-aware routing**: Enable the `RoutingStrategy` to reject pipelines exceeding `max_latency_ms`.
2. **Resource budgeting**: Provide expected duration for capacity planning and request scheduling.
3. **SLA enforcement**: Ensure that routing decisions respect percentile latency bounds.
4. **Tradeoff quantification**: Allow the BALANCED strategy to compute accuracy-per-latency ratios.
5. **Diagnostic feedback**: Expose breakdown of expected latency by sub-module for profiling.

---

## Architectural Context

```
  PipelineSelector
       |
       | pipeline_id, question_text
       v
  LatencyEstimator
       |
       |-- Fetch base latency for pipeline
       |-- Apply text length adjustment
       |-- Apply complexity penalty
       |-- Compute percentile estimates (p50, p95, p99)
       |-- Clamp to [min, max]
       v
  LatencyEstimate
       |-- expected_latency_ms
       |-- p50_latency_ms
       |-- p95_latency_ms
       |-- p99_latency_ms
       |-- breakdown: { module -> ms }
       |-- processing_time_ms
```

---

## Estimation Model

### Base Latency

Each pipeline has a configured base latency representing the expected execution time under reference conditions (100-character question, SIMPLE complexity).

```yaml
latency_estimator:
  base_latency_ms:
    SIMPLE_PIPELINE:    100
    MEDIUM_PIPELINE:    350
    COMPLEX_PIPELINE:   1200
    UNCERTAIN_PIPELINE: 2500
```

### Formula

The expected latency is computed as:

```
expected_latency_ms = base_latency[pipeline_id]
    * text_length_factor(question)
    * complexity_penalty(complexity_tier)
```

Where:

```
text_length_factor(L) = 1.0 + coefficient * log2(L / L_ref)

    L       = character length of question
    L_ref   = 100 (reference length)
    coefficient = configurable (default 0.05)

complexity_penalty(tier) = 1.0 + tier_penalty[tier]

    tier_penalty = {
        SIMPLE:    0.00,
        MEDIUM:    0.10,
        COMPLEX:   0.25,
        UNCERTAIN: 0.40
    }
```

### Percentile Estimates

P50, P95, and P99 are derived from the expected latency using historical variance factors:

```
p50_latency_ms = expected_latency_ms * 0.95
p95_latency_ms = expected_latency_ms * 1.50
p99_latency_ms = expected_latency_ms * 2.00
```

These multipliers are configurable and should be tuned from production monitoring data.

### Worked Examples

#### Example 1: Simple Question, Short Length

```
Question: "What is Python?"
Length: 16 characters
Complexity: SIMPLE
Pipeline: SIMPLE_PIPELINE

text_length_factor = 1.0 + 0.05 * log2(16 / 100)
                   = 1.0 + 0.05 * log2(0.16)
                   = 1.0 + 0.05 * (-2.64)
                   = 1.0 - 0.132
                   = 0.868

complexity_penalty = 1.0 + 0.00 = 1.0

expected_ms = 100 * 0.868 * 1.0 = 86.8 ms

p50 = 86.8 * 0.95 = 82.5 ms
p95 = 86.8 * 1.50 = 130.2 ms
p99 = 86.8 * 2.00 = 173.6 ms
```

#### Example 2: Complex Question, Long Length

```
Question: "Compare the performance characteristics of BERT, RoBERTa,
           and DeBERTa for named entity recognition when fine-tuned
           on biomedical text corpora with limited annotation budgets."
Length: 194 characters
Complexity: COMPLEX
Pipeline: COMPLEX_PIPELINE

text_length_factor = 1.0 + 0.05 * log2(194 / 100)
                   = 1.0 + 0.05 * log2(1.94)
                   = 1.0 + 0.05 * 0.956
                   = 1.0 + 0.0478
                   = 1.048

complexity_penalty = 1.0 + 0.25 = 1.25

expected_ms = 1200 * 1.048 * 1.25 = 1572.0 ms

p50 = 1572.0 * 0.95 = 1493.4 ms
p95 = 1572.0 * 1.50 = 2358.0 ms
p99 = 1572.0 * 2.00 = 3144.0 ms
```

---

## Latency in Strategy Selection

The latency estimate feeds into strategy execution in three ways:

### 1. Constraint Checking (All Strategies)

Before returning a pipeline selection, the engine checks:

```
if latency_estimate.expected_latency_ms > config.max_latency_ms:
    if strategy == FASTEST:
        # Already using fastest; respect constraint but warn
        append_warning("estimated latency exceeds max_latency_ms")
    elif strategy in {BALANCED, HIGHEST_ACCURACY}:
        # Attempt downgrade to next-cheapest pipeline
        downgrade_pipeline()
    elif strategy == RESEARCH:
        # RESEARCH ignores latency
        pass
```

### 2. Strategy Scoring (BALANCED Only)

```
score(pipeline) = baseline_accuracy[pipeline] / expected_latency_ms[pipeline]
```

The BALANCED strategy selects the pipeline with the highest accuracy-per-millisecond score that also satisfies `max_latency_ms`.

### 3. Cost-Benefit Visualization (RESEARCH Only)

RESEARCH strategy includes the full latency breakdown in telemetry output for offline analysis of whether routing decisions align with actual observed latencies.

---

## Accuracy vs. Latency Tradeoff

The tradeoff is quantified by the accuracy density metric:

```
accuracy_density(pipeline) = baseline_accuracy[pipeline] / expected_latency_ms[pipeline]

expressed in accuracy points per second.
```

| Pipeline | Accuracy | Latency (100 char) | Latency (500 char) | Accuracy Density (100 char) |
|---|---|---|---|---|
| SIMPLE_PIPELINE | 0.65 | 86.8 ms | 97.6 ms | 7.49 pts/s |
| MEDIUM_PIPELINE | 0.82 | 385.0 ms | 433.1 ms | 2.13 pts/s |
| COMPLEX_PIPELINE | 0.91 | 1575.0 ms | 1771.9 ms | 0.58 pts/s |
| UNCERTAIN_PIPELINE | 0.93 | 3500.0 ms | 3937.5 ms | 0.27 pts/s |

The BALANCED strategy uses this density to select pipelines that maximize accuracy return per unit of latency investment.

---

## Configuration

```yaml
latency_estimator:
  base_latency_ms:
    SIMPLE_PIPELINE: 100
    MEDIUM_PIPELINE: 350
    COMPLEX_PIPELINE: 1200
    UNCERTAIN_PIPELINE: 2500

  text_length:
    reference_length: 100
    coefficient: 0.05
    max_factor: 2.0
    min_factor: 0.5

  complexity_penalty:
    SIMPLE: 0.00
    MEDIUM: 0.10
    COMPLEX: 0.25
    UNCERTAIN: 0.40

  percentile_factors:
    p50: 0.95
    p95: 1.50
    p99: 2.00

  clamp:
    min_latency_ms: 10
    max_latency_ms: 10000

routing:
  max_latency_ms: 3000
```

---

## Limitations

1. **No queueing delay**: The model does not account for request queueing, resource contention, or concurrent execution overhead.
2. **Static variance factors**: P50/P95/P99 multipliers are static and not informed by real-time system load.
3. **No module-level variance**: Each pipeline's latency is estimated as a single value; sub-module variance is not modeled.
4. **Linear scaling assumption**: The text length adjustment assumes log-linear scaling, which may not hold for very short or very long inputs.
5. **No network latency**: Distributed deployments with module-level network hops are not reflected.

---

## Future Work

### Dynamic Variance Modeling

Replace static percentile factors with a Kalman filter or exponential moving average that tracks observed latency distributions per pipeline in real time.

### Queue-Aware Estimation

Integrate with request queue depth to add a queueing delay term:

```
total_latency = execution_latency + queue_depth * average_execution_latency
```

### Module-Level Breakdown

Support per-module latency estimation (CrossEncoder, SemanticIntelligence, Reasoning, MADE) rather than pipeline-level aggregates, enabling finer-grained pipeline optimization.

### Learned Latency Model

Train a regression model (gradient-boosted tree or small neural network) on historical latency data, using features beyond text length (token count, entity count, POS distribution, etc.).

---

## References

- `ares.acr.estimation.LatencyEstimator` source code
- Latency Benchmark Suite, Q2 2025
- `ares.acr.config.RoutingConfig` latency section
- Accuracy vs. Latency Tradeoff Analysis Report
