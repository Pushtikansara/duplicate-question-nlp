# Regression Report — Phase 10.5.5

## Test Summary

| Suite | Passed | Failed | Errors |
|-------|--------|--------|--------|
| Existing tests (baseline) | 2476 | 1 | 5 |
| New stabilization tests | 48 | 0 | 0 |
| **Total** | **2524** | **1** | **5** |

## Pre-Existing Failures (Unrelated)

1. `tests/integration/tools/test_tool_orchestration.py::TestToolOrchestrationIntegration::test_agent_uses_memory_tool`
   - `KeyError: 'value'` — fixture mismatch, unrelated to Phase 10.5.5

2. `tests/unit/tools/test_builtin.py::TestMemoryTool` (5 errors)
   - `AttributeError` — fixture issue, unrelated to Phase 10.5.5

## New Stabilization Tests

| Test Class | Count | Description |
|------------|-------|-------------|
| `TestReflectionConsistency` | 9 | Trust/risk/review/recommendations mapping |
| `TestGraphValidator` | 7 | Self-loops, duplicates, cycles, missing nodes, DAG check |
| `TestSemanticValidation` | 5 | Entity ambiguity detection, confidence adjustment |
| `TestCalibration` | 4 | Model-specific scaling, overconfidence detection |
| `TestMemoryStoreCapacity` | 8 | FIFO eviction, TTL sweep, stats, per-tier |
| `TestMetricsRegistry` | 5 | Singleton, counter, gauge, snapshot, reset |
| `TestStrategyEnforcer` | 6 | Strategy resolution, fallback, case-insensitive |
| `TestOptimizerDedup` | 3 | Node deduplication, edge rewiring |
| **Total** | **48** | |

## Code Quality

- ruff: 0 errors
- Unused imports removed
- Dead code eliminated
- Import sorting applied
