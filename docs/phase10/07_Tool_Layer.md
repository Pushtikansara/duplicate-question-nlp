# Phase 10 — Tool Abstraction Layer

## 1. Design Principle

Agents never import services directly. All interactions go through **Tools**, which are registered, permissioned, observable, and auditable.

## 2. Tool ABC

```python
class Tool(ABC):
    metadata: ToolMetadata           # id, name, version, description
    permissions_required: list[str]  # e.g. ["memory:read", "predict:execute"]

    @abstractmethod
    async def execute(self, input: ToolInput) -> ToolResult:
        """Execute the tool with given input."""

    @abstractmethod
    def spec(self) -> ToolSpec:
        """OpenAPI-like schema for tool parameters and returns."""

    def validate(self, input: ToolInput) -> None:
        """Pre-execution validation."""

    def on_register(self, registry: ToolRegistry) -> None:
        """Lifecycle hook when tool is registered."""
```

## 3. ToolRegistry

```python
class ToolRegistry:
    def register(self, tool: Tool) -> None
    def unregister(self, tool_id: str) -> None
    def get(self, tool_id: str) -> Tool | None
    def list(self) -> list[ToolMetadata]
    def execute(self, tool_id: str, input: ToolInput, agent_id: str) -> ToolResult
    def get_permissions(self, tool_id: str) -> list[str]
```

## 4. Built-in Tools

| Tool ID | Wraps | Permissions |
|---------|-------|-------------|
| `predict` | `ARES.predict()` | `predict:execute` |
| `predict_batch` | `ARES.predict_batch()` | `predict:execute` |
| `pipeline` | `CognitivePipeline.run()` | `pipeline:execute` |
| `reason` | `ReasonEngine.reason()` | `reason:execute` |
| `reflect` | `ReflectionEngine.evaluate()` | `reflect:execute` |
| `memory_read` | `MemoryManager.retrieve()` | `memory:read` |
| `memory_write` | `MemoryManager.store_episodic/semantic/etc.()` | `memory:write` |
| `memory_search` | `MemoryManager.search()` | `memory:read` |
| `memory_stats` | `MemoryManager.get_statistics()` | `memory:read` |
| `memory_clean` | `MemoryManager.consolidate()` | `memory:write` |
| `plugin_list` | `PluginManager.list()` | `plugins:read` |
| `plugin_exec` | `PluginManager.run_hook()` | `plugins:execute` |
| `http_request` | `httpx.AsyncClient` | `network:http` |

## 5. Tool Execution Flow

```
Agent.execute(input)
  │
  ▼
AgentCoordinator
  │  binds ToolAccessor (permissions-filtered set of tools)
  ▼
Agent.execute(input)
  │  calls tool via self.tools.predict(...)
  ▼
ToolRegistry.execute(tool_id, input, agent_id)
  │  1. Permission check (agent_id has required scope?)
  │  2. Tool spec validation
  │  3. Execute tool
  │  4. Emit ToolEvent.INVOKED on EventBus
  │  5. Record metric (latency, success/failure)
  │  6. Audit log entry
  │
  ▼
ToolResult returned to Agent
```

## 6. ToolSpec (OpenAPI-inspired)

```python
@dataclass
class ToolSpec:
    id: str
    description: str
    parameters: dict[str, ParameterSchema]   # name → type, required, default, description
    returns: ReturnSchema                    # type, schema
    permissions_required: list[str]
    timeout_seconds: float = 30.0
    idempotent: bool = False
    rate_limit_category: str = "default"
```

## 7. Example: PredictTool

```python
class PredictTool(Tool):
    metadata = ToolMetadata(
        id="predict",
        name="Question Similarity Predictor",
        version="1.0.0",
        description="Predicts whether two questions are semantically duplicate",
    )
    permissions_required = ["predict:execute"]

    def __init__(self):
        self._engine = ARES()               # ← existing singleton

    async def execute(self, input: ToolInput) -> ToolResult:
        result = self._engine.predict(
            input.params["question1"],
            input.params["question2"],
            model=input.params.get("model"),
            threshold=input.params.get("threshold"),
            reflect=input.params.get("reflect", False),
        )
        return ToolResult(
            tool_id=self.metadata.id,
            success=True,
            data=asdict(result),
            confidence=result.confidence,
            processing_time_ms=result.latency_ms,
        )

    def spec(self) -> ToolSpec:
        return ToolSpec(
            id="predict",
            description=self.metadata.description,
            parameters={
                "question1": ParameterSchema(type="string", required=True),
                "question2": ParameterSchema(type="string", required=True),
                "model": ParameterSchema(type="string", required=False),
                "threshold": ParameterSchema(type="float", required=False),
                "reflect": ParameterSchema(type="boolean", required=False),
            },
            returns=ReturnSchema(type="object"),
            permissions_required=self.permissions_required,
            idempotent=True,
        )
```
