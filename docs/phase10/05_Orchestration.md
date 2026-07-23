# Phase 10 — Multi-Agent Orchestration

## 1. AgentCoordinator

The `AgentCoordinator` is the central orchestrator that manages multi-agent runs. It replaces and generalizes the existing `DebateEngine`.

```python
class AgentCoordinator:
    def __init__(
        self,
        registry: AgentRegistry,
        event_bus: EventBus,
        tool_registry: ToolRegistry,
    )

    async def run(
        self,
        workflow: WorkflowDef,
        input: AgentInput,
        policies: RunPolicies | None = None,
    ) -> OrchestrationResult:

    async def run_agents(
        self,
        agent_ids: list[str],
        input: AgentInput,
        strategy: OrchestrationStrategy,
    ) -> OrchestrationResult:
```

## 2. Orchestration Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `Sequential` | Agents run one after another; output of N is input to N+1 | Pipeline processing |
| `Parallel` | All agents run concurrently; results merged | Independent analysis |
| `Debate` | Agents evaluate independently, then vote/consensus (existing `DebateEngine` pattern) | Cognitive debate |
| `Race` | Multiple agents compete; fastest valid result wins | Low-latency fallback |
| `Ensemble` | All agents run; results averaged/weighted | Confidence aggregation |
| `Chain` | Agents execute in a directed chain with conditional branching | Workflow DAG |
| `Supervisor` | One agent (supervisor) delegates sub-tasks to worker agents | Hierarchical planning |

## 3. Consensus and Voting (Extended from Phase 9.5)

The existing `DebateEngine._build_votes()` and consensus mechanisms are preserved and generalized:

```python
class OrchestrationResult:
    agent_results: list[AgentOutput]
    votes: list[Vote]                     # preserved from Phase 9.5
    agreement_matrix: AgreementMatrix     # preserved from Phase 9.5
    conflict_reports: list[ConflictReport]
    consensus: ConsensusResult | None
    summary: str
    processing_time_ms: float
    stages: dict[str, float]
```

## 4. Concurrent Execution Model

```
┌──────────────────────────────────────────────────────┐
│                 AgentCoordinator                      │
│                                                      │
│  ┌─────────────┐     ┌──────────────────────────┐   │
│  │ Workflow    │────▶│ AgentScheduler            │   │
│  │ Engine      │     │  ┌────────────────────┐  │   │
│  └─────────────┘     │  │ asyncio TaskGroup   │  │   │
│                      │  │  ├─ Agent A (task)  │  │   │
│                      │  │  ├─ Agent B (task)  │  │   │
│                      │  │  └─ Agent C (task)  │  │   │
│                      │  └────────────────────┘  │   │
│                      └──────────────────────────┘   │
│                                                      │
│  ┌─────────────┐     ┌──────────────────────────┐   │
│  │ Result      │◀────│ Consensus / Merge         │   │
│  │ Aggregator  │     │ (strategy-dependent)      │   │
│  └─────────────┘     └──────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## 5. Integration with Existing DebateEngine

The existing `DebateEngine` becomes one strategy within the `AgentCoordinator`:

```python
class DebateOrchestrator(OrchestrationStrategy):
    """Wraps DebateEngine as an orchestration strategy."""

    def __init__(self):
        self._inner = DebateEngine()   # ← existing, unmodified

    async def execute(
        self,
        agents: list[Agent],
        input: AgentInput,
    ) -> OrchestrationResult:
        # Convert AgentInput → SemanticRepresentation, etc.
        # Call self._inner.debate(rep_a, rep_b, assessment, reasoning)
        # Convert DebateResult → OrchestrationResult
```

## 6. Scheduling Policies

```python
@dataclass
class RunPolicies:
    timeout_seconds: float = 60.0
    max_concurrency: int = 10
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_backoff_base: float = 1.0       # exponential backoff
    partial_results_on_timeout: bool = True
    stop_on_first_error: bool = False     # fail-fast vs. continue
```
