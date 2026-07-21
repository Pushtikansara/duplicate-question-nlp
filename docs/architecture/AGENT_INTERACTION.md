# Agent Interaction -- Dynamics and Information Flow

## Overview

MADE agents operate under a strict independence constraint: no agent communicates with any other agent during evaluation. All inter-agent dynamics are computed post-hoc through three mechanisms: the agreement matrix, conflict detection, and consensus synthesis. This document describes how individual agent evaluations combine into collective intelligence.

## Interaction Architecture

```
     Agent Evaluation Phase (agents are independent)
     ================================================

     IntentAgent      SemanticAgent     EntityAgent      RelationAgent
     +--------+       +--------+        +--------+        +--------+
     | assess |       | assess |        | assess |        | assess |
     | intent |       | sem.   |        | entity |        | rel.   |
     | simil. |       | simil. |        | overlap|        | struct |
     +--------+       +--------+        +--------+        +--------+
          |               |                 |                  |
     ConflictAgent   ConfidenceAgent   EvidenceAgent     ConsensusAgent
     +--------+       +--------+        +--------+        +--------+
     | detect |       | analyze|        | evalu. |        | (meta) |
     | confl. |       | conf.  |        | evid.  |        | no eval|
     +--------+       +--------+        +--------+        +--------+
          |               |                 |                  |
          +-------+-------+-------+--------+---------+--------+
                  |               |                  |
                  v               v                  v
          +-----------+    +-----------+     +-------------+
          |  Vote     |    | Agreement |     |  Conflict   |
          |  Building |    |  Matrix   |     |  Detection  |
          +-----------+    +-----------+     +-------------+
                  |               |                  |
                  +-------+-------+------------------+
                          |
                          v
                  +---------------+
                  |  Consensus   |
                  |  Synthesis   |
                  +---------------+
```

## Agreement Matrix

The agreement matrix captures pairwise recommendation alignment between all voting agents.

### Construction

```python
def _build_agreement_matrix(self, results, votes):
    matrix = {}
    vote_map = {v.agent_name: v.recommendation for v in votes}
    agents = [r.agent_name for r in results if r.agent_name in vote_map]

    for a in agents:
        matrix[a] = {}
        for b in agents:
            if a == b:
                matrix[a][b] = 1.0
            else:
                ra = vote_map.get(a, "uncertain")
                rb = vote_map.get(b, "uncertain")
                matrix[a][b] = 1.0 if ra == rb else 0.0

    return AgreementMatrix(matrix=matrix)
```

### Properties

- Diagonal elements are always 1.0 (an agent always agrees with itself)
- Off-diagonal elements are binary: 1.0 if same recommendation, 0.0 otherwise
- The matrix is symmetric: `M[a][b] == M[b][a]`
- Only agents with votes are included (consensus_agent excluded)
- `"uncertain"` is treated as a distinct recommendation -- two agents both predicting uncertain count as agreeing

### Interpretation

A matrix with all 1.0 values indicates unanimous agreement. High mean agreement (>0.7) suggests strong consensus. Low mean agreement (<0.4) indicates significant disagreement among agents.

### Example Matrix

7 voting agents, 4 say duplicate, 2 say not_duplicate, 1 says uncertain:

```
             Intent Semant Entity Relat Confl Confid Evid
Intent       1.0    1.0    0.0    0.0   1.0   0.0    1.0
Semantic     1.0    1.0    0.0    0.0   1.0   0.0    1.0
Entity       0.0    0.0    1.0    1.0   0.0   0.0    0.0
Relation     0.0    0.0    1.0    1.0   0.0   0.0    0.0
Conflict     1.0    1.0    0.0    0.0   1.0   0.0    1.0
Confidence   0.0    0.0    0.0    0.0   0.0   1.0    0.0
Evidence     1.0    1.0    0.0    0.0   1.0   0.0    1.0
```

Total ones (excluding diagonal): 6 + 6 + 0 + 0 + 6 + 0 + 6 = 24
Total cells (excluding diagonal): 42
Mean agreement: 24 / 42 = 0.571

## Mean Agreement Score

Calculated as:

```python
def mean_agreement(self) -> float:
    values = []
    for a, inner in self.matrix.items():
        for b, v in inner.items():
            if a != b:
                values.append(v)
    if not values:
        return 0.0
    return sum(values) / len(values)
```

The mean agreement score provides a single scalar measure of agent consensus quality. It ranges from 0.0 (complete disagreement) to 1.0 (unanimous agreement).

## Vote Collection

Vote collection is the process of extracting structured votes from agent results:

```python
def _build_votes(self, results):
    votes = []
    for r in results:
        if r.agent_name == "consensus_agent":
            continue
        weight = 1.0  # currently fixed; reserved for agent-specific weights
        votes.append(Vote(
            agent_name=r.agent_name,
            recommendation=r.recommendation,
            confidence=r.confidence,
            weight=weight,
        ))
    return votes
```

Key rules:
- The `consensus_agent` is always excluded from voting
- All other agents contribute exactly one vote each
- Weight is currently fixed at 1.0 (extensible via `CognitiveAgent.weight`)
- Votes carry the agent's confidence for weighted strategies

## Plugin Processing Pipeline

Plugins are post-evaluation processors that can modify or augment agent results:

```python
for plugin in plugins:
    try:
        plugin_results = plugin.process(
            rep_a, rep_b,
            assessment, reasoning_result,
            agent_results,
        )
        if plugin_results:
            existing_names = {r.agent_name for r in agent_results}
            for pr in plugin_results:
                if pr.agent_name not in existing_names:
                    agent_results.append(pr)
                    existing_names.add(pr.agent_name)
    except Exception as exc:
        logging.error("Plugin '%s' failed: %s", type(plugin).__name__, exc)
```

### Plugin Contract

- Receive full pipeline context (representations, assessment, reasoning result, all agent results)
- Return optionally modified list of `AgentResult`
- New results are appended only if their agent name is not already present
- Plugins cannot modify existing results; only append new ones
- Plugin failures are isolated; the debate continues

### Default Plugin

The `DefaultAgentPlugin` simply returns the agent results unchanged. Actual plugins would add new synthetic agents or transform results for downstream analysis.

## Agent Results to Conflict Detection

Conflict detection operates on the full set of agent results and votes:

```python
conflict_reports = self._conflict_detector.detect(agent_results, votes)
```

The detector analyzes:
1. **Recommendation distribution** via vote_map: identifies minority groups
2. **Confidence values** via confidence_map: flags low-confidence agents
3. **Pairwise conclusions**: finds opposite conclusions
4. **Evidence presence**: checks each agent's supporting/contradicting evidence lists
5. **Evidence contradictions**: detects agents with both supporting and contradicting evidence
6. **Warning propagation**: counts warnings per agent

See CONFLICT_RESOLUTION.md for detailed conflict detection algorithms.

## Agent Independence

Agents are designed to be pure functions. The `evaluate()` method:

- Receives only `rep_a`, `rep_b`, `assessment`, `reasoning_result`
- Has no access to other agents' results
- Has no access to registry, plugins, or engine state
- Returns deterministic output based solely on inputs
- Maintains no internal state between calls

This design ensures:

```
Given the same inputs, every agent always produces the same output.
No agent's output can be influenced by another agent's behavior.
Debate runs are perfectly reproducible.
```

## Interaction Patterns Summary

| Interaction Type | When | How |
|-----------------|------|-----|
| Independence | During evaluation | No inter-agent communication |
| Agreement measurement | After evaluation | Pairwise recommendation comparison |
| Conflict detection | After evaluation | Cross-agent recommendation + evidence analysis |
| Consensus synthesis | After evaluation | Vote aggregation + conflict penalty |
| Plugin transformation | After evaluation | Optional post-processing pipeline |
