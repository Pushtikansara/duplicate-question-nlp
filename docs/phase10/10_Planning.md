# Phase 10 — Planning Engine

## 1. Design Principle

The `PlanningEngine` enables agents to decompose a high-level goal into a DAG of sub-tasks that the `WorkflowEngine` can execute. Planning is optional — simple tasks can bypass it and use pre-registered workflows.

## 2. Planning Flow

```
User/Agent submits goal
       │
       ▼
PlanningEngine.receive(goal)
       │
       ▼
Goal Decomposer
  │  Breaks goal into sub-goals
  │  Uses registered decomposer strategies
  ▼
Sub-task Graph
  │  DAG where nodes = sub-tasks, edges = dependencies
  ▼
Plan Validator
  │  Checks: all dependencies resolvable? tools available? agents available?
  ▼
Plan → converted to WorkflowDef
       │
       ▼
WorkflowEngine.execute(workflow)
       │
       ▼
PlanResult (success/failure, trace, metrics)
```

## 3. PlanningEngine API

```python
class PlanningEngine:
    async def create_plan(self, goal: Goal) -> Plan:
        """Decompose a goal into a plan (DAG of sub-tasks)."""

    async def execute_plan(self, plan: Plan, context: ExecutionContext) -> PlanResult:
        """Convert plan to workflow and execute via WorkflowEngine."""

    async def replan(self, plan: Plan, failed_step: str, reason: str) -> Plan:
        """Re-plan around a failed step."""

    def register_decomposer(self, domain: str, decomposer: DecomposerStrategy) -> None:
        """Register a domain-specific decomposer."""

    def validate_plan(self, plan: Plan) -> list[str]:
        """Validate plan viability. Returns list of warnings."""
```

## 4. DecomposerStrategy

```python
class DecomposerStrategy(ABC):
    @abstractmethod
    async def decompose(self, goal: Goal) -> list[SubTask]: ...

    @property
    @abstractmethod
    def domain(self) -> str: ...

class DefaultDecomposer(DecomposerStrategy):
    """Generic hierarchical task decomposer.

    Pattern:
      Goal → sub-goals → atomic tasks
      Each atomic task maps to one agent or tool.
    """
    domain = "general"

class CognitiveDecomposer(DecomposerStrategy):
    """Specialized for duplicate-question analysis.

    Decomposes "analyze pair" → perception, routing, semantic, reasoning, debate
    Matching the existing cognitive pipeline stages.
    """
    domain = "cognitive_analysis"
```

## 5. Plan Representation

```python
@dataclass
class Goal:
    description: str
    constraints: dict[str, Any]      # timeout, quality, etc.
    context: dict[str, Any]          # input data
    priority: int = 0

@dataclass
class SubTask:
    id: str
    description: str
    agent_id: str | None = None      # specific agent, or
    tool_id: str | None = None       # specific tool, or
    workflow_id: str | None = None   # sub-workflow
    input_mapping: dict[str, str]    # maps parent context → sub-task input
    depends_on: list[str]            # sub-task IDs
    timeout_seconds: float = 30.0
    retry_policy: RetryPolicy = RetryPolicy()

@dataclass
class Plan:
    id: str
    goal: Goal
    sub_tasks: list[SubTask]
    dependency_graph: dict[str, list[str]]  # sub_task_id → list of sub_task_ids
    status: PlanStatus
    metadata: dict[str, Any]

class PlanStatus(Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RE_PLANNING = "re_planning"
```

## 6. Re-planning Strategy

```
1. Detect failure (timeout, error, low confidence)
2. PlanningEngine.replan(current_plan, failed_step_id, reason)
3. Strategies:
   a. RETRY: Retry same sub-task (with backoff)
   b. ALTERNATE: Use different agent/tool for this sub-task
   c. SKIP: Skip sub-task (if optional)
   d. DECOMPOSE: Break failed sub-task into smaller steps
   e. ESCALATE: Flag for human intervention
4. Return updated Plan with modified DAG
5. WorkflowEngine continues from the modified point
```

## 7. Integration

```
AgentCoordinator
  │
  ├── uses WorkflowEngine for execution
  │     │
  │     └── WorkflowEngine steps (agent calls, tool calls)
  │
  └── uses PlanningEngine for dynamic decomposition
        │
        └── PlanningEngine.create_plan(goal)
              │
              └── returns Plan → converted to WorkflowDef
```
