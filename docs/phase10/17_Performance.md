# Phase 10 — Performance Goals

## 1. Latency Budgets

| Operation | Target (p50) | Target (p99) | Measurement |
|-----------|-------------|-------------|-------------|
| Agent invocation overhead | < 5 ms | < 20 ms | Time from `AgentCoordinator.invoke()` to `Agent.execute()` |
| Tool invocation overhead | < 2 ms | < 10 ms | Time from `ToolRegistry.execute()` to `Tool.execute()` |
| Workflow step orchestration | < 10 ms | < 50 ms | Time to resolve deps, dispatch, collect |
| Event emission + delivery | < 1 ms | < 5 ms | Time from `emit()` to all subscribers |
| Permission check | < 0.5 ms | < 2 ms | AgentRegistry permission lookup |
| Audit log append | < 1 ms | < 3 ms | AuditEntry serialization + file append |
| Plan creation | < 100 ms | < 500 ms | Goal → Plan decomposition |
| Plan → WorkflowDef conversion | < 10 ms | < 50 ms | Plan data to WorkflowDef DAG |

## 2. Throughput

| Scenario | Target | Constraint |
|----------|--------|------------|
| Agent invocations (single instance) | 1,000 / sec | 2 CPU cores |
| Workflow executions | 100 / sec | 4 CPU cores, 5-step workflows |
| Tool executions | 5,000 / sec | 2 CPU cores |
| Event bus throughput | 50,000 events/sec | Single subscriber per event |
| Concurrent agent executions | 200 | Default `agent_max_concurrency` |

## 3. Memory

| Component | Per-instance | Notes |
|-----------|-------------|-------|
| Agent registration (idle) | < 100 KB | Metadata + ABC instance |
| Tool registration | < 50 KB | Metadata + ABC instance |
| Workflow definition (stored) | < 10 KB | YAML/JSON size |
| Workflow execution context | < 1 MB | Per active execution (ephemeral) |
| Event (in-flight) | < 2 KB | Serialized event |
| Audit entry (batched) | < 1 KB | Before flush to disk |
| Memory tool (delegating to MemoryManager) | ~0 bytes | Delegates to existing MemoryManager |

## 4. Scalability Constraints

| Constraint | Limit | Mitigation |
|------------|-------|------------|
| All agents in single process | Memory-bound (~10k agents) | Process-level isolation (future) |
| Synchronous tool execution (predict) | GPU-bound | Async execution for non-GPU tools |
| EventBus in-memory | Queue depth = event loss if subscriber crashes | File-backed event log (future) |
| Workflow DAG depth | `workflow_max_steps` = 100 | Hard limit; prevents runaway workflows |
| Audit log growth | Unlimited | Log rotation policy (configurable) |

## 5. Benchmarking Strategy

```bash
# Agent invocation benchmark
ares-benchmark agent --count 10000 --concurrency 10

# Workflow execution benchmark
ares-benchmark workflow --workflow analyze_pair --count 1000

# Tool execution benchmark
ares-benchmark tool --tool predict --count 50000

# Event bus benchmark
ares-benchmark eventbus --emit-count 100000 --subscribers 10
```

## 6. Performance Regression Gates

| Metric | Threshold | Action |
|--------|-----------|--------|
| Agent invocation overhead | > 50 ms p99 | Profile and optimize |
| Tool invocation overhead | > 20 ms p99 | Profile and optimize |
| Workflow step orchestration | > 100 ms p99 | Profile and optimize |
| Event delivery | > 10 ms p99 | Profile and optimize |
| Memory per agent | > 1 MB | Profile and optimize |
| Throughput degradation | > 20% drop | Revert specific commit |
