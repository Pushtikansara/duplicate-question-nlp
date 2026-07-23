# Phase 10 — Internal Interfaces

## 1. Interface Summary

```
┌────────────────────────────────────────────────────────────────────────┐
│ Interface           │ Provider           │ Consumer                     │
├─────────────────────┼────────────────────┼──────────────────────────────┤
│ Agent ABC           │ ares.agents.base   │ AgentCoordinator, WR, CLI    │
│ Tool ABC            │ ares.tools.base    │ ToolRegistry, WR, CLI        │
│ WorkflowDef         │ ares.workflow.models│ WorkflowEngine                │
│ EventBus            │ ares.eventbus.bus  │ Everything                    │
│ Plan                │ ares.planning.types │ PlanningEngine, AgentCoord   │
│ AgentLifecycleManager│ ares.agents.lifecycle│ AgentCoordinator            │
│ AgentRegistry       │ ares.agents.registry│ AgentCoordinator, CLI, API   │
│ ToolRegistry        │ ares.tools.registry │ AgentCoordinator, CLI, API   │
│ WorkflowEngine      │ ares.workflow.engine│ AgentCoordinator, REST, CLI   │
│ PlanningEngine      │ ares.planning.engine│ AgentCoordinator              │
│ OrchestrationStrategy│ ares.orchestration │ AgentCoordinator              │
│ ExecutionContext    │ ares.orchestration  │ All agents and tools          │
└────────────────────────────────────────────────────────────────────────┘
```

## 2. Key Internal Contracts

### Agent ↔ ToolRegistry

```python
class ToolAccessor:
    """Bound set of tools available to a specific agent invocation."""
    def predict(self, **params) -> ToolResult
    def memory_read(self, **params) -> ToolResult
    def memory_write(self, **params) -> ToolResult
    def memory_search(self, **params) -> ToolResult
    def reflect(self, **params) -> ToolResult
    def pipeline(self, **params) -> ToolResult
    # ... dynamically generated from ToolRegistry filtered by permissions

    def get_tool(self, tool_id: str) -> Tool
    def list_available(self) -> list[str]
```

### AgentCoordinator ↔ WorkflowEngine

```python
# AgentCoordinator calls:
class WorkflowEngine:
    async def execute(workflow_id, input, context) -> WorkflowResult

# WorkflowEngine calls:
class AgentCoordinator:
    async def invoke_agent(agent_id, input, context) -> AgentOutput
```

### PlanningEngine ↔ WorkflowEngine

```python
# PlanningEngine produces:
@dataclass
class Plan:
    sub_tasks: list[SubTask]
    dependency_graph: dict[str, list[str]]

# Plan → WorkflowDef conversion:
class WorkflowDef:
    @classmethod
    def from_plan(cls, plan: Plan) -> WorkflowDef
```

### EventBus ↔ Everything

```python
# Any component emits:
event_bus.emit("agent", AgentEvent(...))
event_bus.emit("tool", ToolEvent(...))
event_bus.emit("workflow", WorkflowEvent(...))

# Any component subscribes:
event_bus.subscribe("agent", handler)
event_bus.subscribe("tool.*", handler)  # wildcard support
```

### PluginManager ↔ AgentLifecycleManager

```python
# PluginManager discovers plugins with AGENT capability:
class AgentLifecycleManager:
    def register_from_plugin(self, plugin: AgentPlugin) -> str
```

## 3. Configuration

New settings in `APIConfig.Settings`:

```python
class Settings(BaseSettings):
    # ... existing settings unchanged ...

    # Agent Platform (Phase 10)
    agent_max_concurrency: int = 10
    agent_default_timeout_seconds: int = 30
    agent_max_retries: int = 3
    agent_enable_planning: bool = True
    agent_enable_event_bus: bool = True
    agent_audit_log_enabled: bool = True

    # Workflow
    workflow_max_steps: int = 100
    workflow_timeout_seconds: int = 300
    workflow_store_dir: str = ""      # defaults to {data_dir}/workflows

    # Tool
    tool_enable_audit: bool = True
    tool_max_input_size_bytes: int = 1_000_000
```

## 4. Exception Hierarchy

```python
# New exceptions in ares.api.exceptions (alongside existing ones):
class AgentError(ARESAPIError):         # status_code=500
    error_code = "AGENT_ERROR"
class AgentNotFoundError(AgentError):   # status_code=404
    error_code = "AGENT_NOT_FOUND"
class AgentPermissionError(AgentError): # status_code=403
    error_code = "AGENT_PERMISSION_DENIED"
class AgentTimeoutError(AgentError):    # status_code=504
    error_code = "AGENT_TIMEOUT"

class ToolError(ARESAPIError):          # status_code=500
    error_code = "TOOL_ERROR"
class ToolNotFoundError(ToolError):     # status_code=404
    error_code = "TOOL_NOT_FOUND"
class ToolPermissionError(ToolError):   # status_code=403
    error_code = "TOOL_PERMISSION_DENIED"

class WorkflowError(ARESAPIError):      # status_code=500
    error_code = "WORKFLOW_ERROR"
class WorkflowNotFoundError(WorkflowError): # status_code=404
    error_code = "WORKFLOW_NOT_FOUND"
class WorkflowStepError(WorkflowError): # status_code=500
    error_code = "WORKFLOW_STEP_ERROR"
```
