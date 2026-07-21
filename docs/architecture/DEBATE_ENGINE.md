# DebateEngine -- Orchestration and Pipeline

## Overview

`DebateEngine` is the central orchestrator of the MADE system. It manages the full debate lifecycle from agent loading through consensus generation. All inter-component communication flows through the engine, which tracks per-stage timing, handles failures, and assembles the final `DebateResult`.

## Orchestration Flow

```
DebateEngine.debate(rep_a, rep_b, assessment, reasoning_result)
|
|  STAGE 1: Agent Loading
|  +-----------------------------------------------+
|  | engine._registry.get_all()                    |
|  | Returns list[CognitiveAgent] from registry    |
|  | If empty: return early with error summary     |
|  +-----------------------------------------------+
|  Timing: stages["agent_loading"]
|
|  STAGE 2: Agent Evaluation
|  +-----------------------------------------------+
|  | for each agent in agents:                     |
|  |   try:                                        |
|  |     result = agent.evaluate(rep_a, rep_b,    |
|  |                              assessment,      |
|  |                              reasoning_result)|
|  |   except Exception:                           |
|  |     log error                                 |
|  |     create fallback AgentResult               |
|  |     (confidence=0.0, recommendation=uncert.)  |
|  |   append to agent_results list                |
|  +-----------------------------------------------+
|  Timing: stages["agent_evaluation"]
|
|  STAGE 3: Vote Building
|  +-----------------------------------------------+
|  | _build_votes(agent_results)                   |
|  | Excludes consensus_agent                      |
|  | Creates list[Vote] from AgentResult           |
|  +-----------------------------------------------+
|  Timing: stages["vote_building"]
|
|  STAGE 4: Plugin Processing
|  +-----------------------------------------------+
|  | engine._registry.get_plugins()                |
|  | for each plugin:                              |
|  |   try:                                        |
|  |     plugin.process(rep_a, rep_b,             |
|  |                     assessment,               |
|  |                     reasoning_result,         |
|  |                     agent_results)            |
|  |     append new results not already present    |
|  |   except Exception: log error                 |
|  +-----------------------------------------------+
|  Timing: stages["plugin_processing"]
|
|  STAGE 5: Agreement Matrix
|  +-----------------------------------------------+
|  | _build_agreement_matrix(agent_results, votes) |
|  | Pairwise recommendation comparison            |
|  | 1.0 if same recommendation, 0.0 otherwise    |
|  +-----------------------------------------------+
|  Timing: stages["agreement_matrix"]
|
|  STAGE 6: Conflict Detection
|  +-----------------------------------------------+
|  | engine._conflict_detector.detect(             |
|  |     agent_results, votes)                     |
|  | Returns list[ConflictReport]                  |
|  +-----------------------------------------------+
|  Timing: stages["conflict_detection"]
|
|  STAGE 7: Consensus
|  +-----------------------------------------------+
|  | engine._consensus.build(                      |
|  |     agent_results, votes, conflict_reports)   |
|  | Returns ConsensusResult                       |
|  +-----------------------------------------------+
|  Timing: stages["consensus"]
|
|  STAGE 8: Summary
|  +-----------------------------------------------+
|  | _build_summary(agent_results, votes,          |
|  |                conflict_reports, consensus)   |
|  | Returns formatted debate summary string       |
|  +-----------------------------------------------+
|  Timing: stages["summary"]
|
|  RETURN: DebateResult with all stages,           |
|          agent_results, votes, matrix,           |
|          conflict_reports, consensus, summary    |
|          total processing_time_ms, stages dict   |
+--------------------------------------------------+
```

## Timing and Stages

The engine records wall-clock time for each stage in milliseconds. The `DebateResult.stages` dictionary maps stage names to durations:

```python
{
    "agent_loading": 0.032,
    "agent_evaluation": 1.245,
    "vote_building": 0.018,
    "plugin_processing": 0.004,
    "agreement_matrix": 0.008,
    "conflict_detection": 0.065,
    "consensus": 0.009,
    "summary": 0.012,
}
```

Total time is recorded separately in `DebateResult.processing_time_ms`. Per-agent timing is available via each `AgentResult.processing_time_ms`.

## Stage Breakdown

### Agent Loading
Retrieves all registered agents from the `AgentRegistry`. If no agents are registered, the engine returns a `DebateResult` with `debate_summary = "No agents registered"` and zero-length result lists.

### Agent Evaluation
Sequentially evaluates each agent in registration order. Agent failures are caught and produce a fallback `AgentResult` with `confidence=0.0`, `recommendation="uncertain"`, and an error message in warnings. The failing agent's result is appended normally -- failures do not halt the debate.

### Vote Building
Converts `AgentResult` objects to `Vote` objects. The `consensus_agent` is excluded because its output is not a genuine evaluation. Each vote carries the agent name, recommendation, confidence, and weight (currently 1.0 for all agents; weights are reserved for future agent-specific weighting).

### Plugin Processing
Iterates through registered `AgentPlugin` instances. Plugins receive the full pipeline context plus all agent results and may return new `AgentResult` objects. New results are appended only if their agent name is not already present. Plugin failures are caught and logged -- they do not halt the debate.

### Agreement Matrix
Builds an N x N matrix where N is the number of agents (excluding consensus_agent). Cells contain 1.0 if two agents made the same recommendation, 0.0 otherwise. Diagonal values are 1.0. The matrix provides a mean agreement score across all agent pairs.

### Conflict Detection
Delegates to the configured `ConflictDetectionStrategy`. The default strategy (see CONFLICT_RESOLUTION.md) analyzes all agent results and votes for six conflict types.

### Consensus
Delegates to the configured `ConsensusStrategy`. The default strategy (see CONSENSUS_ENGINE.md) combines voting results with conflict severity penalties.

### Summary
Generates a human-readable debate summary string containing total agents, total conflicts, recommendation breakdown with average confidences, conflict details, and final consensus.

## Error Handling

### Agent Failures

```python
try:
    result = agent.evaluate(rep_a, rep_b, assessment, reasoning_result)
except Exception as exc:
    logger.error("Agent '%s' failed: %s", agent.name, exc)
    agent_results.append(AgentResult(
        agent_name=agent.name,
        confidence=0.0,
        recommendation="uncertain",
        warnings=[f"Agent evaluation failed: {exc}"],
        metadata={"error": str(exc)},
    ))
```

All agent exceptions are caught. A fallback result with zero confidence is inserted. The `error` key in metadata preserves the exception message for downstream analysis.

### Plugin Failures

```python
try:
    plugin_results = plugin.process(...)
except Exception as exc:
    logger.error("Plugin '%s' failed: %s", type(plugin).__name__, exc)
```

Plugin failures are caught and logged. The plugin's output is discarded, but the debate continues. No fallback results are generated.

### Empty Registry

```python
if not agents:
    return DebateResult(
        debate_summary="No agents registered",
        processing_time_ms=0.0,
    )
```

An early return prevents downstream processing when no agents are available.

## Pluggable Strategies

### Consensus Strategy
Set at construction or via `set_consensus_strategy()`:

```python
engine = DebateEngine(
    consensus_strategy=DefaultConsensusStrategy(
        voting_strategy=WeightedVoting()
    )
)

# Or later:
engine.set_consensus_strategy(my_custom_strategy)
```

### Conflict Detection Strategy
Set at construction or via `set_conflict_detector()`:

```python
engine = DebateEngine(
    conflict_detector=CustomConflictDetector()
)

# Or later:
engine.set_conflict_detector(my_custom_detector)
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `registry` | `AgentRegistry` | `None` (creates new) | Agent and plugin registry |
| `consensus_strategy` | `ConsensusStrategy` | `DefaultConsensusStrategy()` | Consensus builder |
| `conflict_detector` | `ConflictDetectionStrategy` | `DefaultConflictDetector()` | Conflict detection strategy |

## Sequence Diagram

```
DebateEngine          AgentRegistry      CognitiveAgent     Plugin
    |                     |                    |              |
    | get_all()           |                    |              |
    |-------------------->|                    |              |
    | list[CognitiveAgent]|                    |              |
    |<--------------------|                    |              |
    |                     |                    |              |
    | for each agent:     |                    |              |
    | evaluate(rep,rep,   |                    |              |
    |   assessment,rr)    |                    |              |
    |----------------------------------------->|              |
    | AgentResult          |                    |              |
    |<-----------------------------------------|              |
    |                     |                    |              |
    | _build_votes()      |                    |              |
    | (excl consensus)    |                    |              |
    |                     |                    |              |
    | get_plugins()       |                    |              |
    |-------------------->|                    |              |
    | list[AgentPlugin]   |                    |              |
    |<--------------------|                    |              |
    |                     |                    |              |
    | for each plugin:    |                    |              |
    | process(...,        |                    |              |
    |   agent_results)    |                    |              |
    |----------------------------------------->|              |
    | list[AgentResult]   |                    |              |
    |<-----------------------------------------|              |
    |                     |                    |              |
    | _build_agreement    |                    |              |
    |   _matrix()         |                    |              |
    |                     |                    |              |
    | conflict_detector.  |                    |              |
    |   detect(results,   |                    |              |
    |         votes)      |                    |              |
    |                     |                    |              |
    | consensus.build(    |                    |              |
    |   results,          |                    |              |
    |   votes,            |                    |              |
    |   conflict_reports) |                    |              |
    |                     |                    |              |
    | _build_summary()    |                    |              |
    |                     |                    |              |
    | RETURN DebateResult |                    |              |
    |<-------------------|                    |              |
```

## Extension Points

- **Custom Consensus Strategies**: Implement `ConsensusStrategy` ABC
- **Custom Conflict Detectors**: Implement `ConflictDetectionStrategy` ABC
- **Custom Plugins**: Implement `AgentPlugin` ABC for post-evaluation transformations
- **Custom Agent Weights**: Override `weight` property in agent implementations
