# Phase 10 — Agent Lifecycle

## 1. State Machine

```
                  ┌──────────┐
                  │ DISCOVERED │
                  └─────┬─────┘
                        │ validate()
                        ▼
                  ┌──────────┐
                  │ PENDING   │
                  └─────┬─────┘
                        │ register()
                        ▼
                  ┌──────────┐
          ┌───────│ REGISTERED │◄──────┐
          │       └─────┬─────┘       │
          │             │ load()      │
          │             ▼             │
          │       ┌──────────┐        │
          │       │  LOADED  │        │
          │       └─────┬─────┘       │
          │             │ activate()  │
          │             ▼             │
          │       ┌──────────┐        │
     ┌────┴───────│  ACTIVE  │────────┤
     │            └─────┬─────┘       │
     │                  │             │
     │            ┌─────┴─────┐       │
     │            ▼           ▼       │
     │      ┌─────────┐ ┌─────────┐   │
     │      │ PAUSED  │ │ ERROR   │   │
     │      └────┬────┘ └────┬────┘   │
     │           │ reactivate│ retry()│
     │           └───────────┘        │
     │                               │
     └────── disable() ──────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │ DISABLED │
                    └──────────┘

Valid transitions:
  DISCOVERED → PENDING      (validation passes)
  PENDING    → REGISTERED   (on registration)
  REGISTERED → LOADED       (on load)
  LOADED     → ACTIVE       (on activation)
  ACTIVE     → PAUSED       (on pause)
  PAUSED     → ACTIVE       (on resume)
  ACTIVE     → ERROR        (on unhandled exception)
  ERROR      → ACTIVE       (on retry/restart)
  ACTIVE     → DISABLED     (on disable)
  ERROR      → DISABLED     (on disable)
  DISABLED   → REGISTERED   (on enable)
```

## 2. LifecycleManager API

```python
class AgentLifecycleManager:
    def register(self, agent_cls: type[Agent], metadata: AgentMetadata) -> str
    def load(self, agent_id: str) -> None
    def activate(self, agent_id: str) -> None
    def pause(self, agent_id: str) -> None
    def resume(self, agent_id: str) -> None
    def disable(self, agent_id: str) -> None
    def enable(self, agent_id: str) -> None
    def retry(self, agent_id: str) -> None
    def unregister(self, agent_id: str) -> None
    def get_status(self, agent_id: str) -> AgentStatus
    def list_agents(self, status: AgentStatus | None = None) -> list[AgentInfo]
```

## 3. Guards and Policies

| Transition | Guard |
|------------|-------|
| PENDING → REGISTERED | Metadata validation (name uniqueness, capability declaration, tool dependency resolution) |
| REGISTERED → LOADED | Dependency check (all referenced tools exist in ToolRegistry) |
| LOADED → ACTIVE | `on_activate()` hook returns HookResult.CONTINUE |
| ACTIVE → PAUSED | Graceful — current invocation completes before pausing |
| ERROR → ACTIVE | Max retry count (default 3) and backoff policy |

## 4. Integration with Existing Plugin System

```python
# New in ares.plugins.types — added to PluginCapability enum
class PluginCapability(Enum):
    # ... existing 14 capabilities unchanged ...
    AGENT = auto()            # NEW — plugin provides an agent
    WORKFLOW = auto()         # NEW — plugin provides a workflow
    TOOL = auto()             # NEW — plugin provides a tool
```

Agents are themselves plugins. A plugin declares `AGENT` capability and implements `Agent` ABC. The `PluginManager` delegates to `AgentLifecycleManager` for the agent-specific lifecycle hooks.
