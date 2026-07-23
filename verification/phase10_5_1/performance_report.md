# Performance Report — Phase 10.5.1

## Measured Timings

The demo pipeline tracks these timing metrics for each execution:

| Metric | Source | Description |
|--------|--------|-------------|
| Planning Time | PlanningEngine + Planner | Goal decomposition, plan creation, validation, optimization |
| Prediction Time | ARES engine | Model inference latency |
| Memory Write Time | MemoryManager.store | Key-value storage |
| Memory Read Time | MemoryManager.search | Semantic search retrieval |
| Reflection Time | ReflectionEngine | Trust scoring, risk assessment |
| Execution Time | OrchestrationEngine | Agent orchestration |
| Total Time | Overall | Complete pipeline wall time |

## PlanningEngine Metrics

The existing PlanningMetrics tracks:

| Metric | Description |
|--------|-------------|
| `plans_created` | Total plans generated |
| `plans_completed` | Successfully executed plans |
| `plans_failed` | Failed plans |
| `failure_rate` | Ratio of failed to created |
| `avg_planning_latency_ms` | Average time to create a plan |
| `avg_execution_latency_ms` | Average time to execute a plan |
| `avg_node_count` | Average nodes per plan |
| `total_retries` | Total retry count |
| `avg_optimization_gain_pct` | Average latency improvement from optimization |

## Event Bus Stats

The EventBus tracks total events emitted and event type distribution.

## Observability Features

- [x] Execution Timeline
- [x] Planning Time
- [x] Execution Time
- [x] Optimization Time
- [x] Total Latency
- [x] Agent Execution Order
- [x] Tool Calls
- [x] Memory Reads
- [x] Memory Writes
- [x] Events
- [x] Retries (via PlanExecutor)
- [x] Timeouts (via PlanExecutor)
- [x] Failures
- [x] Recovery (via retry logic)
- [x] Parallel Execution (via PlanOptimizer)
- [x] Plan Graph
- [x] Final Plan
- [x] Final Output
