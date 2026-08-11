# Phase 13.5 — Agent/Diagnostic Orchestration Semantics

## 1. Goal

Route `MultiAgentEngine._predict_phase` and diagnostic endpoints (`/reason`,
`/reflection`, `/trace`, gRPC `run_pipeline`/`run_reflection`) through the
orchestrator via an explicit "raw result" mode instead of constructing `ARES()`
directly.

## 2. Deliverables

| File | Change |
|------|--------|
| `src/ares/orchestration/pipeline.py` | `skip_stages` parameter on `Pipeline.execute()` |
| `src/ares/orchestration/orchestrator.py` | `skip_stages` forwarded from `PredictionOrchestrator.run()` |
| `src/ares/orchestration/prediction_service.py` | `predict_raw()` method on `PredictionService` |
| `src/ares/agents/multi_agent_engine.py` | `_predict_phase` uses `get_prediction_service().predict_raw()` |
| `src/ares/api/routers/reason.py` | Uses orchestrator via `predict_raw()` |
| `src/ares/api/routers/reflection.py` | Uses orchestrator via `predict_raw()` |
| `src/ares/api/routers/trace.py` | Uses orchestrator via `predict_raw()` |
| `src/ares/grpc/services.py` | `run_pipeline`/`run_reflection` use `predict_raw()`; removed `self._engine` |

## 3. Raw Result Mode

`PredictionService.predict_raw()` delegates to the orchestrator with
`skip_stages=(STAGE_RESULT_ENRICHMENT,)`. This runs the full pipeline
(query understanding → strategy selection → prediction) but skips result
enrichment, returning the raw `PredictionResult` with orchestration trace
that excludes the enrichment stage.

**When to use raw mode:**
- Diagnostic endpoints that need engine-level output without enrichment
- Multi-agent consumers that inspect raw trust/risk scores directly

**When NOT to use raw mode:**
- Canonical prediction paths (`predict()`, `predict_batch()`) — always enrich
- User-facing REST `/predict` — full pipeline is desired

## 4. Pipeline skip_stages

`Pipeline.execute()` now accepts `skip_stages: tuple[str, ...] = ()`.
Stages whose `.name` appears in the tuple are excluded from execution.
Metadata correctly records only the stages that actually ran.

```python
pipeline.execute(input, state, metadata, skip_stages=("result_enrichment",))
```

## 5. Backward Compatibility

- `PredictionService.predict()` is unchanged — always runs full pipeline
- `PredictionService.predict_batch()` is unchanged
- REST `/predict` and gRPC `predict`/`predict_batch` are unchanged
- Direct `ARES()` usage is preserved in: `engine_adapter.py`, `__init__.py`
  (public API), `demo_engine.py`, and non-diagnostic endpoints (benchmark,
  system, pipeline, profile)

## 6. Test Coverage

| Test | What it validates |
|------|-------------------|
| `TestPipelineSkipStages` (6 tests) | Pipeline excludes named stages, handles empty/nonexistent skip lists |
| `TestPredictionServiceRaw` (4 tests) | `predict_raw()` skips enrichment, forwards overrides, runs pipeline |
| Existing `TestReflectionEndpoint` (9 tests) | Reflection endpoint returns correct response shape |
| Existing `TestTraceEndpoint` (9 tests) | Trace endpoint returns correct response shape |
| All existing orchestration/entrypoint tests (3987+) | No regressions |

**Total: 3996 passed** (1 pre-existing environmental failure: `tabulate` not installed)

## 7. Phase Status

| Criterion | Status |
|-----------|--------|
| All entry points route through orchestrator | ✅ |
| Raw mode skips enrichment, preserves pipeline | ✅ |
| MultiAgentEngine uses orchestrator | ✅ |
| Diagnostic endpoints use orchestrator | ✅ |
| 0 regressions from Phase 13.4 | ✅ |
| Lint clean | ✅ |
| Typecheck clean | ✅ |

## 8. Future Work

- **Phase 13.6:** external/Redis cache provider behind `CacheProvider`;
  multi-process cache sharing; per-request configuration overrides through
  the service.
