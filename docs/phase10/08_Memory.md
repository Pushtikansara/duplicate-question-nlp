# Phase 10 — Memory Architecture

## 1. Design Principle

The existing `MemoryManager` (30+ files, 10+ interfaces) is the **sole memory backend**. Phase 10 layers event-driven memory operations on top without modifying the existing system.

## 2. Memory as a Service

```
Agent
  │  calls tool (e.g. memory_write, memory_search)
  ▼
Tool Abstraction Layer
  │  validates, audits, emits ToolEvent
  ▼
MemoryTool
  │  delegates to MemoryManager facade
  ▼
MemoryManager (existing, unmodified)
  │
  ├── MemoryStore        (unchanged)
  ├── MemoryIndex        (unchanged)
  ├── RetrievalEngine    (unchanged)
  ├── RetrievalRanker    (unchanged)
  ├── MemoryConsolidator (unchanged)
  ├── ForgettingEngine   (unchanged)
  └── KnowledgeGraph     (unchanged)
```

## 3. NEW: Agent Memory Context

Agents have an **ephemeral execution context** tied to a single workflow run:

```python
@dataclass
class AgentMemoryContext:
    workflow_id: str
    agent_id: str
    trace_id: str
    in_memory_store: dict[str, Any]    # ephemeral — lost after workflow completes
    # Lifecycle:
    # 1. Created when agent is invoked
    # 2. Populated as agent executes (intermediate results)
    # 3. Flushed to persistent MemoryManager on agent completion
    # 4. Discarded after workflow completes (except what was persisted)
```

## 4. NEW: Memory Events

| Event | Payload | Consumer |
|-------|---------|----------|
| `memory.written` | type, key, agent_id, workflow_id | Other agents, audit, telemetry |
| `memory.read` | type, key, agent_id | Audit, telemetry |
| `memory.searched` | query, result_count, agent_id | Telemetry |
| `memory.consolidated` | entries_merged, entries_deleted | Audit |

## 5. Cross-Agent Memory Sharing

| Mode | Mechanism | Use Case |
|------|-----------|----------|
| **Ephemeral** | `AgentMemoryContext.in_memory_store` | Intermediate results within a workflow |
| **Persistent** | `MemoryManager` (tool-mediated) | Long-term knowledge across workflows |
| **Signaled** | EventBus `memory.written` event | Async notification to interested agents |
| **Shared** | Workflow context dict (in `ExecutionContext`) | Within the same workflow DAG |

## 6. Memory Type Extensions

New `MemoryType` values for agent platform:

```python
class MemoryType(Enum):
    EPISODIC          # existing — question-answer experiences
    SEMANTIC          # existing — conceptual knowledge
    REASONING         # existing — reasoning traces
    DEBATE            # existing — multi-agent debate results
    PERFORMANCE       # existing — system performance metrics
    AGENT_STATE       # NEW — agent serialized state (checkpointing)
    WORKFLOW_TRACE    # NEW — full workflow execution trace
    AGENT_COMMS       # NEW — inter-agent messages (for replay/audit)
```
