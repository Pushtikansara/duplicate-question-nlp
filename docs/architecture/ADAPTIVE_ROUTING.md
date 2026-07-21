# Adaptive Cognitive Routing (ACR) Architecture

**Phase 5 of the ARES System**

- **Version:** 1.0.0
- **Status:** Specification
- **Component:** AdaptiveCognitiveRouting

---

## Overview

The Adaptive Cognitive Routing (ACR) system is Phase 5 of the ARES architecture, positioned between Perception (Phase 4) and the cognitive processing modules (Phases 6-9). ACR is a stateless routing layer that determines which reasoning pipeline to execute for a given natural language question. It does not perform any reasoning itself; its sole responsibility is to select and dispatch to the correct cognitive pipeline.

---

## Purpose

ACR addresses the following requirements:

1. **Computational efficiency**: Avoid executing expensive reasoning pipelines on trivial questions.
2. **Accuracy-appropriate routing**: Route complex questions to high-fidelity pipelines.
3. **Latency management**: Meet user-facing latency constraints by selecting faster pipelines when appropriate.
4. **Resource allocation**: Balance computational cost across requests under load.
5. **Graceful degradation**: Fall back to simpler pipelines when advanced modules are unavailable or confidence is low.

---

## System Architecture

```
  +-----------+
  |  Input    |  (Question text, metadata, session context)
  +-----+-----+
        |
        v
+-------------------+
|  Complexity       |  Phase 5a: Classifies question as
|  Estimator        |  SIMPLE / MEDIUM / COMPLEX / UNCERTAIN
+--------+----------+
         |
         v
+-------------------+
|  Uncertainty      |  Phase 5b: Checks confidence of upstream
|  Router           |  cross-encoder, semantic, and reasoning modules
+--------+----------+
         |
         v
+-------------------+
|  Pipeline         |  Phase 5c: Maps (complexity, uncertainty)
|  Selector         |  to a concrete pipeline ID
+--------+----------+
         |
         v
+-------------------+
|  Cost + Latency   |  Phase 5d: Estimates execution cost
|  Estimation       |  and latency for the selected pipeline
+--------+----------+
         |
         v
+-------------------+
|  RoutingResult    |  Final output: pipeline ID, estimates,
|                   |  routing metadata, confidence score
+-------------------+
```

---

## Component Architecture

| Component | Responsibility | Phase |
|---|---|---|
| ComplexityEstimator | Classify question into one of four complexity tiers | 5a |
| UncertaintyRouter | Assess confidence gaps in encoder/semantic/reasoning modules | 5b |
| PipelineSelector | Select pipeline based on complexity-uncertainty matrix | 5c |
| CostEstimator | Compute relative computational cost of selected pipeline | 5d |
| LatencyEstimator | Estimate expected wall-clock time for pipeline execution | 5d |
| AdaptiveRoutingEngine | Orchestrate all components and produce RoutingResult | Orchestrator |
| RoutingConfig | Hold configurable thresholds, strategies, and rules | Configuration |
| RoutingStrategy | Encode selection policy (FASTEST, HIGHEST_ACCURACY, etc.) | Policy |
| RoutingRules | Custom rule engine for override-based pipeline selection | Extension |

---

## Decision Flow

### Tier Decision Logic

```
Input Question
    |
    v
[ComplexityEstimator.predict()]
    |
    +-> score >= UNCERTAIN_THRESHOLD  -----> UNCERTAIN
    +-> score >= COMPLEX_THRESHOLD    -----> COMPLEX
    +-> score >= MEDIUM_THRESHOLD     -----> MEDIUM
    +-> otherwise                     -----> SIMPLE
    |
    v
[UncertaintyRouter.evaluate()]
    |
    +-> cross-encoder confidence < CE_THRESHOLD  --> mark uncertain
    +-> semantic confidence < SEM_THRESHOLD      --> mark uncertain
    +-> reasoning confidence < REASON_THRESHOLD  --> mark uncertain
    |
    v
[PipelineSelector.select()]
    |
    Combine complexity + uncertainty flag
    Apply RoutingStrategy (FASTEST / HIGHEST_ACCURACY / BALANCED / RESEARCH)
    Apply RoutingRules if present
    |
    v
[Pipeline ID + Metadata]
```

### Mapping Complexity to Pipeline Tier

| Complexity | Uncertainty | Default Pipeline | Strategy Influence |
|---|---|---|---|
| SIMPLE | False | SIMPLE_PIPELINE | FASTEST may downgrade; others unchanged |
| SIMPLE | True | SIMPLE_PIPELINE | All strategies unchanged (uncertainty ignored for simple) |
| MEDIUM | False | MEDIUM_PIPELINE | FASTEST may downgrade to SIMPLE |
| MEDIUM | True | UNCERTAIN_PIPELINE | Full pipeline; RESEARCH may add diagnostic probes |
| COMPLEX | False | COMPLEX_PIPELINE | FASTEST may downgrade to MEDIUM |
| COMPLEX | True | UNCERTAIN_PIPELINE | Full pipeline; RESEARCH runs all |
| UNCERTAIN | False | UNCERTAIN_PIPELINE | All strategies run full pipeline |
| UNCERTAIN | True | UNCERTAIN_PIPELINE | All strategies run full pipeline |

---

## Routing Strategy Comparison

| Strategy | Goal | Pipeline Selection Behavior | Cost Preference | Latency Sensitivity |
|---|---|---|---|---|
| FASTEST | Minimize latency | Always selects lowest-latency pipeline within accuracy constraints | Low | Maximum |
| HIGHEST_ACCURACY | Maximize answer quality | Always selects highest-accuracy pipeline regardless of cost | Ignored | Ignored |
| BALANCED | Optimize accuracy per unit cost | Selects pipeline maximizing accuracy/cost ratio | Medium | Moderate |
| RESEARCH | Diagnostic / exploration | Runs full pipeline with instrumentation and telemetry | Ignored | Ignored |

---

## Pipeline Definitions

| Pipeline ID | Components | Relative Cost | Expected Latency | Use Case |
|---|---|---|---|---|
| SIMPLE_PIPELINE | CrossEncoder | 1.0 | 50-150 ms | Greetings, short facts, definitions |
| MEDIUM_PIPELINE | SemanticIntelligence -> Reasoning | 3.0 | 200-500 ms | Configuration, installation, comparisons |
| COMPLEX_PIPELINE | SemanticIntelligence -> Reasoning -> MADE | 7.0 | 500-2000 ms | Multi-entity, long reasoning, ambiguity |
| UNCERTAIN_PIPELINE | CrossEncoder -> SemanticIntelligence -> Reasoning -> MADE | 10.0 | 1000-4000 ms | Unclear intent, low confidence, fallback |

---

## Configuration Management

### Threshold Configuration

```yaml
complexity_estimator:
  simple_threshold: 0.25
  medium_threshold: 0.50
  complex_threshold: 0.75

uncertainty_router:
  cross_encoder_confidence_threshold: 0.70
  semantic_confidence_threshold: 0.65
  reasoning_confidence_threshold: 0.60

latency_estimator:
  base_latency_ms:
    SIMPLE_PIPELINE: 100
    MEDIUM_PIPELINE: 350
    COMPLEX_PIPELINE: 1200
    UNCERTAIN_PIPELINE: 2500
  text_length_factor: 0.05
  complexity_penalty_factor: 0.15

routing:
  default_strategy: BALANCED
  max_latency_ms: 3000
  enable_rules: true
  fallback_pipeline: SIMPLE_PIPELINE
```

### Environment Override

ACR supports hierarchical configuration loading:

1. Defaults compiled into binary
2. Configuration file (`routing_config.yaml`)
3. Environment variables (`ACR_*`)
4. Per-request overrides passed via RoutingContext

---

## Error Handling and Fallbacks

### Failure Modes

| Failure | Detection | Fallback Behavior |
|---|---|---|
| ComplexityEstimator failure | Component returns error or timeout | Default to UNCERTAIN tier |
| UncertaintyRouter failure | Component returns error or timeout | Assume maximum uncertainty |
| PipelineSelector failure | Selected pipeline invalid | Use SIMPLE_PIPELINE |
| CostEstimator failure | Returns negative or NaN | Use default cost for pipeline |
| LatencyEstimator failure | Returns negative or NaN | Use maximum allowed latency |
| All estimators fail | No pipeline selected | Return error with fallback pipeline |

### Circuit Breaker Integration

Each estimator component implements a circuit breaker with configurable thresholds:

- **Failure count threshold**: 5 consecutive failures
- **Reset timeout**: 30 seconds
- **Half-open probe interval**: 5 seconds

When a circuit is open, ACR skips that component and uses its default output.

---

## Limitations

1. **Static thresholds**: Current thresholds are static and may not generalize across domains without retuning.
2. **No online adaptation**: The routing policy does not adapt based on observed latency or accuracy in production.
3. **Cold start**: No complexity history exists for new question types; initial classifications may be inaccurate.
4. **No multi-turn context**: ACR treats each question independently; it does not incorporate conversation history.
5. **No model confidence calibration**: Uncertainty values from downstream modules may be miscalibrated, leading to suboptimal routing.
6. **Single-threaded orchestration**: AdaptiveRoutingEngine currently evaluates stages sequentially; parallel evaluation is not supported.

---

## Future Work

### ML-Based Routing

Replace heuristic complexity scoring with a lightweight classifier (e.g., DistilBERT head) trained on labeled routing decisions. The classifier would output complexity logits directly, reducing hand-tuned thresholds.

### Online Adaptation

Implement a feedback loop that monitors actual pipeline execution latency and accuracy, then adjusts thresholds via Bayesian optimization or bandit algorithms.

### A/B Testing Infrastructure

Expose per-request routing strategy assignment via experiment framework. Each request receives a strategy variant, and downstream metrics (latency, accuracy, cost) are collected for offline analysis.

### Multi-Turn Routing

Incorporate conversation state into complexity estimation. Follow-up questions that depend on previous context should not be re-classified from scratch; instead, ACR should propagate the previous turn's complexity and adjust incrementally.

### Parallel Stage Evaluation

Allow ComplexityEstimator and UncertaintyRouter to execute concurrently, reducing orchestration overhead.

---

## References

- ARES System Architecture Document, Phase 1-4
- MADE: Multi-Agent Discourse Engine Specification
- Semantic Intelligence Module Design Document
- Cross-Encoder Pairwise Scoring API
