# Phase 10 — Milestone Roadmap (10.1 – 10.8)

## Overview

```
10.1 ─── 10.2 ─── 10.3 ─── 10.4 ─── 10.5 ─── 10.6 ─── 10.7 ─── 10.8
  │        │        │        │        │        │        │        │
  │        │        │        │        │        │        │        └─ Platform GA + docs
  │        │        │        │        │        │        └─ Security + hardening
  │        │        │        │        │        └─ Observability + perf
  │        │        │        │        └─ Planning engine
  │        │        │        └─ Event bus + internal comms
  │        │        └─ REST APIs + CLI + gRPC
  │        └─ Workflow engine + tool layer
  └─ Agent ABC + lifecycle + registry
```

## Milestone 10.1 — Agent Foundation

**Goal**: Agent ABC, lifecycle manager, registry, and built-in agent wrappers.

**Deliverables**:
- `ares/agents/__init__.py`, `base.py`, `types.py`, `registry.py`, `lifecycle.py`
- `ares/agents/builtin/` — wrappers for all 8 existing `CognitiveAgent` implementations
- Agent state machine (REGISTERED → LOADED → ACTIVE → PAUSED → ERROR → DISABLED)
- `AgentLifecycleManager` with full state transition guards
- Unit tests: 80 tests
- **Gate**: All 1960 existing tests pass; agent lifecycle tests pass

**Risks**: None — purely new code, no modifications to existing system.

---

## Milestone 10.2 — Workflow Engine + Tool Layer

**Goal**: Workflow DAG engine and Tool Abstraction Layer.

**Deliverables**:
- `ares/workflow/engine.py`, `models.py`, `storage.py`, `executor.py`, `types.py`
- `ares/tools/` — `base.py`, `registry.py`, `types.py`
- `ares/tools/builtin/` — 12 built-in tools (predict, batch_predict, pipeline, reason, reflect, memory_read/write/search/stats/clean, plugin_list, http_request)
- Workflow YAML schema + parser
- Sequential, parallel, conditional node execution
- File-backed `WorkflowStore`
- Unit tests: 150 tests

**Dependencies**: 10.1

**Risks**: Variable substitution (`${...}`) complexity; keep scope limited to simple expressions in 10.2.

---

## Milestone 10.3 — REST APIs + CLI + gRPC

**Goal**: All new functionality accessible via existing access layers.

**Deliverables**:
- `ares/api/routers/agents.py` — new router with agent endpoints
- `ares/api/routers/workflows.py` — new router with workflow endpoints
- `ares/api/routers/tools.py` — new router with tool endpoints
- `ares/api/routers/execute.py` — unified execution endpoint
- CLI subcommands: `ares agent`, `ares workflow`, `ares tool`, `ares execute`
- gRPC service extensions (new methods on `AresGrpcService`)
- Client SDK: `ares.client.AgentClient`, `WorkflowClient`, `ToolClient`
- Integration tests: 20 tests
- Updated OpenAPI schema

**Dependencies**: 10.2

**Risks**: Router count grows; ensure auth middleware coverage for all new endpoints.

---

## Milestone 10.4 — Event Bus + Internal Communication

**Goal**: Global event bus for async agent communication and system observability.

**Deliverables**:
- `ares/eventbus/bus.py` — `EventBus` singleton
- `ares/eventbus/events.py` — typed event classes
- `ares/eventbus/subscribers.py` — Telemetry, Audit, Metrics subscribers
- Bridge to existing plugin `EventBus`
- Event-driven memory write on agent completion
- Unit tests: 30 tests

**Dependencies**: 10.1

**Risks**: Async event delivery in synchronous contexts (e.g., gRPC handler); use `emit_sync` pattern.

---

## Milestone 10.5 — Multi-Agent Orchestration

**Goal**: AgentCoordinator with orchestration strategies, consensus, and scheduling.

**Deliverables**:
- `ares/orchestration/coordinator.py` — `AgentCoordinator`
- `ares/orchestration/scheduler.py` — `AgentScheduler` (asyncio-based)
- `ares/orchestration/policies.py` — `RunPolicies`, retry/backoff/timeout
- Orchestration strategies: Sequential, Parallel, Debate (wrapping `DebateEngine`), Chain, Supervisor
- `DebateOrchestrator` — wraps existing `DebateEngine` as a strategy
- Unit tests: 50 tests; integration tests: 10 tests

**Dependencies**: 10.1, 10.2, 10.4

**Risks**: Concurrent agent execution may expose threading issues in existing code (MemoryManager, File I/O). Mitigation: asyncio + thread pool for synchronous tools.

---

## Milestone 10.6 — Planning Engine

**Goal**: Dynamic goal decomposition and plan→workflow conversion.

**Deliverables**:
- `ares/planning/engine.py` — `PlanningEngine`
- `ares/planning/decomposer.py` — `DefaultDecomposer`, `CognitiveDecomposer`
- `ares/planning/planner_types.py` — `Goal`, `SubTask`, `Plan`, `PlanStatus`
- Re-planning strategies: RETRY, ALTERNATE, SKIP, DECOMPOSE, ESCALATE
- Plan → WorkflowDef converter
- Unit tests: 30 tests; integration tests: 5 tests

**Dependencies**: 10.2, 10.5

**Risks**: Decomposer quality depends on domain knowledge. Start with rule-based decomposers; LLM-based decomposers are future work.

---

## Milestone 10.7 — Observability + Performance

**Goal**: Production-grade metrics, tracing, audit, and performance tuning.

**Deliverables**:
- Agent-level metrics (invocations, latency, errors, confidence)
- Workflow-level traces (OpenTelemetry spans per step)
- Audit log implementation (file-backed)
- Performance benchmarks (agent, workflow, tool, event bus)
- Optimization pass based on benchmark results
- Performance regression gates in CI
- Security tests: permission enforcement, isolation, timeout
- Documentation: performance tuning guide

**Dependencies**: 10.5, 10.6

**Risks**: Audit log I/O may impact throughput under load. Mitigation: async batch writer with configurable flush interval.

---

## Milestone 10.8 — Platform GA

**Goal**: General availability — hardening, documentation, and release.

**Deliverables**:
- Full test pass: all unit + integration + regression + security + performance
- API documentation (OpenAPI + Markdown)
- Plugin authoring guide (MD + examples)
- Migration guide for Phase 9.5/9.6 users
- CLI help text review and polish
- Final security audit
- Release notes

**Dependencies**: 10.1 – 10.7

**Risks**: Scope creep. Strictly no new features in 10.8 — only stabilization.

---

## Dependency Graph

```
10.1 ──────────────────────────────────────────────────────▶ 10.8
 │                                                           ▲
 ├──▶ 10.2 ──▶ 10.3 ────────────────────────────────────────┤
 │             │                                             │
 │             └──▶ 10.5 ──▶ 10.6 ──▶ 10.7 ─────────────────┤
 │                            │                              │
 └──▶ 10.4 ──────────────────┘                              │
                                                            │
All milestones feed into 10.8 (GA)                          │
```

## Estimated Effort

| Milestone | Files | LOC | Tests | Effort (dev-weeks) |
|-----------|-------|-----|-------|---------------------|
| 10.1 | 15 | ~1,500 | 80 | 2 |
| 10.2 | 25 | ~3,000 | 150 | 3 |
| 10.3 | 10 | ~2,000 | 20 | 2 |
| 10.4 | 8 | ~1,000 | 30 | 1 |
| 10.5 | 10 | ~2,000 | 60 | 3 |
| 10.6 | 8 | ~1,500 | 35 | 2 |
| 10.7 | 5 | ~1,000 | 40 | 2 |
| 10.8 | 5 | ~500 | 10 | 1 |
| **Total** | **86** | **~12,500** | **425** | **16** |

## Architectural Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Existing synchronous tools block async agent flow | High | High | Wrap sync tools in `asyncio.to_thread()`; keep TAL interface async |
| MemoryManager thread-safety under concurrent agent access | Medium | High | Audit existing locks in MemoryManager; add tests |
| Plugin Manager conflicts with new Agent/Tool plugins | Low | Medium | Separate `PluginCapability` enum; no shared state |
| YAML workflow DSL becomes too complex | Medium | Medium | Start simple; add node types iteratively across milestones |
| EventBus becomes bottleneck under high load | Low | Medium | Async delivery; in-process queue; separate subscriber threads |
| Permission model too complex for plugin authors | Medium | Low | Sensible defaults; permissive by default, restrictive on opt-in |
