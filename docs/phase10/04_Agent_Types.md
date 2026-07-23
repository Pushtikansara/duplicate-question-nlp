# Phase 10 — Agent Types and Responsibilities

## 1. Agent Taxonomy

```
Agent (ABC)
├── CognitiveAgent (builds on existing _agents.CognitiveAgent)
│   ├── IntentAgent
│   ├── SemanticAgent
│   ├── EntityAgent
│   ├── RelationAgent
│   ├── ConflictAgent
│   ├── ConfidenceAgent
│   ├── EvidenceAgent
│   └── ConsensusAgent
│
├── WorkflowAgent (executes a named WorkflowDef)
│   └── Invokes other agents via WorkflowEngine
│
├── DecisionAgent (makes yes/no/uncertain decisions)
│   └── Aggregates multiple CognitiveAgent outputs
│
├── MemoryAgent (manages memory as a service)
│   ├── StoreAgent
│   ├── RetrieveAgent
│   ├── SearchAgent
│   └── ConsolidateAgent
│
├── PlanningAgent (decomposes goals into plans)
│   └── Uses PlanningEngine internally
│
├── MonitoringAgent (health, metrics, alerts)
│   └── Watches other agents and system resources
│
├── GatewayAgent (proxies external API calls)
│   └── HTTP / gRPC / CLI wrappers
│
└── PluginAgent (user-defined, loaded via PluginManager)
    └── Any custom logic implementing the Agent ABC
```

## 2. Agent ABC

```python
class Agent(ABC):
    metadata: AgentMetadata           # id, name, version, capabilities, tools
    status: AgentStatus
    context: AgentContext             # logger, config, event_bus reference

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Primary execution method. Called by the orchestrator."""

    @abstractmethod
    def capabilities(self) -> set[AgentCapability]:
        """Declared capabilities for routing decisions."""

    def on_activate(self) -> HookResult:
        """Lifecycle hook — called when agent becomes ACTIVE."""

    def on_pause(self) -> HookResult:
        """Lifecycle hook — called when agent is paused."""

    def on_error(self, exc: Exception) -> HookResult:
        """Lifecycle hook — called on unhandled exception."""
```

## 3. Agent Metadata Schema

```yaml
agent_id: "intent_agent.v2"
name: "Intent Analysis Agent"
version: "2.0.0"
type: "cognitive"            # cognitive | workflow | planning | memory | monitoring | gateway | plugin
capabilities:
  - "intent_analysis"
  - "semantic_understanding"
tools_required:
  - "predict"
  - "memory_search"
tools_optional:
  - "reflect"
dependencies:
  - plugin_id: "semantic_agent"
    version_spec: ">=1.0"
    optional: false
timeout_seconds: 30
max_retries: 3
permissions:
  - "memory:read"
  - "predict:execute"
```

## 4. Agent Input/Output Contract

```python
@dataclass
class AgentInput:
    task: str                          # description of what to do
    params: dict[str, Any]            # task-specific parameters
    context: ExecutionContext          # trace_id, workflow_id, parent_agent_id
    tools: ToolAccessor               # bound tool set (permissions-filtered)

@dataclass
class AgentOutput:
    agent_id: str
    status: AgentExecutionStatus       # SUCCESS | FAILURE | PARTIAL | BLOCKED
    result: dict[str, Any]            # agent-specific result data
    confidence: float                  # 0.0 - 1.0
    evidence: list[Evidence]
    warnings: list[str]
    processing_time_ms: float
    trace: SpanContext                 # OpenTelemetry span for this execution
```

## 5. Built-in Agent Wrappers

Each existing `CognitiveAgent` in `duplicate_question_app._agents` gets a thin `ares.agents.builtin` wrapper that implements the new `Agent` ABC and delegates `execute()` → `evaluate()`. This is purely an adapter — the existing logic is unmodified.

```python
class IntentAgent(Agent):
    def __init__(self):
        self._inner = _agents.IntentAgent()

    async def execute(self, input: AgentInput) -> AgentOutput:
        # Extract SemanticRepresentations from input params
        # Call self._inner.evaluate(rep_a, rep_b, assessment, reasoning)
        # Convert AgentResult → AgentOutput
```
