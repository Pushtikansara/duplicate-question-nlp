# Memory Types — ARES Cognitive Memory Taxonomy

---

## 1. Overview

The ARES CMS defines five specialized memory types, each corresponding to a distinct cognitive function in the duplicate question NLP pipeline. Each memory type is stored as a `MemoryEntry` with the unified schema but enforces type-specific content validation rules.

Memory types are defined via the `MemoryType` enum (`interfaces.py:10`):

```python
class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    REASONING = "reasoning"
    DEBATE = "debate"
    PERFORMANCE = "performance"
```

Content validation is enforced by `DefaultMemoryValidator` (`memory_validator.py:10-16`), which defines required content fields per type. Entries missing required fields fail validation.

---

## 2. Type Comparison Table

| Dimension | Episodic | Semantic | Reasoning | Debate | Performance |
|---|---|---|---|---|---|
| **Enum Value** | `EPISODIC` | `SEMANTIC` | `REASONING` | `DEBATE` | `PERFORMANCE` |
| **Cognitive Analog** | Autobiographical memory | Encyclopedia knowledge | Working memory trace | Social consensus | Metacognitive monitor |
| **Purpose** | Record question pairs and outcomes | Store concepts, entities, relations | Capture reasoning chains and evidence | Record multi-agent debate results | Track latency, cost, routing |
| **Persistence** | Per-request | Cross-request | Per-request | Per-request | Cumulative |
| **Required Content Fields** | `question_a`, `question_b`, `pipeline_used`, `decision` | `concepts`, `entities`, `relations`, `intent_pattern` | `reasoning_graph`, `premises`, `evidence_chains`, `hypotheses`, `confidence_chain`, `reasoning_trace` | `agent_results`, `votes`, `conflicts`, `consensus`, `disagreements`, `confidence_distribution` | `latency_ms`, `pipeline_cost`, `routing_decision`, `memory_hit_rate` |
| **Typical Confidence** | 0.7-1.0 | 0.8-1.0 | 0.5-0.9 | 0.6-0.95 | 0.9-1.0 |
| **Typical Tags** | Question topics, model names, error categories | Entity types, domain names | Reasoning patterns, evidence types | Agent names, conflict types | Model names, pipeline stages |
| **Consolidation Strategy** | Merge similar question pairs | Merge related concept graphs | Merge redundant reasoning paths | Merge duplicate debate records | Aggregate performance stats |
| **Volume** | High (per-request) | Medium (per-concept) | Medium (per-reasoning) | Medium (per-debate) | Low (per-routing) |

---

## 3. Episodic Memory

### Purpose

Episodic memory stores records of specific question pair evaluations. Each episode captures the input questions, the pipeline version used, the decision rendered, and the confidence associated with that decision. This enables post-hoc analysis of prediction patterns, error analysis, and experience replay.

### Content Structure

```python
{
    "question_a": str,          # First question text
    "question_b": str,          # Second question text
    "pipeline_used": str,       # Pipeline version identifier
    "decision": str,            # "duplicate" | "non_duplicate" | "uncertain"
}
```

### Typical Metadata

```python
{
    "model_name": str,          # Primary model used
    "ensemble_weights": dict,   # Weights at time of prediction
    "agreement_score": float,   # Model agreement (0-1)
    "error_categories": list,   # Error types if misprediction
}
```

### Typical Use Case

```python
# After prediction completes
engine.store(
    memory_type=MemoryType.EPISODIC,
    content={
        "question_a": "How to install Python?",
        "question_b": "How to install Python on Ubuntu?",
        "pipeline_used": "ares_v2.1",
        "decision": "non_duplicate",
    },
    tags=["python", "installation", "os-specific"],
    source_module="prediction_pipeline",
    confidence=0.92,
)
```

### Retrieval Pattern

```python
# Find similar past episodes
query = MemoryQueryBuilder.text_search("install python ubuntu")
result = engine.search(query)
```

---

## 4. Semantic Memory

### Purpose

Semantic memory stores structured knowledge about concepts, entities, relations, and intent patterns extracted from question pairs. Unlike episodic memory (specific events), semantic memory captures generalizable knowledge that persists across requests.

### Content Structure

```python
{
    "concepts": list[dict],     # [{name: str, type: str, confidence: float}]
    "entities": list[dict],     # [{name: str, category: str, value: str}]
    "relations": list[dict],    # [{source: str, target: str, relation: str, weight: float}]
    "intent_pattern": str,      # Intent category identified
}
```

### Typical Metadata

```python
{
    "knowledge_base_version": str,
    "linguistic_engine": str,
    "extraction_method": str,  # "pattern" | "ner" | "hybrid"
}
```

### Typical Use Case

```python
engine.store(
    memory_type=MemoryType.SEMANTIC,
    content={
        "concepts": [
            {"name": "Python", "type": "programming_language", "confidence": 0.95},
            {"name": "installation", "type": "action", "confidence": 0.88},
        ],
        "entities": [
            {"name": "Python", "category": "language", "value": "python"},
            {"name": "Ubuntu", "category": "os", "value": "ubuntu"},
        ],
        "relations": [
            {"source": "Python", "target": "Ubuntu", "relation": "runs_on", "weight": 1.0},
        ],
        "intent_pattern": "installation_guide",
    },
    tags=["python", "ubuntu", "installation"],
    source_module="linguistic_engine",
    confidence=0.90,
)
```

---

## 5. Reasoning Memory

### Purpose

Reasoning memory captures the full reasoning trace produced by the Cognitive Reasoning Engine (CRE). This includes the reasoning graph, premises, evidence chains, hypotheses considered, and the confidence chain that led to the final conclusion.

### Content Structure

```python
{
    "reasoning_graph": dict,        # {nodes: [...], edges: [...]}
    "premises": list[dict],         # [{statement: str, source: str, confidence: float}]
    "evidence_chains": list[dict],  # [{premises: [...], conclusion: str, confidence: float}]
    "hypotheses": list[dict],       # [{statement: str, confidence: float, status: str}]
    "confidence_chain": list[dict], # [{stage: str, confidence: float, reason: str}]
    "reasoning_trace": str,         # Free-text reasoning summary
}
```

### Typical Use Case

```python
engine.store(
    memory_type=MemoryType.REASONING,
    content={
        "reasoning_graph": {
            "nodes": ["q1_intent", "q2_intent", "entity_overlap"],
            "edges": [("q1_intent", "entity_overlap", "supports")],
        },
        "premises": [
            {"statement": "Both questions ask about installation",
             "source": "intent_agent", "confidence": 0.95},
            {"statement": "Different target operating systems",
             "source": "entity_agent", "confidence": 0.88},
        ],
        "evidence_chains": [
            {
                "premises": ["Both installation", "Different OS"],
                "conclusion": "Related but not duplicates",
                "confidence": 0.82,
            }
        ],
        "hypotheses": [
            {"statement": "Questions are duplicates", "confidence": 0.30, "status": "rejected"},
            {"statement": "Questions are related but distinct", "confidence": 0.82, "status": "accepted"},
        ],
        "confidence_chain": [
            {"stage": "intent_analysis", "confidence": 0.95, "reason": "Match"},
            {"stage": "entity_analysis", "confidence": 0.88, "reason": "OS mismatch"},
            {"stage": "final", "confidence": 0.82, "reason": "Weighted combination"},
        ],
        "reasoning_trace": "Intent matches (installation), but entity mismatch (ubuntu vs linux) reduces confidence.",
    },
    tags=["reasoning", "installation", "entity_mismatch"],
    source_module="reasoning_engine",
    confidence=0.82,
)
```

---

## 6. Debate Memory

### Purpose

Debate memory records the results of the Multi-Agent Cognitive Debate Engine (MADE). Each debate entry captures individual agent results, votes, detected conflicts, consensus outcome, and per-agent confidence distributions.

### Content Structure

```python
{
    "agent_results": list[dict],    # [{agent_name, confidence, recommendation, ...}]
    "votes": list[dict],            # [{agent_name, recommendation, confidence, weight}]
    "conflicts": list[dict],        # [{conflict_type, agents, description, severity}]
    "consensus": dict,              # {decision, confidence, vote_counts, strategy_used}
    "disagreements": list[dict],    # [{agent_a, agent_b, issue, severity}]
    "confidence_distribution": list[float],  # Per-agent confidence values
}
```

### Typical Use Case

```python
engine.store(
    memory_type=MemoryType.DEBATE,
    content={
        "agent_results": [
            {"agent_name": "IntentAgent", "confidence": 0.92, "recommendation": "duplicate"},
            {"agent_name": "EntityAgent", "confidence": 0.78, "recommendation": "non_duplicate"},
        ],
        "votes": [
            {"agent_name": "IntentAgent", "recommendation": "duplicate", "confidence": 0.92, "weight": 1.0},
            {"agent_name": "EntityAgent", "recommendation": "non_duplicate", "confidence": 0.78, "weight": 1.0},
        ],
        "conflicts": [
            {"conflict_type": "ENTITY_MISMATCH", "agents": ["IntentAgent", "EntityAgent"],
             "description": "Intent matches but entities differ", "severity": 0.6},
        ],
        "consensus": {
            "decision": "related",
            "confidence": 0.72,
            "vote_counts": {"duplicate": 5, "non_duplicate": 3},
            "strategy_used": "majority_voting",
        },
        "disagreements": [
            {"agent_a": "IntentAgent", "agent_b": "EntityAgent",
             "issue": "entity_mismatch", "severity": 0.6},
        ],
        "confidence_distribution": [0.92, 0.78, 0.85, 0.91, 0.67, 0.73, 0.88, 0.82],
    },
    tags=["debate", "entity_mismatch", "majority_consensus"],
    source_module="debate_engine",
    confidence=0.72,
)
```

### Retrieval Pattern

```python
# Find debates with entity mismatches
query = MemoryQuery.by_type(MemoryType.DEBATE)
query.tags = ["entity_mismatch"]
result = engine.search(query)
```

---

## 7. Performance Memory

### Purpose

Performance memory stores latency, cost, and routing decision data for each pipeline stage. This enables performance profiling, bottleneck identification, and adaptive routing optimization.

### Content Structure

```python
{
    "latency_ms": dict,             # {stage_name: duration_ms}
    "pipeline_cost": float,         # Total computational cost
    "routing_decision": str,        # "skip" | "full" | "debate"
    "memory_hit_rate": float,       # Fraction of retrievals that hit
}
```

### Typical Use Case

```python
engine.store(
    memory_type=MemoryType.PERFORMANCE,
    content={
        "latency_ms": {
            "preprocessing": 12.3,
            "embedding": 45.6,
            "inference": 234.5,
            "reasoning": 8.9,
            "debate": 2.1,
            "total": 303.4,
        },
        "pipeline_cost": 0.0045,
        "routing_decision": "full",
        "memory_hit_rate": 0.67,
    },
    tags=["performance", "full_pipeline", "routing:full"],
    source_module="routing_engine",
    confidence=1.0,
)
```

---

## 8. Type Registry and Factories

The `MemoryTypeRegistry` (`memory_registry.py:8`) maps memory types to factory functions:

```python
registry = MemoryTypeRegistry()

def create_episodic(q1, q2, pipeline, decision):
    return MemoryEntry(
        memory_type=MemoryType.EPISODIC,
        content={
            "question_a": q1,
            "question_b": q2,
            "pipeline_used": pipeline,
            "decision": decision,
        },
        ...
    )

registry.register(MemoryType.EPISODIC, create_episodic)
```

Factories can be registered for each type and retrieved via `registry.get_factory(type)`.

---

## 9. Validation Rules

| Memory Type | Required Fields | Optional Fields |
|---|---|---|
| EPISODIC | `question_a`, `question_b`, `pipeline_used`, `decision` | `error_categories`, `model_confidence` |
| SEMANTIC | `concepts`, `entities`, `relations`, `intent_pattern` | `knowledge_base_refs` |
| REASONING | `reasoning_graph`, `premises`, `evidence_chains`, `hypotheses`, `confidence_chain`, `reasoning_trace` | `alternative_paths` |
| DEBATE | `agent_results`, `votes`, `conflicts`, `consensus`, `disagreements`, `confidence_distribution` | `debate_id` |
| PERFORMANCE | `latency_ms`, `pipeline_cost`, `routing_decision`, `memory_hit_rate` | `model_info`, `batch_info` |

---

## 10. References

- System overview: `COGNITIVE_MEMORY_SYSTEM.md`
- MemoryEngine: `MEMORY_ENGINE.md`
- Validator source: `memory_validator.py`
