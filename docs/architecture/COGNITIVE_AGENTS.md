# Cognitive Agents -- Detailed Specification

## Overview

MADE defines eight cognitive agents, each implementing the `CognitiveAgent` abstract base class. Every agent is a deterministic function that transforms semantic representations, assessments, and reasoning results into structured evaluations. Agents operate independently without inter-agent communication. This document describes each agent's purpose, algorithm, confidence logic, and extension patterns.

## Agent Interface

```
class CognitiveAgent(ABC):

    @abstractmethod
    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    def weight(self) -> float:
        return 1.0
```

### Agent Lifecycle

1. **Registration**: Agent is instantiated and registered via `AgentRegistry.register()`
2. **Evaluation**: `DebateEngine.debate()` calls `agent.evaluate()` with full pipeline context
3. **Result Production**: Agent returns `AgentResult` with confidence, recommendation, evidence, and warnings
4. **Vote Extraction**: `DebateEngine._build_votes()` converts `AgentResult` to `Vote` (excludes consensus_agent)
5. **Collection**: Results are collected into `DebateResult.agent_results` for downstream analysis

### Inputs

| Input | Type | Description | Optionality |
|-------|------|-------------|-------------|
| `rep_a` | `SemanticRepresentation` | First question's full semantic representation | Required |
| `rep_b` | `SemanticRepresentation` | Second question's full semantic representation | Required |
| `assessment` | `SemanticAssessment` | Cross-question similarity and conflict assessment | Optional |
| `reasoning_result` | `ReasoningResult` | Upstream CRE reasoning output with evidence chains | Optional |

### Outputs

All agents return `AgentResult`:

| Field | Type | Description |
|-------|------|-------------|
| `agent_name` | `str` | Unique agent identifier |
| `confidence` | `float` | [0.0, 1.0] confidence in the recommendation |
| `recommendation` | `str` | `"duplicate"`, `"not_duplicate"`, or `"uncertain"` |
| `supporting_evidence` | `list[Evidence]` | Evidence supporting the recommendation |
| `contradicting_evidence` | `list[Evidence]` | Evidence contradicting the recommendation |
| `warnings` | `list[str]` | Operational warnings |
| `metadata` | `dict[str, Any]` | Agent-specific diagnostic data |
| `processing_time_ms` | `float` | Wall-clock time for evaluation in milliseconds |

## Agent 1: IntentAgent

### Purpose
Evaluates whether two questions share the same underlying intent by comparing intent summaries and intent similarity scores from the semantic assessment.

### Inputs Used
- `rep_a.intent_summary`, `rep_b.intent_summary`
- `assessment.intent_similarity.score`
- `assessment.intent_similarity.confidence`

### Algorithm

```
1. If both intent summaries are missing:
   recommendation = uncertain, confidence = 0.5, warning = "No intent data"
2. If one intent summary is missing:
   recommendation = uncertain, confidence = 0.4, warning = "Missing intent"
3. If assessment provided with intent_similarity:
   a. Score > 0.7: recommendation = duplicate, confidence = score * confidence
   b. Score < 0.3: recommendation = not_duplicate, confidence = 0.3
   c. Otherwise: fall through to exact-match check
4. Exact match of intent_summary strings (case-insensitive):
   recommendation = duplicate, confidence = 0.8
5. Otherwise:
   recommendation = uncertain, confidence = 0.4
```

### Confidence Logic
Confidence is a product of similarity score and similarity confidence when assessment data is present. Falls back to fixed heuristic values when assessment is unavailable.

### Decision Table

| Has Intent A | Has Intent B | Intent Similarity | Recommendation | Confidence |
|-------------|-------------|------------------|----------------|------------|
| No | No | N/A | uncertain | 0.5 |
| Yes | No | N/A | uncertain | 0.4 |
| Yes | Yes | > 0.7 | duplicate | score * conf |
| Yes | Yes | < 0.3 | not_duplicate | 0.3 |
| Yes | Yes | exact match | duplicate | 0.8 |
| Yes | Yes | else | uncertain | 0.4 |

## Agent 2: SemanticAgent

### Purpose
Evaluates semantic similarity between question pairs by combining semantic similarity scores, concept overlap, and reasoning engine alignment.

### Inputs Used
- `assessment.semantic_similarity`
- `assessment.concept_overlap.overlap_score`
- `rep_a.concepts`, `rep_b.concepts`
- `reasoning_result.decision`, `reasoning_result.confidence`

### Algorithm

```
1. If no assessment: uncertain, 0.5, warning "No semantic assessment"
2. Compute combined_sem = semantic_similarity * 0.6 + overlap_score * 0.4
3. If combined_sem >= 0.5 and semantic_similarity >= 0.7:
   recommendation = duplicate, confidence = combined_sem
4. If combined_sem <= 0.4 and semantic_similarity <= 0.3:
   recommendation = not_duplicate, confidence = 1.0 - combined_sem
5. Otherwise: uncertain, 0.5
6. Check alignment with reasoning_result:
   a. If align: add supporting evidence
   b. If conflict: add contradicting evidence + warning
7. Check concept count mismatch: add neutral evidence
```

### Confidence Logic
Uses weighted combination of semantic similarity (0.6 weight) and concept overlap (0.4 weight). When recommending `not_duplicate`, confidence is inverted: `1.0 - combined_sem`.

### Decision Table

| Semantic Sim. | Concept Overlap | Combined | Reasoning Aligns | Recommendation | Confidence |
|--------------|----------------|----------|-----------------|----------------|------------|
| >= 0.7 | >= 0.5 | >= 0.5 | any | duplicate | combined_sem |
| <= 0.3 | <= 0.4 | <= 0.4 | any | not_duplicate | 1.0 - combined |
| any | any | any | yes (agree) | (as above) | boosted |
| any | any | any | no (disagree) | (as above) | warning |
| any | any | else | any | uncertain | 0.5 |

## Agent 3: EntityAgent

### Purpose
Analyzes entity-level overlap and conflicts between the two questions by comparing entity labels and entity overlap assessments.

### Inputs Used
- `rep_a.entities`, `rep_b.entities`
- `assessment.entity_overlap.overlap_score`
- `assessment.entity_overlap.shared_entities`
- `assessment.entity_overlap.conflicts`

### Algorithm

```
1. Extract entity label sets from question representations
2. Compute shared, only_in_a, only_in_b sets
3. If assessment entity_overlap available: add overlap and conflict evidence
4. If no entities in either: uncertain, 0.5
5. If shared > max(only_in_a, only_in_b):
   duplicate, confidence = shared / (shared + only_a + only_b)
6. If only_a + only_b > shared and either non-empty:
   not_duplicate, confidence = (only_a+only_b) / total_unique
7. Otherwise: uncertain, 0.5
```

### Confidence Logic
Confidence is proportional to entity set ratios. For duplicate, it is the fraction of shared entities relative to total. For not_duplicate, it is the fraction of exclusive entities relative to total unique.

### Decision Table

| Shared Entities | Only in A | Only in B | Recommendation | Confidence |
|----------------|-----------|-----------|----------------|------------|
| 0 | 0 | 0 | uncertain | 0.5 |
| > max(only_a, only_b) | any | any | duplicate | shared / total |
| any | > 0 | > 0 | not_duplicate | exclusive / total |
| == only_a | > 0 | 0 | not_duplicate | exclusive / total |
| == only_b | 0 | > 0 | not_duplicate | exclusive / total |

## Agent 4: RelationAgent

### Purpose
Evaluates relational structure similarity between question representations, examining relationship chains, types, and alignment.

### Inputs Used
- `rep_a.relationships`, `rep_b.relationships`
- `assessment.relation_similarity.score`
- `assessment.relation_similarity.matching_relations`
- `assessment.relation_similarity.missing_in_a`
- `assessment.relation_similarity.missing_in_b`

### Algorithm

```
1. If no relations in either: uncertain, 0.5, neutral evidence
2. If relations in only one: warning "Asymmetric relation data"
3. If assessment relation_similarity available:
   a. score > 0.7: duplicate, confidence = score
   b. score < 0.3: not_duplicate, confidence = 1.0 - score
   c. otherwise: uncertain, 0.5, with evidence about missing/matching
4. Extract shared relation types as supporting evidence
```

### Confidence Logic
Direct mapping from relation similarity score for clear signals. Inversion for low similarity. Defaults to 0.5 for ambiguous similarity ranges.

## Agent 5: ConflictAgent

### Purpose
Detects explicit conflicts in assessment data and reasoning results, including contradictory hypotheses, high uncertainty, and low confidence premises.

### Inputs Used
- `assessment.conflicts` (list of `Conflict` objects)
- `reasoning_result.contradicting_evidence`
- `reasoning_result.hypotheses`
- `reasoning_result.uncertainty`
- `reasoning_result.premises`

### Algorithm

```
1. Process assessment conflicts: each becomes contradicting evidence
2. Process reasoning contradictions: each becomes contradicting evidence
3. Check if both duplicate and not_duplicate hypotheses have supporting premises
4. If uncertainty > 0.6: high uncertainty warning
5. Count low-confidence premises (< 0.5)
6. If conflict_count == 0: duplicate, 0.8
7. If conflict_count <= 2: uncertain, 0.5
8. If conflict_count > 2: not_duplicate, max(0.1, 1.0 - count * 0.2)
```

### Confidence Logic
Confidence degrades linearly with conflict count: `1.0 - conflict_count * 0.2`, floored at 0.1. Zero conflicts yields high confidence (0.8). One or two conflicts yields 0.5.

## Agent 6: ConfidenceAgent

### Purpose
Analyzes the confidence chain from the CRE to detect over-confidence (high hypothesis confidence with low evidence confidence) and under-confidence (low hypothesis confidence with high evidence confidence).

### Inputs Used
- `reasoning_result.confidence_chain`
- `reasoning_result.confidence`

### Algorithm

```
1. If no reasoning_result or confidence_chain: uncertain, 0.5
2. Extract chain components: premise_conf, hypothesis_conf, evidence_conf,
   reasoning_conf, decision_conf
3. Overconfidence detection: hypothesis > 0.7 and evidence < 0.4
   -> uncertain, 0.3, warning
4. Underconfidence detection: hypothesis < 0.3 and evidence > 0.7
   -> uncertain, 0.5, warning
5. If decision_conf > 0.7: duplicate, confidence = decision_conf
6. If decision_conf < 0.3: not_duplicate, confidence = 1.0 - decision_conf
7. Otherwise: uncertain, confidence = decision_conf
```

### Decision Table

| Hypothesis Conf | Evidence Conf | Pattern | Recommendation | Confidence |
|----------------|--------------|---------|----------------|------------|
| > 0.7 | < 0.4 | overconfidence | uncertain | 0.3 |
| < 0.3 | > 0.7 | underconfidence | uncertain | 0.5 |
| any | any | decision_conf > 0.7 | duplicate | decision_conf |
| any | any | decision_conf < 0.3 | not_duplicate | 1.0 - decision_conf |
| any | any | else | uncertain | decision_conf |

## Agent 7: EvidenceAgent

### Purpose
Evaluates the quality, balance, and integrity of evidence from the CRE reasoning result. Deduplicates evidence, ranks by quality, and assesses support-contradiction balance.

### Inputs Used
- `reasoning_result.supporting_evidence`
- `reasoning_result.contradicting_evidence`

### Algorithm

```
1. If no reasoning_result: uncertain, 0.5
2. Merge and deduplicate evidence (by text content)
3. Rank supporting evidence by weight * confidence
4. Flag low-quality evidence (product < 0.3)
5. If supporting > contradicting * 2: duplicate
   confidence = supporting / (supporting + contradicting)
6. If contradicting > supporting * 2: not_duplicate
   confidence = contradicting / (supporting + contradicting)
7. Otherwise: uncertain, 0.5
```

### Confidence Logic
Confidence is proportional to the dominant evidence type's proportion of total evidence. Balanced evidence defaults to 0.5 confidence.

## Agent 8: ConsensusAgent

### Purpose
Meta-agent that does not perform evaluation. Its sole purpose is to provide a placeholder in the agent list while the actual consensus computation is handled by the `DebateEngine`.

### Behavior
Always returns `recommendation="uncertain"`, `confidence=1.0`, empty evidence lists. The engine explicitly excludes this agent's vote during vote building.

## Extension: Adding a New Agent

To add a new cognitive agent:

1. Create a class inheriting from `CognitiveAgent`
2. Implement `name` property (must be unique among registered agents)
3. Implement `evaluate()` method with deterministic logic
4. Optionally override `weight` property if weighted voting will use custom weights
5. Register via `AgentRegistry.register(MyNewAgent())`

### Template

```python
from duplicate_question_app._agents.interfaces import CognitiveAgent
from duplicate_question_app._agents.agent_result import AgentResult
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment
from duplicate_question_app._reasoning.reasoning_result import ReasoningResult

class MyNewAgent(CognitiveAgent):
    @property
    def name(self) -> str:
        return "my_new_agent"

    def evaluate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
    ) -> AgentResult:
        # Deterministic evaluation logic here
        return AgentResult(
            agent_name=self.name,
            confidence=0.8,
            recommendation="duplicate",
            supporting_evidence=[],
            contradicting_evidence=[],
            warnings=[],
            metadata={},
            processing_time_ms=0.0,
        )
```

### Registration

```python
from duplicate_question_app._agents.agent_registry import get_agent_registry

registry = get_agent_registry()
registry.register(MyNewAgent())
```
