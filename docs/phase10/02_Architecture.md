# Phase 10 — High-Level Architecture

## 1. Architecture Diagram (Logical)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      EXISTING ACCESS LAYERS                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐   │
│  │ REST API │  │   CLI    │  │   gRPC   │  │ Python SDK (client)│   │
│  │ :8000    │  │  ares    │  │ :50051   │  │ ares.client       │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬──────────┘   │
│       │              │              │                  │              │
├───────┴──────────────┴──────────────┴──────────────────┴──────────────┤
│                                                                       │
│                      ┌──────────────────────┐                         │
│                      │   WORKFLOW ENGINE    │  ◄── NEW                │
│                      │  (DAG orchestrator)  │                         │
│                      └──────────┬───────────┘                         │
│                                 │                                     │
│                      ┌──────────┴───────────┐                         │
│                      │    PLANNING ENGINE   │  ◄── NEW                │
│                      │ (goal decomposition) │                         │
│                      └──────────┬───────────┘                         │
│                                 │                                     │
│                      ┌──────────┴───────────┐                         │
│                      │   AGENT ORCHESTRATOR │  ◄── NEW                │
│                      │  (coordinates agents)│                         │
│                      └──────────┬───────────┘                         │
│                                 │                                     │
│              ┌──────────────────┼──────────────────┐                  │
│              ▼                  ▼                  ▼                  │
│  ┌────────────────────┐ ┌────────────────┐ ┌──────────────────┐      │
│  │   TOOL ABSTRACTION │ │   AGENT POOL   │ │   EVENT BUS      │ ◄──  │
│  │   LAYER (TAL)      │ │  (agent registry)│ │  (pub/sub)       │ NEW  │
│  └─────────┬──────────┘ └────────────────┘ └──────────────────┘      │
│            │                                                          │
├────────────┼──────────────────────────────────────────────────────────┤
│            ▼         EXISTING SERVICES                                 │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │     │
│  │  │ PREDICT  │  │  MEMORY  │  │ REFLECT  │  │   PIPELINE  │  │     │
│  │  │ Service  │  │ Manager  │  │  Engine  │  │   Service   │  │     │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │     │
│  │  │ PLUGIN   │  │   CORE   │  │ REASONING│  │   SEARCH    │  │     │
│  │  │ Manager  │  │  Engine  │  │  Engine  │  │   Service   │  │     │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## 2. Package Structure

```
src/ares/
  __init__.py                 # ← export Agent, Workflow, Tool classes
  _engine.py                  # unchanged
  _result.py                  # unchanged

  api/                        # unchanged — routers remain
  cli/                        # unchanged — new agent/workflow subcommands added
  client/                     # unchanged — new agent/workflow client methods
  grpc/                       # unchanged — new endpoints proxied through TAL
  plugins/                    # unchanged — AgentPlugin extended, not modified

  agents/                     # ◄── NEW PACKAGE
    __init__.py               # exports Agent, AgentType, AgentStatus
    base.py                   # Agent ABC — the new universal agent interface
    registry.py               # AgentRegistry (replaces agents/agent_registry.py)
    types.py                  # AgentResult, AgentMetadata, AgentCapability
    lifecycle.py              # AgentLifecycleManager
    builtin/                  # ◄── Built-in agents wrapping existing CognitiveAgent
      __init__.py
      intent_agent.py         # wraps duplicate_question_app._agents.IntentAgent
      semantic_agent.py
      entity_agent.py
      relation_agent.py
      conflict_agent.py
      confidence_agent.py
      evidence_agent.py
      consensus_agent.py
    wrappers/                 # ◄── Agent adapters for external systems
      __init__.py
      http_agent.py
      cli_agent.py
      grpc_agent.py

  tools/                      # ◄── NEW PACKAGE
    __init__.py
    base.py                   # Tool ABC
    registry.py               # ToolRegistry
    types.py                  # ToolResult, ToolSpec
    builtin/
      __init__.py
      predict_tool.py         # wraps ARES.predict
      batch_predict_tool.py
      pipeline_tool.py
      reason_tool.py
      reflect_tool.py
      memory_read_tool.py
      memory_write_tool.py
      memory_search_tool.py
      memory_stats_tool.py
      plugin_list_tool.py
      search_tool.py

  workflow/                   # ◄── NEW PACKAGE
    __init__.py
    engine.py                 # WorkflowEngine — DAG executor
    models.py                 # WorkflowDef, WorkflowStep, WorkflowStatus
    storage.py                # WorkflowStore (file-backed)
    executor.py               # step executors (sequential, parallel, conditional)
    types.py                  # WorkflowResult, NodeResult

  planning/                   # ◄── NEW PACKAGE
    __init__.py
    engine.py                 # PlanningEngine
    decomposer.py             # Hierarchical task decomposer
    planner_types.py          # Plan, SubTask, PlanStatus

  eventbus/                   # ◄── NEW PACKAGE
    __init__.py
    bus.py                    # Global EventBus (pub/sub)
    events.py                 # Event types (AgentEvent, ToolEvent, WorkflowEvent)
    subscribers.py            # Background subscribers (metrics, audit, telemetry)

  orchestration/              # ◄── NEW PACKAGE
    __init__.py
    coordinator.py            # AgentCoordinator — orchestrates multi-agent runs
    scheduler.py              # AgentScheduler — manages concurrent execution
    policies.py               # Selection, retry, timeout policies
```

## 3. Backward Compatibility Strategy

| Existing Component | Phase 10 Change |
|-------------------|-----------------|
| `ares.api.routers.*` | **Unchanged** — all endpoints keep working |
| `ares.cli.commands.*` | **Unchanged** — new `agent` and `workflow` commands added |
| `ares.grpc.services.AresGrpcService` | **Unchanged** — remains as synchronous facade |
| `ares.plugins.base.Plugin` | **Unchanged** — `AgentPlugin` is a NEW subclass, not a modification |
| `duplicate_question_app._agents.*` | **Unchanged** — `Agent` in `ares.agents` wraps it |
| `duplicate_question_app._memory.*` | **Unchanged** — tools call it through existing `MemoryManager` |
| Existing tests | **Unchanged** — must all continue to pass |

## 4. Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| New `ares/agents/` package vs. modify `duplicate_question_app/_agents/` | Isolation: existing agents are domain-specific; Phase 10 agents are platform-agnostic. The new `Agent` ABC generalizes beyond duplicate-detection. |
| Tool Abstraction Layer (TAL) | Decouples agents from services. Agents never import `MemoryManager` or `ARES` directly — they use tools. Enables permissions, auditing, and hot-swap. |
| Event Bus as global singleton | Required for async agent communication and observability. Single bus with typed event channels prevents coupling. |
| Workflow engine separate from agent orchestrator | Workflows coordinate agents; orchestrator manages agent lifecycle. Separation of concerns. |
| File-backed storage (not SQL) | Matches existing data_dir pattern in Phase 9.5. Keeps the dependency footprint unchanged. |
| All new code in `ares/` package | Preserves the `duplicate_question_app` package as a pure ML engine. Phase 10 is a platform layer, not an engine change. |
