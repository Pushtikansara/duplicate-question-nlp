# Execution Trace — Phase 10.5.1

## Complete Pipeline Flow

```
User Request (question1 + question2)
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  DemoEngine.run_demo()                                       │
├──────────────────────────────────────────────────────────────┤
│  1. EventBus: demo_started                                   │
│  2. DemoEngine.initialize() (if not initialized)             │
│     - Register PredictTool in ToolRegistry                   │
│     - Register MemoryTool in ToolRegistry                    │
│     - Register PlannerAgent in AgentRegistry                 │
│     - Register PredictAgent in AgentRegistry                 │
│     - Register MemoryAgent in AgentRegistry                  │
│     - Register ReflectionAgent in AgentRegistry              │
│     - Activate all agents                                   │
│  3. EventBus: scenario_selected                              │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  [Phase 1] PLANNING                                         │
├──────────────────────────────────────────────────────────────┤
│  a. PlanningEngine.create_goal(description)                  │
│     → Goal object created with sub-goals                    │
│  b. EventBus: planning_started                               │
│  c. PlanningEngine.create_plan(goal, strategy, agents)       │
│     → PlanGraph with nodes + edges                           │
│  d. PlanningEngine.validate_plan(graph, agents, tools)       │
│     → Validation errors (or empty)                           │
│  e. PlanningEngine.optimize_plan(graph)                      │
│     → Optimization statistics                                │
│  f. EventBus: planning_completed                             │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  [Phase 2] PREDICTION                                       │
├──────────────────────────────────────────────────────────────┤
│  a. EventBus: prediction_started                             │
│  b. ARES.predict(question1, question2)                       │
│     → PredictionResult with label, confidence, latency       │
│  c. EventBus: prediction_completed                           │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  [Phase 3] MEMORY STORE                                     │
├──────────────────────────────────────────────────────────────┤
│  a. EventBus: memory_write_started                           │
│  b. MemoryManager.store(key="prediction:{goal_id}", ...)     │
│     → MemoryEntry stored                                     │
│  c. EventBus: memory_write_completed                         │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  [Phase 4] MEMORY READ                                      │
├──────────────────────────────────────────────────────────────┤
│  a. EventBus: memory_read_started                            │
│  b. MemoryManager.search("prediction:", limit=10)            │
│     → List of MemoryEntry objects                            │
│  c. EventBus: memory_read_completed                          │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  [Phase 5] REFLECTION                                       │
├──────────────────────────────────────────────────────────────┤
│  a. EventBus: reflection_started                             │
│  b. ReflectionEngine.reflect(prediction=...)                 │
│     → Trust score, risk level, recommendations              │
│  c. MemoryManager.store(key="reflection:{goal_id}", ...)     │
│  d. EventBus: reflection_completed                           │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  [Phase 6] ORCHESTRATION                                    │
├──────────────────────────────────────────────────────────────┤
│  a. EventBus: execution_started                              │
│  b. OrchestrationEngine.run_agents(agents, input, strategy)  │
│     → AgentCoordinator resolves agents                      │
│     → SequentialStrategy executes agents in order           │
│     → Each agent receives input, produces output            │
│  c. EventBus: execution_completed (or execution_error)      │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  [Phase 7] RESULTS                                          │
├──────────────────────────────────────────────────────────────┤
│  a. EventBus: demo_completed                                 │
│  b. Return comprehensive result dict with:                   │
│     - Goal, Plan, Prediction, Reflection                    │
│     - Memory entries                                        │
│     - Orchestration results                                 │
│     - Timeline with latencies                               │
│     - Event stream                                          │
│     - Final response text                                   │
└──────────────────────────────────────────────────────────────┘
```

## Agent Execution Order

1. **PlannerAgent** — Creates goal, generates plan, validates, optimizes
2. **PredictAgent** — Makes duplicate question prediction
3. **MemoryAgent** — Stores prediction results, retrieves history
4. **ReflectionAgent** — Assesses trust, risk, recommendations

## Tool Calls

1. **PredictTool** — `predict` operation → ARES inference engine
2. **MemoryTool** — `store` and `search` operations → MemoryManager

## Memory Operations

1. **Write**: `prediction:{goal_id}` — stores prediction result
2. **Write**: `reflection:{goal_id}` — stores reflection result
3. **Read**: Search all `prediction:` prefixed entries
