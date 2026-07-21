# Consensus Engine -- Decision Synthesis

## Overview

The consensus engine synthesizes the outputs of all eight cognitive agents into a single final decision. It integrates voting results with conflict analysis to produce a calibrated confidence score. The `DefaultConsensusStrategy` provides the reference implementation, combining a configurable `VotingStrategy` with conflict severity penalties.

## ConsensusStrategy Interface

```python
class ConsensusStrategy(ABC):
    @abstractmethod
    def build(
        self,
        results: list[AgentResult],
        votes: list[Vote],
        conflict_reports: list[ConflictReport],
    ) -> ConsensusResult:
        ...
```

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `results` | `list[AgentResult]` | All agent evaluation results (8 agents) |
| `votes` | `list[Vote]` | Vote objects (7 votes, excluding consensus_agent) |
| `conflict_reports` | `list[ConflictReport]` | Detected conflicts from ConflictDetectionStrategy |

### Output

Returns `ConsensusResult`:

| Field | Type | Description |
|-------|------|-------------|
| `decision` | `str` | Final decision: `"duplicate"`, `"not_duplicate"`, `"uncertain"` |
| `confidence` | `float` | Calibrated confidence in [0.0, 1.0] |
| `vote_counts` | `dict[str, int]` | Raw counts per recommendation |
| `weighted_vote` | `dict[str, float]` | Weighted distribution per recommendation |
| `strategy_used` | `str` | Name of the voting strategy employed |
| `details` | `str` | Human-readable explanation of decision factors |

## DefaultConsensusStrategy

### Algorithm

```
INPUT: results, votes, conflict_reports

1. IF no results:
   RETURN uncertain, 0.0, "No agent results"

2. COMPUTE base vote result:
   vote_result = self._voting.compute(votes)
   // vote_result.decision, vote_result.confidence

3. COMPUTE conflict severity penalty:
   total_severity = SUM(c.severity for c in conflict_reports)
   severity_penalty = total_severity / MAX(1, len(conflict_reports))

4. ADJUST confidence:
   adjusted_confidence = vote_result.confidence
                          * (1.0 - severity_penalty * 0.3)
   adjusted_confidence = CLAMP(adjusted_confidence, 0.0, 1.0)

5. OVERRIDE if high conflict:
   IF severity_penalty > 0.7:
     RETURN uncertain, adjusted_confidence
            (overridden due to high conflict severity)

6. RETURN:
   decision = vote_result.decision
   confidence = adjusted_confidence
   details includes base strategy output + conflict penalty info
```

### Confidence Calculation

The final confidence is a product of vote confidence and conflict penalty:

```
final_confidence = vote_confidence * (1.0 - mean_severity * 0.3)
```

The conflict penalty coefficient (0.3) dampens the impact of conflicts: even at maximum mean severity (1.0), the confidence multiplier is `1.0 - 0.3 = 0.7`. This prevents a single conflict type from completely suppressing consensus confidence.

### Conflict Override

When mean conflict severity exceeds 0.7, the decision is overridden to `"uncertain"` regardless of vote outcome. This prevents high-confidence decisions when the system detects severe internal disagreement.

## Vote Counting Mechanics

The consensus strategy delegates voting to a configurable `VotingStrategy`. Three implementations are available:

### MajorityVoting

```
counts = Counter(recommendation for each vote)
total = sum(counts.values())
decision = most_common(counts)
confidence = top_count / total

IF tie (top two counts equal):
  decision = uncertain
  confidence = 0.0
```

Majority voting counts agents equally regardless of confidence or weight.

### WeightedVoting

```
weighted = {}
for each vote:
  w = vote.weight * vote.confidence
  weighted[vote.recommendation] += w

decision = argmax(weighted)
total_weight = sum(weighted.values())
confidence = weighted[decision] / total_weight

IF top two weights differ by < 0.01:
  decision = uncertain, confidence = 0.0
```

Weighted voting uses each agent's `weight` property (default 1.0) multiplied by confidence as the voting power.

### ConfidenceWeightedVoting

```
weighted = {}
for each vote:
  weighted[vote.recommendation] += vote.confidence

decision = argmax(weighted)
total_confidence = sum(weighted.values())
confidence = weighted[decision] / total_confidence

IF top two weights differ by < 0.01:
  decision = uncertain, confidence = 0.0
```

Confidence-weighted voting uses confidence directly as the voting weight, ignoring the agent's base weight.

## Tie Handling

All three voting strategies handle ties by returning `decision = "uncertain"` with `confidence = 0.0`. The tie detection criteria differ:

| Strategy | Tie Condition |
|----------|---------------|
| MajorityVoting | Top two recommendation counts are equal |
| WeightedVoting | Top two weighted scores differ by < 0.01 |
| ConfidenceWeightedVoting | Top two confidence sums differ by < 0.01 |

## Strategy Configuration

### Setting the Voting Strategy

```python
from duplicate_question_app._agents.consensus import DefaultConsensusStrategy
from duplicate_question_app._agents.voting import (
    MajorityVoting,
    WeightedVoting,
    ConfidenceWeightedVoting,
)

# Default: majority voting
strategy = DefaultConsensusStrategy()

# Explicit majority
strategy = DefaultConsensusStrategy(voting_strategy=MajorityVoting())

# Weighted
strategy = DefaultConsensusStrategy(voting_strategy=WeightedVoting())

# Confidence-weighted
strategy = DefaultConsensusStrategy(
    voting_strategy=ConfidenceWeightedVoting()
)
```

### Injecting into DebateEngine

```python
from duplicate_question_app._agents.debate_engine import DebateEngine

engine = DebateEngine(
    consensus_strategy=DefaultConsensusStrategy(
        voting_strategy=ConfidenceWeightedVoting()
    )
)

# Or change at runtime:
engine.set_consensus_strategy(new_strategy)
```

## Decision Flow

```
                    +-----------+
                    | Agent     |
                    | Results   |
                    +-----------+
                         |
                         v
                    +-----------+
                    | Vote      |
                    | Building  |
                    +-----------+
                    (excl consensus_agent)
                         |
                         v
                    +-------------------+
                    | VotingStrategy    |
                    | compute(votes)    |
                    +-------------------+
                         |
                         v
                    +-----------------------+
                    | ConsensusResult       |
                    | (decision, confidence)|
                    +-----------------------+
                         |
                         v
                    +-------------------+
                    | Conflict Reports  |
                    +-------------------+
                         |
                         v
                    +-------------------+
                    | Severity Penalty   |
                    | Calculation        |
                    +-------------------+
                         |
                         v
                    +-------------------+
                    | Confidence        |
                    | Adjustment        |
                    +-------------------+
                         |
                         v
                    +-------------------+
                    | Override Check    |
                    | severity > 0.7?   |
                    +-------------------+
                      /        \
                   yes          no
                     |            |
                     v            v
              +-----------+  +-----------+
              | uncertain |  | base      |
              | + adj.    |  | decision  |
              | conf.     |  | + adj.    |
              |           |  | conf.     |
              +-----------+  +-----------+
```

## Edge Cases

- **Empty results**: Returns `uncertain` with `confidence=0.0`
- **No conflicts**: No penalty applied; raw vote confidence used
- **All agents agree**: High vote confidence (~1.0); minimal penalty from any leftover conflicts
- **Severe conflicts**: Override to `uncertain` when mean severity > 0.7
- **Tied votes**: Returns `uncertain` with `confidence=0.0`, preserving vote_counts for transparency

## Extension: Custom Consensus Strategy

```python
from duplicate_question_app._agents.interfaces import ConsensusStrategy
from duplicate_question_app._agents.agent_result import (
    AgentResult, Vote, ConflictReport, ConsensusResult,
)

class MyConsensusStrategy(ConsensusStrategy):
    def build(
        self,
        results: list[AgentResult],
        votes: list[Vote],
        conflict_reports: list[ConflictReport],
    ) -> ConsensusResult:
        # Custom logic here
        return ConsensusResult(
            decision="duplicate",
            confidence=0.85,
            strategy_used="my_custom",
            details="Custom consensus logic",
        )
```
