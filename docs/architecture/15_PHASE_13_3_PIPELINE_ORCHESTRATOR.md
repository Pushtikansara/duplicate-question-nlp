# Phase 13.3 — Pipeline + Prediction Orchestrator

**Status:** Implemented (Phase 13.4 will integrate this orchestrator into the
prediction entry points: REST, gRPC, CLI, SDK).

**Scope:** Stage registry, the five default pipeline stages, the pipeline
executor (retry/fallback/cancellation/timing), the ARES engine adapter and
the thin `PredictionOrchestrator` controller with single and batch execution.

---

## 1. Component overview

```
PredictionOrchestrator.run(q1, q2, model=, threshold=, reflect=, skip_cache=, timeout_ms=)
        │
        ▼
   Pipeline.execute(input, state, metadata, cancellation_token)
        │   for stage in StageRegistry.ordered_stages():
        │       pre-hook (event) → timed run → post-hook (event)
        │       on error: RetryPolicy (bounded attempts + backoff)
        │                 → FallbackPolicy (swap engine config, re-run once)
        │                 → re-raise (orchestration error contract)
        ▼
   PredictionResult (orchestration_trace attached)
```

The stage set is **never hardcoded in the orchestrator**: it comes entirely
from the injected `StageRegistry`, which is built config-driven by
`build_default_stage_registry` from `configs/orchestration.yaml`
(`pipeline.stages` section).

## 2. Modules

| Module | Responsibility |
|---|---|
| `stage_registry.py` | `StageRegistry` (register/unregister/resolve/validate/ordered_stages) + `StageDefinition` |
| `stages/validation.py` | `InputValidationStage` — non-empty, printable, bounded length, threshold range |
| `stages/query_understanding.py` | `QueryUnderstandingStage` — QU pipeline + Phase 13.2 cache integration |
| `stages/strategy_selection.py` | `StrategySelectionStage` — routing decision → `EngineConfiguration` via `StrategySelector` |
| `stages/prediction.py` | `PredictionStage` — engine invocation through the `PredictionEngine` protocol |
| `stages/enrichment.py` | `ResultEnrichmentStage` — attaches the orchestration trace to the result |
| `pipeline.py` | `Pipeline` executor: lifecycle events, timing, retry, fallback, cancellation |
| `policies.py` | `DefaultRetryPolicy`, `DefaultFallbackPolicy` (Phase 13.1 protocol implementations) |
| `engine_adapter.py` | `ARESPredictionEngine` — ARES fluent builder + worker-thread timeout |
| `orchestrator.py` | `PredictionOrchestrator` — thin controller, `run` + `run_batch` |
| `factory.py` | `build_default_stage_registry` — config-driven default wiring |

## 3. Stage registry semantics

- Registration rejects duplicates (`DuplicateStageError`), non-`PipelineStage`
  objects (`InvalidStageConfigurationError`), self-dependencies
  (`StageDependencyError`).
- `ordered_stages()` computes the runnable closure (a stage runs only when
  every registered dependency is enabled — dependents of disabled stages are
  skipped), then topologically sorts with Kahn's algorithm; ties are broken
  by explicit `order` value, then stage name. Cycles raise
  `StageDependencyError`.
- `configs/orchestration.yaml` declares all five stages with explicit order
  and the QU → strategy → prediction dependency chain. Unknown stage names
  and unsupported keys are rejected by `build_pipeline_stage_config`.

## 4. Pipeline executor

Per stage the pipeline publishes `orchestration.stage.started` /
`orchestration.stage.complete` (or `orchestration.stage.aborted`) events and
records a `StageResult` (status, duration, failure detail) into
`OrchestrationMetadata`.

- **Retry**: on failure the `RetryPolicy.should_retry(attempt, error)` is
  consulted; backoff (`get_backoff`) is slept between attempts; the retry
  count accumulates in `ExecutionMetadata.retry_count`. Input validation,
  cancellation, timeout, cache and configuration errors are never retried by
  the default policy.
- **Fallback**: after retries are exhausted, the failing stage is re-executed
  once with the `FallbackPolicy.get_fallback_config()` engine configuration
  — only for the strategy-selection and prediction stages, only once, and
  only for transient/execution errors (`TaskExecutionError`,
  `StrategyResolutionError`, `ModelUnavailableError`, `ModelTimeoutError`,
  `MaxRetriesExceededError`). Fallback usage is recorded in
  `ExecutionMetadata.fallback_used` and the trace (`strategy: fallback`).
- **Cancellation**: `CancellationToken` is checked before every stage and
  every retry; cancellation raises `RunCancelledError`.
- **Finalisation**: stage list, per-stage timings, total duration, error,
  model and strategy are copied into `ExecutionMetadata`, and the complete
  trace (including the enrichment stage's own entry) is attached to
  `PredictionResult.orchestration_trace`.

## 5. Orchestrator

- `run(question1, question2, *, model, threshold, reflect, skip_cache,
  timeout_ms, cancellation_token) -> PredictionResult` — thin controller:
  builds `PredictionInput`/`PipelineState`/metadata, runs the pipeline,
  publishes `orchestration.started`/`complete`/`failed`, re-raises
  orchestration errors unchanged.
- `run_batch(pairs, *, ..., max_concurrency=4) -> list[result]` —
  `ThreadPoolExecutor` with bounded concurrency (configured cap
  `max_concurrency`, per-call `max_concurrency` can only lower it), results
  returned in input order, per-pair failures isolated (the exception is
  returned at the pair's index, never propagated). Oversized batches raise
  `ValueError` (`batch_max_pairs` guard).
- No stage logic lives in the orchestrator; the injected `StageRegistry`
  fully determines execution.

## 6. Engine adapter

`ARESPredictionEngine` implements the `PredictionEngine` protocol added to
`interfaces.py`. It applies the selected `EngineConfiguration` through the
ARES fluent builder (`with_model/with_threshold/with_reflection/
with_semantic_validation`) and enforces `timeout_ms` by running the
prediction in a dedicated worker thread:

- timeout → `ModelTimeoutError`
- unknown model / "No models available" → `ModelUnavailableError`
- any other engine failure → `TaskExecutionError`

## 7. Error contract (reuse, no duplication)

All Phase 13.1/13.2 exceptions are reused (`InputValidationError`,
`QueryUnderstandingError`, `StrategyResolutionError`, `ModelUnavailableError`,
`ModelTimeoutError`, `TaskExecutionError`, `RunCancelledError`, `CacheError`,
`PipelineAbortedError`, …). New exceptions are limited to registry concerns:
`DuplicateStageError`, `StageNotFoundError`, `InvalidStageConfigurationError`,
`StageDependencyError`.

`PredictionResult` gained three additive optional fields to carry the
trace/error contract mandated by `06_INTERFACE_SPECIFICATIONS.md`:
`orchestration_trace`, `error`, `error_code` (all default `None`, so existing
construction sites are unaffected).

## 8. Configuration

`configs/orchestration.yaml` gained:

```yaml
cache:
  fail_closed: false          # cache failures fatal when true
pipeline:
  stages:                     # consumed by build_pipeline_stage_config
    InputValidationStage:   { enabled: true, order: 1 }
    QueryUnderstandingStage: { enabled: true, order: 2 }
    StrategySelectionStage:  { enabled: true, order: 3, depends_on: [QueryUnderstandingStage] }
    PredictionStage:         { enabled: true, order: 4, depends_on: [StrategySelectionStage] }
    ResultEnrichmentStage:   { enabled: true, order: 5, depends_on: [PredictionStage] }
```

## 9. Performance measurements (CI machine, no-op stubs)

| Measurement | median | p95 |
|---|---|---|
| Minimal pipeline overhead (1 no-op stage) | 0.007 ms | 0.013 ms |
| Full 5-stage pipeline, QU cache hit | 0.049 ms | 0.060 ms |
| Full 5-stage pipeline, QU cache miss | 0.059 ms | 0.080 ms |
| Strategy resolution (`StrategySelector.resolve`) | 0.007 ms | 0.008 ms |
| Full orchestration via `PredictionOrchestrator.run` | 0.060 ms | 0.099 ms |
| `run_batch` (4 pairs, max_concurrency=4) | ~1.5 ms total | — |

Cache hits cut the full-pipeline p95 by ~25 % versus misses. The measured
bounds are enforced in `test_orchestrator_performance.py` with generous
budgets (2 ms p95 for stage-level work, 20 ms p95 for full orchestration).

## 10. Testing

113 new tests across `test_stage_registry.py`, `test_stages.py`,
`test_pipeline.py`, `test_policies.py`, `test_engine_adapter.py`,
`test_orchestrator.py`, `test_factory.py`, `test_config_loader_stages.py`,
`test_orchestrator_performance.py`. Full orchestration suite: **489 passed**.
Covered: registry validation/ordering, stage behaviours, retry accounting
(including non-retryable classes and backoff timing), fallback swap/re-run
and single-shot semantics, cancellation, event emission, timeout mapping,
trace completeness, batch order/isolation/concurrency bounds, config-driven
stage enablement/ordering, and performance budgets.
