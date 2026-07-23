# Phase 10 — Security Model

## 1. Principles

| Principle | Implementation |
|-----------|----------------|
| Least privilege | Each agent has a role-bound permission set |
| Defense in depth | API auth (Phase 9.6) + agent-level auth + tool-level auth |
| Full audit | Every agent call, tool call, and workflow step is logged |
| Isolation | Agents cannot access other agents' ephemeral context |
| No backdoors | Tool Abstraction Layer is the ONLY way agents access services |

## 2. Permission Model

```
Agent Role
  │
  ├── agent:execute          — agent can be invoked by orchestrator
  ├── agent:monitor          — agent can observe other agents' outputs
  ├── tool:access            — agent can use tools (further scoped)
  │
  └── Tool Permissions
        ├── predict:execute
        ├── pipeline:execute
        ├── reason:execute
        ├── reflect:execute
        ├── memory:read
        ├── memory:write
        ├── plugins:read
        ├── plugins:execute
        └── network:http
```

## 3. Permission Assignment

```python
@dataclass
class AgentPermissions:
    agent_id: str
    allowed_tools: list[str]         # tool IDs this agent may use
    memory_scopes: list[MemoryScope] # which memory types agent can read/write
    max_invocations_per_minute: int = 1000
    allowed_agents: list[str] | None = None  # None = all; [] = none; [...] = specific

@dataclass
class MemoryScope:
    memory_type: str
    access: Literal["read", "write", "both"]
```

## 4. Permission Enforcement Points

```
┌──────────────────────────────────────────────────┐
│ 1. API Gateway (Phase 9.6)                        │
│    - JWT/API key → UserRole → endpoint access     │
│                                                    │
│ 2. AgentRegistry                                   │
│    - AgentPermission assigned on register()        │
│    - Permissions immutable while agent is ACTIVE   │
│                                                    │
│ 3. ToolRegistry.execute()                          │
│    - Checks agent_id has required permission       │
│    - Returns PermissionDenied if not               │
│                                                    │
│ 4. EventBus.emit()                                 │
│    - Sensitive events carry permission check       │
│                                                    │
│ 5. AuditLogger                                      │
│    - Every denied access attempt is logged         │
└──────────────────────────────────────────────────┘
```

## 5. Audit Log Schema

```python
@dataclass
class AuditEntry:
    timestamp: datetime
    event_type: str                 # "agent.invoked" | "tool.executed" | "permission.denied"
    agent_id: str
    workflow_id: str
    trace_id: str
    tool_id: str | None
    input_snapshot: dict            # params (PII-safelisted)
    result_status: str              # "success" | "failure" | "denied"
    processing_time_ms: float
    error: str | None
```

## 6. Security Boundaries

| Boundary | Separation Mechanism |
|----------|---------------------|
| Agent ↔ Agent | No shared memory (except via EventBus or MemoryManager) |
| Agent ↔ Tool | TAL permission check on every invocation |
| Agent ↔ Plugin | Plugin runs in same process; capabilities gated by permissions |
| Agent ↔ External | GatewayAgent with network policy (allow/deny list) |
| Agent ↔ OS | No filesystem access except via Tools |
| REST API ↔ Agent | Authentication enforced (Phase 9.6) before AgentCoordinator |

## 7. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Agent runs forever | per-agent timeout (configurable, default 30s) |
| Agent consumes too many resources | max_concurrency, max_memory_bytes policies |
| Agent accesses restricted memory | MemoryScope enforcement in TAL |
| Agent leaks data via EventBus | Events marked with sensitivity level |
| Rogue plugin agent | Plugin signing / hash verification (future) |
