# Voting Strategies -- Aggregation and Decision

## Overview

Voting strategies determine how individual agent recommendations are aggregated into a collective decision. MADE provides three strategies, each offering a different trade-off between simplicity, expressiveness, and sensitivity to confidence signals.

## VotingStrategy Interface

```python
class VotingStrategy(ABC):
    @abstractmethod
    def compute(self, votes: list[Vote]) -> ConsensusResult:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
```

### Vote Dataclass

```python
@dataclass
class Vote:
    agent_name: str
    recommendation: str       # "duplicate", "not_duplicate", "uncertain"
    confidence: float          # [0.0, 1.0] from AgentResult
    weight: float = 1.0        # agent base weight (default 1.0)
```

Votes are extracted from `AgentResult` objects by `DebateEngine._build_votes()`. The `consensus_agent` is excluded. Each vote carries the agent's confidence and weight for strategies that use them.

## Strategy 1: MajorityVoting

### Algorithm

```python
counts = Counter()
for v in votes:
    counts[v.recommendation] += 1

if no votes:
    return uncertain, 0.0

total = sum(counts.values())
decision = counts.most_common(1)[0][0]
top_count = counts.most_common(1)[0][1]
confidence = top_count / total

# Tie detection
if len(counts) >= 2 and top_count == second_count:
    decision = uncertain
    confidence = 0.0
```

### Properties

- Each agent gets exactly one vote
- Only vote counts matter; confidence and weight are ignored
- Ties resolve to uncertain with zero confidence
- Vote counts are normalized to produce weighted_vote fractions

### Example

| Agent | Recommendation | Confidence | Weight |
|-------|---------------|-----------|--------|
| IntentAgent | duplicate | 0.9 | 1.0 |
| SemanticAgent | duplicate | 0.8 | 1.0 |
| EntityAgent | not_duplicate | 0.7 | 1.0 |
| RelationAgent | not_duplicate | 0.6 | 1.0 |
| ConflictAgent | duplicate | 0.8 | 1.0 |
| ConfidenceAgent | uncertain | 0.5 | 1.0 |
| EvidenceAgent | duplicate | 0.7 | 1.0 |

Result: `duplicate` (3 votes), `confidence = 3/7 = 0.429`

### Tie Example

| Agent | Recommendation |
|-------|---------------|
| IntentAgent | duplicate |
| SemanticAgent | duplicate |
| EntityAgent | not_duplicate |
| RelationAgent | not_duplicate |
| ConflictAgent | uncertain |
| ConfidenceAgent | uncertain |
| EvidenceAgent | uncertain |

Result: `uncertain` (3-way tie with 2 each, but 2=2 tie between top two), `confidence = 0.0`

## Strategy 2: WeightedVoting

### Algorithm

```python
weighted = {}
total_weight = 0.0
for v in votes:
    w = v.weight * v.confidence
    weighted[v.recommendation] += w
    total_weight += w

decision = argmax(weighted)
confidence = weighted[decision] / total_weight

# Tie detection (within 0.01)
sorted_weights = sorted(weighted.items(), key=by_value, reverse=True)
if abs(top_weight - second_weight) < 0.01:
    decision = uncertain
    confidence = 0.0
```

### Properties

- Each vote's power is `weight * confidence`
- Agent weights (default 1.0) can be customized per agent
- Higher confidence agents have proportionally more influence
- Near-ties within 0.01 threshold resolve to uncertain
- Weighted vote results are normalized to fractions

### Example

| Agent | Recommendation | Confidence | Weight | Weighted Power |
|-------|---------------|-----------|--------|---------------|
| IntentAgent | duplicate | 0.9 | 1.0 | 0.9 |
| SemanticAgent | duplicate | 0.8 | 1.0 | 0.8 |
| EntityAgent | not_duplicate | 0.7 | 1.0 | 0.7 |
| RelationAgent | not_duplicate | 0.6 | 1.0 | 0.6 |
| ConflictAgent | duplicate | 0.8 | 1.0 | 0.8 |
| ConfidenceAgent | uncertain | 0.5 | 1.0 | 0.5 |
| EvidenceAgent | duplicate | 0.7 | 1.0 | 0.7 |

Weighted sums: duplicate=3.2, not_duplicate=1.3, uncertain=0.5
Result: `duplicate`, confidence = 3.2 / 5.0 = 0.640

### Custom Weight Example

```python
from duplicate_question_app._agents.voting import WeightedVoting

# All agents get weight=2.0
strategy = WeightedVoting(default_weight=2.0)
```

## Strategy 3: ConfidenceWeightedVoting

### Algorithm

```python
weighted = {}
total_confidence = 0.0
for v in votes:
    weighted[v.recommendation] += v.confidence
    total_confidence += v.confidence

decision = argmax(weighted)
confidence = weighted[decision] / total_confidence

# Tie detection (within 0.01)
sorted_weights = sorted(weighted.items(), key=by_value, reverse=True)
if abs(top_confidence - second_confidence) < 0.01:
    decision = uncertain
    confidence = 0.0
```

### Properties

- Confidence is the sole weight; agent base weight is ignored
- Agents with higher confidence dominate proportionally
- Same tie detection as WeightedVoting (0.01 threshold)
- Simpler than WeightedVoting when per-agent weights are not needed

### Example

| Agent | Recommendation | Confidence |
|-------|---------------|-----------|
| IntentAgent | duplicate | 0.9 |
| SemanticAgent | duplicate | 0.8 |
| EntityAgent | not_duplicate | 0.7 |
| RelationAgent | not_duplicate | 0.6 |
| ConflictAgent | duplicate | 0.8 |
| ConfidenceAgent | uncertain | 0.5 |
| EvidenceAgent | duplicate | 0.7 |

Confidence sums: duplicate=3.2, not_duplicate=1.3, uncertain=0.5
Result: `duplicate`, confidence = 3.2 / 5.0 = 0.640

## Comparison Table

| Property | MajorityVoting | WeightedVoting | ConfidenceWeightedVoting |
|----------|---------------|---------------|------------------------|
| Uses confidence | No | Yes | Yes |
| Uses agent weight | No | Yes | No |
| Tie threshold | exact equality | abs diff < 0.01 | abs diff < 0.01 |
| Sensitivity to outliers | Low | High | High |
| Interpretability | Highest | Medium | Medium |
| Default for | Simplicity | Custom weighting | Confidence-only |

## When to Use Each Strategy

### MajorityVoting
- All agents are considered equally authoritative
- Simplicity and interpretability are priorities
- Confidence values are unreliable or not comparable across agents
- Use as default for most debate configurations

### WeightedVoting
- Some agents should have more influence (e.g., SemanticAgent weighted higher than ConfidenceAgent)
- Calibrated per-agent weights are available from prior validation
- The interaction between confidence and authority needs to be jointly modeled

### ConfidenceWeightedVoting
- Agent confidence is the best available signal of decision quality
- No additional per-agent weight calibration is available
- Simpler alternative to WeightedVoting when all agents should be equally important but confidence tracks reliability

## Extension: Custom Voting Strategy

```python
from duplicate_question_app._agents.interfaces import VotingStrategy
from duplicate_question_app._agents.agent_result import Vote, ConsensusResult

class RankedVoting(VotingStrategy):
    @property
    def name(self) -> str:
        return "ranked"

    def compute(self, votes: list[Vote]) -> ConsensusResult:
        if not votes:
            return ConsensusResult(
                decision="uncertain",
                confidence=0.0,
                strategy_used=self.name,
                details="No votes",
            )
        # Custom ranked voting logic
        # ...
        return ConsensusResult(
            decision="duplicate",
            confidence=0.8,
            strategy_used=self.name,
            details="Ranked voting result",
        )
```

Register via injection into `DefaultConsensusStrategy`:

```python
strategy = DefaultConsensusStrategy(voting_strategy=RankedVoting())
```
