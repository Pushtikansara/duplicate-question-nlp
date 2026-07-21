# AdaptiveRoutingEngine: Routing Orchestration

**Deep Dive into Phase 5 Orchestration**

- **Version:** 1.0.0
- **Module:** `ares.acr.engine.AdaptiveRoutingEngine`

---

## Overview

The `AdaptiveRoutingEngine` is the central orchestrator of the Adaptive Cognitive Routing system. It coordinates five sequential estimation stages, manages error handling per stage, and produces a `RoutingResult` that downstream cognitive modules consume.

This document provides a stage-by-stage breakdown of the engine's internal execution, covering input validation, component invocation, output aggregation, and integration patterns.

---

## Purpose

The AdaptiveRoutingEngine exists to:

1. **Sequence** the routing stages in a deterministic order
2. **Validate** inputs before routing begins
3. **Isolate** failures per stage so one component failure does not cascade
4. **Aggregate** outputs from each estimator into a coherent routing decision
5. **Produce** a standardized `RoutingResult` struct for downstream consumption
6. **Support** pluggable estimator implementations through a common interface

---

## Orchestration Flow

```
  Input
  (QuestionText, Metadata, RoutingContext)
    |
    v
+-----------------------+
| 1. Input Validation   |  Check non-empty, length bounds, UTF-8 encoding
+-----------+-----------+
            |
            v
+-----------------------+
| 2. Complexity Stage   |  ComplexityEstimator.predict(question, context)
+-----------+-----------+
            |
            v
+-----------------------+
| 3. Uncertainty Stage  |  UncertaintyRouter.evaluate(question,
|                       |      cross_encoder_conf, semantic_conf, reason_conf)
+-----------+-----------+
            |
            v
+-----------------------+
| 4. Selection Stage    |  PipelineSelector.select(complexity, uncertainty,
|                       |      strategy, rules)
+-----------+-----------+
            |
            v
+-----------------------+
| 5. Estimation Stage   |  CostEstimator.estimate(pipeline_id, question)
|                       |  LatencyEstimator.estimate(pipeline_id, question)
+-----------+-----------+
            |
            v
+-----------------------+
| 6. Result Assembly    |  Build RoutingResult with all outputs,
|                       |  metadata, and timing diagnostics
+-----------------------+
```

---

## Stage-by-Stage Breakdown

### Stage 1: Input Validation

**Component**: `AdaptiveRoutingEngine._validate_input()`

```python
def _validate_input(self, question: str, context: RoutingContext) -> None:
    if not question or not question.strip():
        raise InvalidInputError("Question text is empty")
    if len(question) > self.config.max_question_length:
        raise InvalidInputError(
            f"Question exceeds max length {self.config.max_question_length}"
        )
    if not question.isprintable():
        raise InvalidInputError("Question contains non-printable characters")
```

Validation rules:

| Rule | Default | Behavior on Violation |
|---|---|---|
| Non-empty | true | Raise `InvalidInputError` |
| Max length | 4096 characters | Raise `InvalidInputError` |
| Printable characters | true | Raise `InvalidInputError` |
| Valid UTF-8 | true | Raise `InvalidInputError` |

### Stage 2: Complexity Estimation

**Component**: `ComplexityEstimator.predict()`

Invoked with the validated question and optional context. The engine passes the raw question string; the estimator handles tokenization internally.

**Interface**:

```python
class ComplexityEstimator(ABC):
    @abstractmethod
    def predict(
        self,
        question: str,
        context: Optional[RoutingContext] = None
    ) -> ComplexityResult:
        ...
```

**Error handling**: If the estimator raises an exception or times out (>500ms), the engine catches the error and sets complexity to `UNCERTAIN` with a diagnostic flag.

**Output**:

```python
@dataclass
class ComplexityResult:
    tier: ComplexityTier  # SIMPLE | MEDIUM | COMPLEX | UNCERTAIN
    score: float          # 0.0 to 1.0
    features: Dict[str, float]
    processing_time_ms: float
```

### Stage 3: Uncertainty Routing

**Component**: `UncertaintyRouter.evaluate()`

Requires confidence scores from upstream modules (CrossEncoder, SemanticIntelligence, Reasoning). If scores are not yet computed, the router can optionally trigger lightweight probes.

**Interface**:

```python
class UncertaintyRouter(ABC):
    @abstractmethod
    def evaluate(
        self,
        question: str,
        cross_encoder_confidence: Optional[float],
        semantic_confidence: Optional[float],
        reasoning_confidence: Optional[float],
        context: Optional[RoutingContext] = None
    ) -> UncertaintyResult:
        ...
```

**Error handling**: Missing confidence scores default to 0.0 (maximum uncertainty). If the router itself fails, the engine assumes `UncertaintyResult(uncertain=True, source="fallback")`.

**Output**:

```python
@dataclass
class UncertaintyResult:
    uncertain: bool
    source: Optional[str]         # which module triggered uncertainty
    details: Dict[str, float]     # per-module confidence breakdown
    processing_time_ms: float
```

### Stage 4: Pipeline Selection

**Component**: `PipelineSelector.select()`

The core decision point. Takes complexity tier, uncertainty flag, routing strategy, and optional rules.

**Interface**:

```python
class PipelineSelector(ABC):
    @abstractmethod
    def select(
        self,
        complexity: ComplexityResult,
        uncertainty: UncertaintyResult,
        strategy: RoutingStrategy,
        rules: Optional[RoutingRules] = None
    ) -> SelectionResult:
        ...
```

**Error handling**: If selection fails (e.g., invalid strategy, missing pipeline mapping), the engine falls back to `SIMPLE_PIPELINE`.

**Output**:

```python
@dataclass
class SelectionResult:
    pipeline_id: str
    strategy_applied: RoutingStrategy
    rules_matched: List[str]
    selection_confidence: float
    processing_time_ms: float
```

### Stage 5: Cost and Latency Estimation

**Components**: `CostEstimator.estimate()` and `LatencyEstimator.estimate()`

These two estimators run sequentially (cost first, then latency). They share the same pipeline ID and question context.

**Interfaces**:

```python
class CostEstimator(ABC):
    @abstractmethod
    def estimate(
        self,
        pipeline_id: str,
        question: str,
        context: Optional[RoutingContext] = None
    ) -> CostEstimate:
        ...

class LatencyEstimator(ABC):
    @abstractmethod
    def estimate(
        self,
        pipeline_id: str,
        question: str,
        context: Optional[RoutingContext] = None
    ) -> LatencyEstimate:
        ...
```

**Error handling**: Negative or NaN estimates are replaced with defaults from `RoutingConfig.cost_defaults` and `RoutingConfig.latency_defaults`.

**Outputs**:

```python
@dataclass
class CostEstimate:
    relative_cost: float      # normalized against SIMPLE_PIPELINE = 1.0
    cost_units: str           # "relative" | "tokens" | "flops"
    breakdown: Dict[str, float]
    processing_time_ms: float

@dataclass
class LatencyEstimate:
    expected_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    processing_time_ms: float
```

### Stage 6: Result Assembly

**Component**: `AdaptiveRoutingEngine._assemble_result()`

Aggregates all stage outputs into a single `RoutingResult`.

```python
@dataclass
class RoutingResult:
    pipeline_id: str
    complexity: ComplexityResult
    uncertainty: UncertaintyResult
    selection: SelectionResult
    cost: CostEstimate
    latency: LatencyEstimate
    total_routing_time_ms: float
    fallback_triggered: bool
    warnings: List[str]
```

---

## Pluggable Estimators

Each estimator interface supports multiple implementations. Registration is done via dependency injection at engine construction time.

```python
class AdaptiveRoutingEngine:
    def __init__(
        self,
        config: RoutingConfig,
        complexity_estimator: ComplexityEstimator,
        uncertainty_router: UncertaintyRouter,
        pipeline_selector: PipelineSelector,
        cost_estimator: CostEstimator,
        latency_estimator: LatencyEstimator,
    ):
        self.config = config
        self._complexity = complexity_estimator
        self._uncertainty = uncertainty_router
        self._selector = pipeline_selector
        self._cost = cost_estimator
        self._latency = latency_estimator
```

This design allows:

- Swapping heuristic estimators for ML-based ones without changing orchestration
- Injecting mock estimators for unit testing
- Wrapping estimators with caching, rate-limiting, or circuit-breaker decorators

---

## Error Handling Per Stage

| Stage | Failure Mode | Catch | Default Output | Diagnostic |
|---|---|---|---|---|
| Validation | Empty question | `InvalidInputError` | Propagate to caller | N/A |
| Complexity | Exception / timeout | `Exception` | `UNCERTAIN`, score 0.0 | `fallback_triggered=True` |
| Uncertainty | Exception / timeout | `Exception` | `uncertain=True` | `fallback_triggered=True` |
| Selection | Missing pipeline | `KeyError` | `SIMPLE_PIPELINE` | `warnings.append(...)` |
| Cost | Negative / NaN | Runtime check | Default cost from config | `warnings.append(...)` |
| Latency | Negative / NaN | Runtime check | Default latency from config | `warnings.append(...)` |

---

## Integration Points

### Upstream: Perception (Phase 4)

Perception passes a `RoutingContext` containing:

- Raw question text
- Detected language
- Token count
- Upstream confidence scores (CrossEncoder output)
- Session metadata

### Downstream: Cognitive Modules (Phases 6-9)

Cognitive modules receive `RoutingResult` and use `pipeline_id` to determine their execution behavior:

- `SIMPLE_PIPELINE`: CrossEncoder only
- `MEDIUM_PIPELINE`: SemanticIntelligence -> Reasoning
- `COMPLEX_PIPELINE`: SemanticIntelligence -> Reasoning -> MADE
- `UNCERTAIN_PIPELINE`: Full pipeline from CrossEncoder through MADE

### Telemetry

Every `RoutingResult` is emitted to the telemetry system for:

- Real-time dashboard monitoring of routing decisions
- Offline analysis of strategy effectiveness
- Threshold tuning via historical data

---

## Limitations

1. **Sequential bottleneck**: Stages cannot run in parallel, adding 10-50ms overhead per request.
2. **No stage caching**: Repeated identical questions re-run all stages.
3. **No dynamic reconfiguration**: Strategy changes require engine restart or config reload.
4. **Single language assumption**: The engine does not validate language consistency between stages.

---

## Future Work

### Concurrent Stage Execution

Allow ComplexityEstimator and UncertaintyRouter to execute in parallel via `asyncio.gather()` or thread pools, reducing orchestration overhead by 40-60%.

### Semantic Caching

Cache `ComplexityResult` and `UncertaintyResult` keyed by question embedding similarity. Repeated questions bypass stages 2 and 3 entirely.

### Live Configuration Reload

Support hot-reloading of `RoutingConfig` via signal handler or watch loop, enabling dynamic threshold adjustment without restart.

### Multi-Language Support

Add language detection validation and per-language estimator dispatch, allowing language-specific complexity models.

---

## References

- `ARES.ACR.Engine` source package
- `RoutingResult` protobuf schema definition
- `RoutingConfig` YAML schema documentation
- Pluggable Estimator Interface Design RFC
