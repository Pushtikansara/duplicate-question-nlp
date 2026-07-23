# Phase 10.5 — Architecture Report

## Dependency Flow

```
PlanningEngine
  ├── Planner → produces PlanGraph
  ├── PlanValidator → validates PlanGraph
  ├── PlanOptimizer → optimizes PlanGraph
  └── PlanExecutor → executes via Orchestrator
       ├── Orchestrator → runs Agents
       │    ├── AgentManager / AgentRegistry (from ares.agents)
       │    └── ToolManager (from ares.tools)
       └── MemoryManager (from ares.memory)
```

## Reuse Verification

| Existing System | Reused? | How |
|----------------|---------|-----|
| `ares.orchestration.task_graph.TaskGraph` | ✅ | PlanGraph reuses DAG/cycle detection patterns (adapted for PlanNode) |
| `ares.orchestration.engine.OrchestrationEngine` | ✅ | PlanExecutor delegates to Orchestrator for agent execution |
| `ares.agents.manager.AgentManager` | ✅ | PlanExecutor uses AgentManager for agent lookup |
| `ares.agents.registry.AgentRegistry` | ✅ | PlanExecutor uses registry for agent resolution |
| `ares.tools.manager.ToolManager` | ✅ | PlanValidator checks tool permissions against ToolManager |
| `ares.memory.base.MemoryManager` | ✅ | PlanningEngine stores goals/plans/results via MemoryManager |
| Event patterns | ✅ | PlanningEvent mirrors OrchestrationEvent/AgentEvent pattern |
| Error hierarchy | ✅ | PlanningException extends ARESAPIError (same as all other ares packages) |

## Non-duplication Verification

- ❌ No duplicate planners — new `Planner` is the only planner
- ❌ No duplicate graphs — `PlanGraph` wraps planning concepts, `TaskGraph` remains for orchestration
- ❌ No duplicate executors — `PlanExecutor` delegates to `Orchestrator`
- ❌ No duplicate validators — `PlanValidator` is for planning-level concerns only
- ❌ No duplicate memory — uses existing `MemoryManager`
- ❌ `duplicate_question_app/` untouched

## Circular Import Check

```
ares.planning → ares.orchestration → ares.agents → ares.tools → ares.memory
                                                              → ares.api
ares.memory → ares.api
ares.agents → ares.api
ares.tools → ares.api
ares.orchestration → ares.agents, ares.tools
```

No circular imports detected. Planning depends on existing systems; existing systems never depend on planning.
