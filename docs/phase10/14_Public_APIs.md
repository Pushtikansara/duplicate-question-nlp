# Phase 10 — Public APIs

## 1. REST API Extensions

All new endpoints are prefixed under `/api/v1/agents` and `/api/v1/workflows`. Existing endpoints remain unchanged.

### Agent Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/agents` | `require_admin` | List all registered agents |
| GET | `/api/v1/agents/{id}` | `require_admin` | Get agent metadata and status |
| POST | `/api/v1/agents/{id}/invoke` | `require_user` | Invoke a single agent |
| POST | `/api/v1/agents/{id}/pause` | `require_admin` | Pause an agent |
| POST | `/api/v1/agents/{id}/resume` | `require_admin` | Resume an agent |
| POST | `/api/v1/agents/{id}/disable` | `require_admin` | Disable an agent |

### Workflow Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/workflows` | `require_admin` | List registered workflows |
| GET | `/api/v1/workflows/{id}` | `require_admin` | Get workflow definition |
| POST | `/api/v1/workflows` | `require_admin` | Register a new workflow (YAML body) |
| POST | `/api/v1/workflows/{id}/execute` | `require_user` | Execute a workflow |
| GET | `/api/v1/workflows/{id}/result/{run_id}` | `require_user` | Get workflow execution result |
| DELETE | `/api/v1/workflows/{id}` | `require_admin` | Unregister a workflow |

### Tool Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/tools` | `require_admin` | List registered tools and their specs |
| POST | `/api/v1/tools/{id}/execute` | `require_user` | Execute a tool directly |

### Execution Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/execute` | `require_user` | General execution: agent, tool, or workflow |
| GET | `/api/v1/execute/{run_id}` | `require_user` | Get execution status/result |
| DELETE | `/api/v1/execute/{run_id}` | `require_admin` | Cancel execution |

## 2. CLI Extensions

New sub-commands under the existing `ares` CLI:

```bash
ares agent list                      # list agents
ares agent show <id>                 # show agent details
ares agent invoke <id> --params ...  # invoke an agent
ares agent pause <id>
ares agent resume <id>
ares agent disable <id>
ares agent enable <id>

ares workflow list                   # list workflows
ares workflow show <id>              # show workflow YAML
ares workflow register <file.yaml>   # register workflow from file
ares workflow run <id> --params ...  # execute workflow
ares workflow result <run_id>        # get result

ares tool list                       # list tools
ares tool show <id>                  # show tool spec
ares tool execute <id> --params ...  # execute tool

ares execute --agent <id>            # execute agent
ares execute --workflow <id>         # execute workflow
ares execute --tool <id>             # execute tool
ares execute status <run_id>         # check execution status
```

## 3. Python SDK (ares.client)

```python
class AgentClient:
    async def list_agents(self) -> list[AgentInfo]
    async def invoke_agent(self, agent_id: str, params: dict) -> AgentOutput
    async def pause_agent(self, agent_id: str) -> None
    async def resume_agent(self, agent_id: str) -> None

class WorkflowClient:
    async def list_workflows(self) -> list[WorkflowDef]
    async def register_workflow(self, definition: dict) -> str
    async def execute_workflow(self, workflow_id: str, params: dict) -> str  # returns run_id
    async def get_workflow_result(self, run_id: str) -> WorkflowResult

class ToolClient:
    async def list_tools(self) -> list[ToolSpec]
    async def execute_tool(self, tool_id: str, params: dict) -> ToolResult

class ExecutionClient:
    async def execute(self, target: ExecuteTarget) -> str  # returns run_id
    async def get_status(self, run_id: str) -> ExecutionStatus
```

## 4. gRPC Extensions

New methods added to `AresGrpcService`:

```python
class AresGrpcService:
    # Existing methods (unchanged)
    def predict(self, ...)
    def predict_batch(self, ...)
    def health(self)
    def version(self)
    def system_info(self)
    def run_pipeline(self, ...)
    def run_reflection(self, ...)
    def search_memory(self, ...)
    def list_plugins(self)

    # New methods (Phase 10)
    def list_agents(self) -> list[AgentInfo]
    def invoke_agent(self, agent_id: str, params: dict) -> AgentOutput
    def register_workflow(self, workflow_def: dict) -> str
    def execute_workflow(self, workflow_id: str, params: dict) -> WorkflowResult
    def list_tools(self) -> list[ToolSpec]
    def execute_tool(self, tool_id: str, params: dict) -> ToolResult
```

## 5. Plugin API (Stable)

The plugin author API for Phase 10:

```python
from ares.plugins import Plugin, PluginCapability, PluginMetadata
from ares.agents import Agent, AgentInput, AgentOutput
from ares.tools import Tool, ToolInput, ToolResult
from ares.workflow import WorkflowPlugin
```

No imports from `ares.agents.builtin`, `ares.workflow.engine`, or other internal packages are exposed.
