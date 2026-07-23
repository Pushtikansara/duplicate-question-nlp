# Phase 10 — Reflection Architecture

## 1. Design Principle

The existing `ReflectionEngine` (15+ files) provides trust scoring, confidence auditing, and consistency checking. Phase 10 adds **agent-level reflection** — agents introspect their own outputs and those of peer agents.

## 2. Reflection Levels

```
Level 0: No reflection (raw agent output)
Level 1: Self-reflection (agent evaluates its own confidence)
Level 2: Peer reflection (agent reviews peer agents' outputs)
Level 3: Meta-reflection (orchestrator reflects on the whole debate)
```

All levels reuse the existing `ReflectionEngine` under the hood.

## 3. Self-Reflection Protocol

Every `Agent` gets a `reflect()` method:

```python
class Agent(ABC):
    async def reflect(self, output: AgentOutput) -> ReflectionResult:
        """Self-reflection: evaluate own output's trustworthiness."""
        # Default: return existing ReflectionEngine.evaluate(output)
        return await default_reflect(output)
```

Built-in overrides for cognitive agents:

```python
class CognitiveAgent(Agent):
    async def reflect(self, output: AgentOutput) -> ReflectionResult:
        # Use existing ReflectionEngine with domain-specific auditors
        return reflection_engine.analyze(
            output=output,
            auditors=[
                ConfidenceAuditor(),
                ConsistencyChecker(),
                EvidenceAnalyzer(),
            ],
        )
```

## 4. Reflection Result Schema

```python
@dataclass
class AgentReflectionResult:
    agent_id: str
    trust_score: float              # 0.0 - 1.0
    trust_level: str                # "high" | "medium" | "low"
    risk_level: str                 # "low" | "medium" | "high"
    confidence_audit: dict | None
    consistency_check: dict | None
    evidence_quality: dict | None
    recommendations: list[str]
    human_review_required: bool
    processing_time_ms: float
```

## 5. Integration with Orchestrator

```python
class AgentCoordinator:
    async def _reflect_on_results(
        self,
        results: list[AgentOutput],
    ) -> list[AgentReflectionResult]:
        """Run reflection on every agent result (Level 2)."""
        reflections = []
        for result in results:
            agent = self.registry.get(result.agent_id)
            reflection = await agent.reflect(result)
            reflections.append(reflection)
            self.event_bus.emit(AgentEvent.REFLECTED, reflection)
        return reflections
```

## 6. Threshold-Based Actions

| Condition | Action |
|-----------|--------|
| `trust_score < 0.3` | Flag for human review; add to `human_review_required` queue |
| `trust_score < 0.5` | Re-run with different agent set (fallback strategy) |
| `risk_level == "high"` | Engage `ConflictAgent` for deeper analysis |
| `consistency_check.failed` | Reject output; request re-execution |

## 7. Reuse of Existing Components

| Existing Component | Phase 10 Role |
|--------------------|---------------|
| `ReflectionEngine` | Core reflection engine — called by `Agent.reflect()` |
| `ConfidenceAuditor` | Evaluates confidence alignment in agent outputs |
| `ConsistencyChecker` | Checks consistency across multiple agent outputs |
| `EvidenceAnalyzer` | Analyzes evidence quality in agent results |
| `TrustEngine` | Computes final trust score from multiple auditors |
| `MemoryAuditor` | Tracks reflection results as memory entries |
