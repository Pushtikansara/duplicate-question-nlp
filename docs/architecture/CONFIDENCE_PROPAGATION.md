# Confidence Propagation -- Computation and Aggregation

## Overview

Confidence flows through the MADE system along a well-defined path: from upstream CRE through individual agents, through voting, and finally through consensus synthesis. Each stage transforms and calibrates confidence, with the final consensus confidence reflecting both agreement levels and conflict severity.

## Confidence Chain

```
    CRE (upstream)
    ReasoningResult.confidence
    ReasoningResult.confidence_chain
           |
           v
    Agent Layer (8 agents)
    Each agent computes AgentResult.confidence
    Based on inputs + agent-specific logic
           |
           v
    Vote Building
    Vote.confidence = AgentResult.confidence
    Vote.weight = agent.weight (default 1.0)
           |
           v
    VotingStrategy.compute()
    confidence = f(vote confidences, vote weights)
           |
           v
    ConsensusStrategy.build()
    adjusted_confidence = vote_confidence * conflict_penalty
           |
           v
    ConsensusResult.confidence
```

## Per-Agent Confidence Computation

Each agent computes confidence independently based on its evaluation logic. Confidences are clamped to [0.0, 1.0].

### IntentAgent

| Condition | Confidence Formula | Range |
|-----------|-------------------|-------|
| No intent data | 0.5 | fixed |
| Missing one intent | 0.4 | fixed |
| Similarity > 0.7 | score * similarity_confidence | 0.0 - 1.0 |
| Similarity < 0.3 | 0.3 | fixed |
| Exact match | 0.8 | fixed |
| Fallback | 0.4 | fixed |

### SemanticAgent

| Condition | Confidence Formula | Range |
|-----------|-------------------|-------|
| No assessment | 0.5 | fixed |
| duplicate | combined_sem = sim*0.6 + overlap*0.4 | 0.0 - 1.0 |
| not_duplicate | 1.0 - combined_sem | 0.0 - 1.0 |
| uncertain | 0.5 | fixed |

### EntityAgent

| Condition | Confidence Formula | Range |
|-----------|-------------------|-------|
| No entities | 0.5 | fixed |
| duplicate | shared / (shared + only_a + only_b) | 0.0 - 1.0 |
| not_duplicate | (only_a + only_b) / total_unique | 0.0 - 1.0 |
| Fallback | 0.5 | fixed |

### RelationAgent

| Condition | Confidence Formula | Range |
|-----------|-------------------|-------|
| No relations | 0.5 | fixed |
| duplicate | relation_similarity_score | 0.0 - 1.0 |
| not_duplicate | 1.0 - relation_similarity_score | 0.0 - 1.0 |
| uncertain | 0.5 | fixed |

### ConflictAgent

| Condition | Confidence Formula | Range |
|-----------|-------------------|-------|
| 0 conflicts | 0.8 | fixed |
| 1-2 conflicts | 0.5 | fixed |
| 3+ conflicts | max(0.1, 1.0 - count * 0.2) | 0.1 - 0.9 |

### ConfidenceAgent

| Condition | Confidence Formula | Range |
|-----------|-------------------|-------|
| No reasoning result | 0.5 | fixed |
| Overconfidence | 0.3 | fixed |
| Underconfidence | 0.5 | fixed |
| decision_conf > 0.7 | decision_confidence | 0.7 - 1.0 |
| decision_conf < 0.3 | 1.0 - decision_confidence | 0.7 - 1.0 |
| Else | decision_confidence | 0.3 - 0.7 |

### EvidenceAgent

| Condition | Confidence Formula | Range |
|-----------|-------------------|-------|
| No reasoning result | 0.5 | fixed |
| duplicate | supporting / (supporting + contradicting) | 0.0 - 1.0 |
| not_duplicate | contradicting / (supporting + contradicting) | 0.0 - 1.0 |
| uncertain | 0.5 | fixed |

### ConsensusAgent

Always returns confidence = 1.0. The consensus agent does not evaluate; its confidence is a sentinel value.

## Vote Confidence

Vote confidence is directly copied from `AgentResult.confidence`:

```python
Vote(
    agent_name=r.agent_name,
    recommendation=r.recommendation,
    confidence=r.confidence,   # <-- direct copy
    weight=r.weight,
)
```

## ConfidenceAggregationStrategy

MADE provides four strategies for aggregating a set of confidence values (typically used outside the core debate flow for downstream analysis).

### Interface

```python
class ConfidenceAggregationStrategy(ABC):
    @abstractmethod
    def aggregate(
        self,
        confidences: list[float],
        weights: list[float] | None = None,
    ) -> float:
        ...
```

### Strategies

#### MeanAggregation

```python
# Unweighted:
result = mean(confidences)

# Weighted:
result = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)
# Falls back to unweighted mean if all weights are zero
```

| Input | Result |
|-------|--------|
| [0.8, 0.6, 0.4] | 0.6 |
| [0.8, 0.6] with weights [2, 1] | (0.8*2 + 0.6*1) / 3 = 0.733 |

#### MinAggregation

```python
result = min(confidences)
# Weights are ignored
```

| Input | Result |
|-------|--------|
| [0.8, 0.4, 0.9] | 0.4 |

#### MaxAggregation

```python
result = max(confidences)
# Weights are ignored
```

| Input | Result |
|-------|--------|
| [0.3, 0.9, 0.5] | 0.9 |

#### ProductAggregation

```python
result = product(confidences)
# Weights are ignored
```

| Input | Result |
|-------|--------|
| [0.8, 0.5, 0.6] | 0.24 |
| [0.8, 0.0, 0.6] | 0.0 |

### Comparison

| Strategy | Range | Sensitivity | Use Case |
|----------|-------|-------------|----------|
| Mean | [0, 1] | All values contribute | General purpose |
| Min | [0, 1] | Only lowest matters | Conservative estimates |
| Max | [0, 1] | Only highest matters | Optimistic estimates |
| Product | [0, 1] | Single zero zeros all | Strict conjunction |

## Consensus Confidence

The final consensus confidence is computed in `DefaultConsensusStrategy.build()`:

```python
# Step 1: Get vote result from VotingStrategy
vote_result = self._voting.compute(votes)

# Step 2: Compute conflict severity penalty
severity_penalty = sum(c.severity for c in conflict_reports) / max(1, len(conflict_reports))

# Step 3: Adjust confidence
adjusted_confidence = vote_result.confidence * (1.0 - severity_penalty * 0.3)
adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))
```

### Example Calculations

**Scenario A: Unanimous, no conflicts**
- Vote confidence: 1.0 (all agents agree)
- Mean severity: 0.0 (no conflicts)
- Final confidence: 1.0 * (1.0 - 0.0 * 0.3) = **1.0**

**Scenario B: Majority, minor conflicts**
- Vote confidence: 0.571 (4/7 for duplicate)
- Mean severity: 0.3 (one low-confidence agent)
- Final confidence: 0.571 * (1.0 - 0.3 * 0.3) = 0.571 * 0.91 = **0.520**

**Scenario C: Split, severe conflicts**
- Vote confidence: 0.429 (3/7 for duplicate)
- Mean severity: 0.8 (opposite conclusion + disagreements)
- Final confidence: 0.429 * (1.0 - 0.8 * 0.3) = 0.429 * 0.76 = **0.326**
- Decision overridden to uncertain (severity > 0.7)

## Over/Under-Confidence Detection

The `ConfidenceAgent` specifically analyzes the CRE's confidence chain for calibration issues:

### Overconfidence Detection

```
CONDITION: hypothesis_confidence > 0.7 AND evidence_confidence < 0.4
RESULT:    The system is confident in a hypothesis despite weak evidence
ACTION:    Force recommendation to "uncertain", set confidence = 0.3
```

### Underconfidence Detection

```
CONDITION: hypothesis_confidence < 0.3 AND evidence_confidence > 0.7
RESULT:    The system has strong evidence but low hypothesis confidence
ACTION:    Force recommendation to "uncertain", set confidence = 0.5
```

These detections propagate through the entire confidence chain:
1. `ConfidenceAgent` produces low confidence due to mismatch
2. Vote confidence for this agent is low
3. Conflict detection may flag `low_confidence` (if < 0.4)
4. Consensus confidence is adjusted down by conflict penalty
5. If severity is high enough, decision is overridden to uncertain

## Confidence Chain from CRE (Detailed)

The upstream CRE provides a `ConfidenceChain` with five components:

```python
@dataclass
class ConfidenceChain:
    premise_confidence: float       # Confidence in premises
    hypothesis_confidence: float    # Confidence in selected hypothesis
    evidence_confidence: float      # Confidence in available evidence
    reasoning_confidence: float     # Confidence in reasoning process
    decision_confidence: float      # Final decision confidence
```

Each agent uses this chain differently:
- `ConfidenceAgent`: Full chain analysis for over/under-confidence
- `SemanticAgent`: References `reasoning_result.confidence` and `reasoning_result.decision` for alignment checks
- `ConflictAgent`: Uses chain components for uncertainty and premise quality analysis
- `EvidenceAgent`: Uses the evidence lists (not directly chain values)

## Design Principles

1. **Monotonic Decomposition**: Confidence flows from source (CRE) through increasingly specialized analyses
2. **Conservative Propagation**: Each stage can only reduce confidence (or keep it unchanged for unanimous cases)
3. **Conflict as Confidence Signal**: Conflicts serve as a confidence penalty, not a rejection mechanism
4. **Deterministic Computation**: Every confidence value is a deterministic function of upstream inputs
5. **Calibration by Design**: Per-agent confidence formulas are designed to match recommendation strength
