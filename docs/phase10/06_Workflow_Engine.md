# Phase 10 — Workflow Engine Design

## 1. Workflow Definition (YAML Schema)

```yaml
# Example workflow: analyze_question_pair
id: "analyze_pair.v1"
name: "Analyze Question Pair"
description: "Full cognitive analysis of a duplicate question pair"
version: "1.0.0"
tags: ["cognitive", "analysis"]

inputs:
  question1: { type: string, required: true }
  question2: { type: string, required: true }
  threshold: { type: float, default: 0.5 }

steps:
  - id: "preprocess"
    type: "sequential"                # node type
    steps:                            # nested sub-steps for sequential groups
      - id: "perception"
        agent: "perception_agent"
        input:
          question1: "${input.question1}"
          question2: "${input.question2}"
        tools: ["perception"]

      - id: "semantic_analysis"
        agent: "semantic_agent"
        depends_on: ["perception"]     # explicit dependency (implied if sequential)

  - id: "cognitive_debate"
    type: "parallel"                  # all agents run concurrently
    agents:
      - "intent_agent"
      - "entity_agent"
      - "relation_agent"
      - "conflict_agent"
    depends_on: ["semantic_analysis"]

  - id: "consensus"
    type: "agent"
    agent: "consensus_agent"
    strategy: "debate"                # uses DebateEngine internally
    depends_on: ["cognitive_debate"]
    input:
      agent_results: "${steps.cognitive_debate.results}"

  - id: "reflection"
    type: "conditional"               # branch based on condition
    condition: "${steps.consensus.confidence} < 0.6"
    if_true:
      - id: "deep_reflect"
        agent: "reflection_agent"
        tools: ["reflect", "memory_search"]
    if_false: []

  - id: "store_result"
    type: "tool"
    tool: "memory_write"
    depends_on: ["consensus", "reflection"]
    input:
      memory_type: "semantic"
      content: "${steps.consensus}"

output:
  result: "${steps.consensus.result}"
  confidence: "${steps.consensus.confidence}"
  trace: "${steps}"
```

## 2. Node Types

| Type | Behavior | Max Children |
|------|----------|--------------|
| `agent` | Single agent execution | 1 output |
| `sequential` | Run sub-steps in order, passing output to input | N sub-steps |
| `parallel` | Run all sub-steps concurrently; merge results | N sub-steps |
| `conditional` | Evaluate condition; run if_true or if_false branch | 2 branches |
| `tool` | Single tool invocation | 1 output |
| `foreach` | Iterate over list input, execute body for each item | 1 body |
| `map` | Parallel map over list input | 1 body |
| `transform` | Inline data transformation (filter, aggregate, sort) | 1 output |

## 3. Workflow Engine

```python
class WorkflowEngine:
    def __init__(self, registry: AgentRegistry, tool_registry: ToolRegistry, event_bus: EventBus)

    async def execute(
        self,
        workflow_id: str,
        input: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> WorkflowResult:
        """Load WorkflowDef, build DAG, execute topologically, return result."""

    def register_workflow(self, workflow: WorkflowDef) -> str:
        """Register a workflow definition (from YAML/dict)."""

    def get_workflow(self, workflow_id: str) -> WorkflowDef | None:
        """Retrieve a stored workflow definition."""

    def list_workflows(self) -> list[WorkflowDef]:
        """List all registered workflows."""

    def delete_workflow(self, workflow_id: str) -> bool:
        """Unregister a workflow."""

    def export_workflow(self, workflow_id: str) -> str:
        """Serialize workflow to YAML."""
```

## 4. DAG Execution Algorithm

```
1. Load WorkflowDef
2. Build adjacency list from depends_on edges
3. Topological sort (Kahn's algorithm)
4. For each batch of nodes with all dependencies met:
   a. Execute nodes in parallel (asyncio.gather)
   b. Collect results in shared context dict
   c. Emit WorkflowEvent.STEP_COMPLETED for each node
5. Build WorkflowResult from final context state
```

## 5. WorkflowResult

```python
@dataclass
class WorkflowResult:
    workflow_id: str
    status: WorkflowStatus          # PENDING | RUNNING | COMPLETED | FAILED | CANCELLED
    input: dict[str, Any]
    output: dict[str, Any]          # final output per output spec
    steps: dict[str, NodeResult]    # results keyed by step id
    processing_time_ms: float
    error: str | None = None
    trace_id: str = ""
```

## 6. Variable Substitution

Workflow definitions use `${...}` expressions for dynamic values:

| Expression | Resolves To |
|------------|-------------|
| `${input.var}` | Workflow input parameter |
| `${steps.step_id.result}` | Output of a previous step |
| `${steps.step_id.confidence}` | Confidence of a previous step |
| `${context.trace_id}` | Execution context |
| `${env.VAR}` | Environment variable |

## 7. Storage

`WorkflowStore` persists workflow definitions as JSON files in `config.data_dir / workflows/`:

```python
class WorkflowStore:
    def save(self, workflow: WorkflowDef) -> None
    def load(self, workflow_id: str) -> WorkflowDef | None
    def delete(self, workflow_id: str) -> bool
    def list(self) -> list[str]        # returns workflow IDs
    def load_all(self) -> list[WorkflowDef]
```
