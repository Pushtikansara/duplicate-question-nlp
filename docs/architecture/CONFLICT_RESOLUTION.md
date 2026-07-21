# Conflict Resolution -- Detection and Impact

## Overview

The conflict resolution subsystem analyzes agent outputs to identify disagreements, anomalies, and warning conditions. These conflicts inform the consensus engine, which applies severity-based penalties to adjust confidence and potentially override decisions.

## ConflictDetectionStrategy Interface

```python
class ConflictDetectionStrategy(ABC):
    @abstractmethod
    def detect(
        self,
        results: list[AgentResult],
        votes: list[Vote],
    ) -> list[ConflictReport]:
        ...
```

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `results` | `list[AgentResult]` | All agent evaluation results (8 agents) |
| `votes` | `list[Vote]` | Vote objects from vote building (7 votes) |

### Output

Returns `list[ConflictReport]`:

```python
@dataclass
class ConflictReport:
    conflict_type: str
    agents: list[str]
    description: str
    severity: float    # 0.0 to 1.0
```

## DefaultConflictDetector

The default detector analyzes six distinct conflict types. Detection is applied in a fixed order, and all detected conflicts are returned.

### Conflict Type 1: agent_disagreement

**Purpose**: Identifies agents whose recommendations differ from the majority.

**Algorithm**:
```
1. Count recommendations across all votes
2. Find majority recommendation (most common)
3. Identify agents whose recommendation differs from majority
4. IF minority agents exist:
   severity = len(minority) / len(votes)
```

**Severity**: Proportion of agents in the minority. A single dissenting agent gets 0.14 (1/7), while 3 dissenting agents get 0.43.

**Example**: 5 agents say duplicate, 2 say not_duplicate. The 2 not_duplicate agents are flagged with severity 0.286.

### Conflict Type 2: low_confidence

**Purpose**: Flags agents whose confidence is below 0.4 threshold.

**Algorithm**:
```
1. Check each agent's confidence
2. IF confidence < 0.4:
   severity = 0.3 (fixed)
```

**Severity**: Fixed at 0.3 regardless of how low the confidence is. This reflects that low confidence is a notable but not critical issue.

**Example**: EvidenceAgent with confidence 0.3 is flagged with severity 0.3.

### Conflict Type 3: opposite_conclusion

**Purpose**: Detects pairs of agents that reached directly opposite conclusions (duplicate vs not_duplicate).

**Algorithm**:
```
1. Define opposite_map: {duplicate: not_duplicate, not_duplicate: duplicate}
2. For each pair of agents (i, j):
   IF vote_map[i] == opposite_map[vote_map[j]]:
     add pair to opposite_pairs
3. For each opposite pair:
   severity = 0.8 (fixed)
```

**Severity**: Fixed at 0.8, reflecting that opposite conclusions between agents represent a serious cognitive conflict.

**Example**: IntentAgent says duplicate, EntityAgent says not_duplicate -- flagged with severity 0.8.

### Conflict Type 4: missing_evidence

**Purpose**: Identifies agents that produced neither supporting nor contradicting evidence.

**Algorithm**:
```
1. For each agent result:
   IF no supporting_evidence AND no contradicting_evidence:
     severity = 0.4 (fixed)
```

**Severity**: Fixed at 0.4. Missing evidence is concerning but may be legitimate (e.g., ConsensusAgent always has empty evidence).

**Example**: RelationAgent with no entities -- if relations are empty in both representations, the agent produces only neutral evidence (not stored in supporting or contradicting lists).

### Conflict Type 5: contradictory_evidence

**Purpose**: Detects agents that produced both supporting and contradicting evidence, indicating internal inconsistency.

**Algorithm**:
```
1. For each agent result:
   IF has supporting AND has contradicting:
     ratio = len(contradicting) / max(1, len(supporting) + len(contradicting))
     severity = min(1.0, ratio)
```

**Severity**: Proportion of contradicting evidence relative to total evidence. An agent with 3 supporting and 2 contradicting gets severity 0.4.

**Example**: SemanticAgent with evidence both agreeing and disagreeing with the reasoning engine -- contradictory evidence flagged.

### Conflict Type 6: agent_warnings

**Purpose**: Propagates agent-level warnings as system-level conflicts.

**Algorithm**:
```
1. For each agent result:
   IF warnings count > 0:
     severity = min(0.5, warnings_count * 0.1)
```

**Severity**: Capped at 0.5, with each warning contributing 0.1 to severity. An agent with 3 warnings gets 0.3.

**Example**: ConflictAgent warns "Multiple conflicts detected: 4" and "Both hypotheses have supporting evidence" -- 2 warnings, severity 0.2.

## Complete Detection Flow

```
DefaultConflictDetector.detect(results, votes)
|
+-> Build vote_map (name -> recommendation)
|   Build confidence_map (name -> confidence)
|
+-> 1. agent_disagreement
|      Count recommendations, find minority
|      IF minority exists: add report
|
+-> 2. low_confidence
|      Check each confidence_map value < 0.4
|      IF below threshold: add report
|
+-> 3. opposite_conclusion
|      Scan all agent pairs for direct opposites
|      IF opposite pair found: add report
|
+-> 4. missing_evidence
|      Check each result for empty evidence lists
|      IF both lists empty: add report
|
+-> 5. contradictory_evidence
|      Check each result for mixed evidence types
|      IF both present: add report
|
+-> 6. agent_warnings
|      Check each result for non-empty warnings
|      IF warnings exist: add report
|
+-> Return list[ConflictReport]
```

## Severity Summary Table

| Conflict Type | Severity Calculation | Typical Range | Impact Level |
|--------------|---------------------|---------------|--------------|
| agent_disagreement | minority_count / total_votes | 0.14 - 0.86 | Moderate |
| low_confidence | 0.3 (fixed) | 0.3 | Low |
| opposite_conclusion | 0.8 (fixed) | 0.8 | High |
| missing_evidence | 0.4 (fixed) | 0.4 | Moderate |
| contradictory_evidence | contra / (sup + contra) | 0.0 - 1.0 | Variable |
| agent_warnings | min(0.5, count * 0.1) | 0.1 - 0.5 | Low-Moderate |

## Impact on Consensus

Conflict reports feed directly into the `DefaultConsensusStrategy`:

```python
# Mean conflict severity
severity_penalty = sum(c.severity for c in conflict_reports) / max(1, len(conflict_reports))

# Confidence adjustment
adjusted_confidence = vote_result.confidence * (1.0 - severity_penalty * 0.3)

# Override to uncertain
if severity_penalty > 0.7:
    decision = "uncertain"
```

The penalty coefficient (0.3) ensures that even with maximum mean severity (1.0), the confidence multiplier is 0.7. The override threshold (0.7) ensures only severe widespread conflicts force an uncertain outcome.

## Example Conflict Analysis

Input: 7 voting agents

| Agent | Recommendation | Confidence | Warnings | Evidence Mix |
|-------|---------------|-----------|----------|-------------|
| IntentAgent | duplicate | 0.85 | 0 | support only |
| SemanticAgent | duplicate | 0.75 | 1 | support + contra |
| EntityAgent | not_duplicate | 0.60 | 0 | contra only |
| RelationAgent | uncertain | 0.50 | 1 | neutral only |
| ConflictAgent | duplicate | 0.80 | 0 | support only |
| ConfidenceAgent | uncertain | 0.35 | 2 | support + contra |
| EvidenceAgent | duplicate | 0.70 | 0 | support only |

Detected conflicts:

1. **agent_disagreement**: Minority = EntityAgent (not_duplicate), severity = 1/7 = 0.143
2. **agent_disagreement**: Minority = RelationAgent, ConfidenceAgent (uncertain), severity = 2/7 = 0.286
3. **low_confidence**: ConfidenceAgent (0.35 < 0.4), severity = 0.3
4. **opposite_conclusion**: IntentAgent (duplicate) vs EntityAgent (not_duplicate), severity = 0.8
5. **missing_evidence**: RelationAgent (no support/contra evidence), severity = 0.4
6. **contradictory_evidence**: SemanticAgent and ConfidenceAgent have mixed evidence, severity = variable
7. **agent_warnings**: SemanticAgent (1), RelationAgent (1), ConfidenceAgent (2), severity = variable

Mean severity: impacts consensus confidence according to `adjusted_confidence = vote_confidence * (1.0 - mean_severity * 0.3)`.

## Custom Conflict Detection

```python
from duplicate_question_app._agents.interfaces import ConflictDetectionStrategy
from duplicate_question_app._agents.agent_result import (
    AgentResult, Vote, ConflictReport,
)

class CustomConflictDetector(ConflictDetectionStrategy):
    def detect(
        self,
        results: list[AgentResult],
        votes: list[Vote],
    ) -> list[ConflictReport]:
        reports = []
        # Custom detection logic
        # ...
        return reports

# Usage
engine = DebateEngine(
    conflict_detector=CustomConflictDetector()
)
```

## Design Rationale

The six conflict types were chosen to cover distinct failure modes:

- **agent_disagreement**: Captures social disagreement dynamics
- **low_confidence**: Identifies agents operating outside their competence
- **opposite_conclusion**: Flags fundamental cognitive contradictions
- **missing_evidence**: Detects evaluation failures
- **contradictory_evidence**: Identifies self-inconsistency
- **agent_warnings**: Propagates operational signals to the system level

This comprehensive coverage ensures that consensus decisions account for both quantitative (vote counts) and qualitative (conflict severity) factors.
