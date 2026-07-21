# Pipeline Selection Logic

**Mapping Complexity and Uncertainty to Execution Pipelines**

- **Version:** 1.0.0
- **Module:** `ares.acr.selection.PipelineSelector`

---

## Overview

The `PipelineSelector` is the decision-making component of the Adaptive Cognitive Routing system. It receives a complexity tier and uncertainty assessment from upstream estimators, then maps the combined state to a concrete pipeline identifier. The mapping is influenced by the active `RoutingStrategy` and may be overridden by user-defined `RoutingRules`.

This document describes the mathematical and logical basis for pipeline selection, including the selection matrix, strategy influence, rule-based overrides, and worked examples.

---

## Purpose

Pipeline selection must satisfy the following requirements:

1. **Correctness**: Every (complexity, uncertainty) pair must map to a valid pipeline.
2. **Strategy awareness**: The same inputs may produce different outputs depending on the active strategy.
3. **Override capability**: Rules must allow custom logic without modifying core selection tables.
4. **Determinism**: Given identical inputs, strategy, and rules, the output must be identical.
5. **Graceful fallback**: Invalid or missing mappings must resolve to a safe default.

---

## Selection Matrix

The primary selection mechanism is a 4x2 matrix mapping (complexity, uncertainty) to a pipeline ID.

### Default Matrix (BALANCED Strategy)

| Complexity | Uncertainty = False | Uncertainty = True |
|---|---|---|
| SIMPLE | SIMPLE_PIPELINE | SIMPLE_PIPELINE |
| MEDIUM | MEDIUM_PIPELINE | UNCERTAIN_PIPELINE |
| COMPLEX | COMPLEX_PIPELINE | UNCERTAIN_PIPELINE |
| UNCERTAIN | UNCERTAIN_PIPELINE | UNCERTAIN_PIPELINE |

### FASTEST Strategy

Under FASTEST, the selector attempts to downgrade to the cheapest acceptable pipeline.

| Complexity | Uncertainty = False | Uncertainty = True |
|---|---|---|
| SIMPLE | SIMPLE_PIPELINE | SIMPLE_PIPELINE |
| MEDIUM | SIMPLE_PIPELINE | MEDIUM_PIPELINE |
| COMPLEX | MEDIUM_PIPELINE | COMPLEX_PIPELINE |
| UNCERTAIN | UNCERTAIN_PIPELINE | UNCERTAIN_PIPELINE |

Note: FASTEST will not downgrade below `SIMPLE_PIPELINE` and will not downgrade when uncertainty is true (to ensure sufficient signal).

### HIGHEST_ACCURACY Strategy

Under HIGHEST_ACCURACY, the selector upgrades to the most capable pipeline without regard for cost.

| Complexity | Uncertainty = False | Uncertainty = True |
|---|---|---|
| SIMPLE | MEDIUM_PIPELINE | MEDIUM_PIPELINE |
| MEDIUM | COMPLEX_PIPELINE | UNCERTAIN_PIPELINE |
| COMPLEX | UNCERTAIN_PIPELINE | UNCERTAIN_PIPELINE |
| UNCERTAIN | UNCERTAIN_PIPELINE | UNCERTAIN_PIPELINE |

### RESEARCH Strategy

Under RESEARCH, every request executes the full pipeline with instrumentation. Complexity and uncertainty are recorded but do not influence selection.

| Complexity | Uncertainty = False | Uncertainty = True |
|---|---|---|
| SIMPLE | UNCERTAIN_PIPELINE | UNCERTAIN_PIPELINE |
| MEDIUM | UNCERTAIN_PIPELINE | UNCERTAIN_PIPELINE |
| COMPLEX | UNCERTAIN_PIPELINE | UNCERTAIN_PIPELINE |
| UNCERTAIN | UNCERTAIN_PIPELINE | UNCERTAIN_PIPELINE |

---

## Strategy Influence on Selection

### Selection Formula

For any (complexity, uncertainty, strategy) triple, the selector computes:

```
candidates = selection_matrix[strategy][complexity][uncertainty]
if isinstance(candidates, str):
    candidates = [candidates]
pipeline = apply_rules(candidates, rules)
pipeline = apply_strategy_preferences(pipeline, strategy)
return pipeline
```

### Cost-Weighted Selection (BALANCED)

For BALANCED, when multiple candidates are valid (via rules), the selector chooses the pipeline maximizing:

```
score(p) = accuracy_weight(p) / cost_weight(p)

where:
  accuracy_weight(p) = baseline_accuracy[p] - min_accuracy
  cost_weight(p) = relative_cost[p]

  baseline_accuracy = {
      SIMPLE_PIPELINE:    0.65,
      MEDIUM_PIPELINE:    0.82,
      COMPLEX_PIPELINE:   0.91,
      UNCERTAIN_PIPELINE: 0.93
  }

  relative_cost = {
      SIMPLE_PIPELINE:    1.0,
      MEDIUM_PIPELINE:    3.0,
      COMPLEX_PIPELINE:   7.0,
      UNCERTAIN_PIPELINE: 10.0
  }
```

---

## Pipeline Definitions

| Pipeline ID | Execution Order | Required Modules | Typical Use |
|---|---|---|---|
| SIMPLE_PIPELINE | CrossEncoder | CrossEncoder | Factual lookups, greetings, short Q&A |
| MEDIUM_PIPELINE | SemanticIntelligence -> Reasoning | SI, RE | Comparisons, explanations, multi-step |
| COMPLEX_PIPELINE | SemanticIntelligence -> Reasoning -> MADE | SI, RE, MADE | Multi-entity analysis, reasoning chains |
| UNCERTAIN_PIPELINE | CrossEncoder -> SemanticIntelligence -> Reasoning -> MADE | CE, SI, RE, MADE | All modules, fallback, exploration |

---

## Custom Pipeline Support

The `PipelineSelector` supports registering custom pipelines at initialization:

```python
selector.register_pipeline(
    pipeline_id="CUSTOM_LITE",
    components=["CrossEncoder", "LightweightReasoning"],
    relative_cost=1.5,
    baseline_accuracy=0.70,
    priority=10
)
```

Custom pipelines can be referenced in `RoutingRules` or by extending the selection matrix via configuration:

```yaml
selection_matrix_overrides:
  BALANCED:
    SIMPLE:
      false: CUSTOM_LITE
      true: CUSTOM_LITE
```

---

## Rule-Based Selection (RoutingRules)

`RoutingRules` provides a flexible expression engine for pipeline selection overrides. Rules are evaluated in priority order; the first matching rule's action is applied.

### Rule Format

```yaml
routing_rules:
  - name: "short_factual_simple"
    priority: 100
    condition:
      complexity: SIMPLE
      max_length: 20
      strategy: [FASTEST, BALANCED]
    action: "force_pipeline(SIMPLE_PIPELINE)"

  - name: "high_confidence_medium"
    priority: 90
    condition:
      complexity: MEDIUM
      min_semantic_confidence: 0.85
      strategy: [BALANCED]
    action: "force_pipeline(SIMPLE_PIPELINE)"

  - name: "research_override"
    priority: 1000
    condition:
      strategy: RESEARCH
    action: "force_pipeline(UNCERTAIN_PIPELINE)"

  - name: "custom_domain_rule"
    priority: 80
    condition:
      domain: "legal"
      complexity: [COMPLEX, UNCERTAIN]
    action: "force_pipeline(UNCERTAIN_PIPELINE)"
```

### Rule Evaluation Algorithm

```
1. Collect all rules from RoutingRules.registry
2. Filter rules whose conditions match the current (complexity, uncertainty, strategy, context)
3. Sort matching rules by priority (highest first)
4. If a rule action is "force_pipeline(X)":
     a. Verify X is a registered pipeline
     b. If valid, return X immediately
     c. If invalid, skip rule and log warning
5. If no rule matches, fall back to selection matrix
```

---

## Priority Ordering

When multiple selection signals exist (matrix, strategy, rules), priority order is:

| Priority | Source | Description |
|---|---|---|
| 1 (highest) | RoutingRules | User-defined overrides |
| 2 | Strategy | Strategy-specific matrix modifications |
| 3 | Default matrix | Standard (complexity, uncertainty) mapping |
| 4 (lowest) | Fallback | `SIMPLE_PIPELINE` |

---

## Selection Examples

### Example 1: SIMPLE Question, BALANCED Strategy

```
Input: "What is the capital of France?"
Complexity: SIMPLE (score 0.15)
Uncertainty: False
Strategy: BALANCED

Lookup: matrix[BALANCED][SIMPLE][False] = SIMPLE_PIPELINE
No rules match.
Output: SIMPLE_PIPELINE
```

### Example 2: MEDIUM Question, FASTEST Strategy

```
Input: "How do I configure NGINX for WebSocket support?"
Complexity: MEDIUM (score 0.55)
Uncertainty: False
Strategy: FASTEST

Lookup: matrix[FASTEST][MEDIUM][False] = SIMPLE_PIPELINE
Rule "short_factual_simple" does not match (length > 20).
Output: SIMPLE_PIPELINE
```

### Example 3: COMPLEX Question, HIGHEST_ACCURACY

```
Input: "Analyze the comparative effectiveness of transformer-based vs.
        CNN-based approaches for medical image segmentation given limited
        annotated data, and discuss the tradeoffs in terms of accuracy,
        computational cost, and data efficiency."
Complexity: COMPLEX (score 0.89)
Uncertainty: False
Strategy: HIGHEST_ACCURACY

Lookup: matrix[HIGHEST_ACCURACY][COMPLEX][False] = UNCERTAIN_PIPELINE
No rules match.
Output: UNCERTAIN_PIPELINE
```

### Example 4: Uncertainty Triggered

```
Input: "What is the best way to...?"
Complexity: UNCERTAIN (score 0.76, incomplete question)
Uncertainty: True (reasoning module confidence 0.42)
Strategy: BALANCED

Lookup: matrix[BALANCED][UNCERTAIN][True] = UNCERTAIN_PIPELINE
No rules match.
Output: UNCERTAIN_PIPELINE
```

### Example 5: Rule Override

```
Input: "File a motion for summary judgment."
Complexity: COMPLEX (score 0.80)
Uncertainty: False
Strategy: BALANCED
Domain: "legal"

Default lookup: matrix[BALANCED][COMPLEX][False] = COMPLEX_PIPELINE
Rule "custom_domain_rule" matches (domain=legal, complexity=COMPLEX).
Action: force_pipeline(UNCERTAIN_PIPELINE)
Output: UNCERTAIN_PIPELINE
```

---

## Limitations

1. **Matrix explosion**: Each new strategy requires a full 4x2 matrix definition.
2. **No dynamic priority**: Rule priority is static; no mechanism exists for priority reordering based on observed outcomes.
3. **No conflict resolution**: If two rules match at the same priority, behavior is undefined (first encountered wins).
4. **No negative conditions**: Rules cannot express exclusion logic (e.g., "if not SIMPLE").

---

## Future Work

### Probabilistic Selection

Replace deterministic matrix lookups with a probabilistic model that samples pipelines from a distribution conditioned on (complexity, uncertainty). This enables exploration in production for bandit-style optimization.

### Learned Strategy

Train a strategy selector that chooses between FASTEST / BALANCED / HIGHEST_ACCURACY based on predicted latency headroom and accuracy requirements.

### Rule Conflict Detection

Add a validation pass at startup that detects conflicting rules and reports them as errors rather than silently accepting undefined behavior.

### Multi-Output Routing

Support selecting multiple pipelines for ensemble-based answer generation, merging results downstream.

---

## References

- `ares.acr.selection.PipelineSelector` source code
- `ares.acr.selection.RoutingRules` expression engine
- `ares.acr.config.RoutingConfig` YAML schema
- Strategy Comparison Experiment Report, Q3 2025
