# Quality Scoring — Composite Memory Quality Assessment

---

## 1. Overview

The Quality Scoring subsystem computes a composite quality score for every memory entry, providing a unified measure of entry value that accounts for confidence, evidence support, usage frequency, and content completeness. Quality scores influence retrieval ranking and forgetting decisions, ensuring that high-quality entries are prioritized and retained while low-quality entries are candidates for archival.

---

## 2. Architecture

```
QualityScorer
  |
  +-- compute(entry) -> float          # Composite quality score [0, 1]
  +-- compute_batch(entries) -> list[float]
  |
  Components:
    +-- confidence_score:  entry.confidence
    +-- evidence_score:    evidence_count / max_evidence
    +-- usage_score:       access_count / max_access
    +-- completeness_score: present_fields / required_fields
```

---

## 3. Composite Score Formula

```
quality_score = confidence * W_conf
              + evidence   * W_evidence
              + usage      * W_usage
              + completeness * W_completeness

where: W_conf + W_evidence + W_usage + W_completeness = 1.0
```

Default weights:

| Component | Weight | Description |
|---|---|---|
| Confidence | 0.40 | Model/pipeline confidence in the entry |
| Evidence | 0.25 | Number of supporting evidence items |
| Usage | 0.15 | Access frequency relative to peers |
| Completeness | 0.20 | Fraction of required content fields present |

### Formula

```python
class MemoryQualityScorer:
    DEFAULT_WEIGHTS = {
        "confidence": 0.40,
        "evidence": 0.25,
        "usage": 0.15,
        "completeness": 0.20,
    }

    def compute(self, entry: MemoryEntry) -> float:
        confidence_score = self._confidence(entry)
        evidence_score = self._evidence(entry)
        usage_score = self._usage(entry)
        completeness_score = self._completeness(entry)

        score = (
            self.weights["confidence"] * confidence_score
            + self.weights["evidence"] * evidence_score
            + self.weights["usage"] * usage_score
            + self.weights["completeness"] * completeness_score
        )

        return max(0.0, min(1.0, score))  # Clamp to [0, 1]
```

---

## 4. Component Calculation Methods

### 4.1 Confidence Score

```
confidence_score = entry.confidence

Source: Directly from MemoryEntry.confidence [0, 1]
Rationale: The pipeline's own confidence assessment.
```

### 4.2 Evidence Score

```
evidence_score = min(1.0, evidence_count / max_evidence)

Where:
  evidence_count = number of evidence-like items in content
    - EPISODIC: evidence from error categories count
    - SEMANTIC: number of concepts + entities + relations
    - REASONING: number of premises + evidence chains
    - DEBATE: number of agent results + conflicts
    - PERFORMANCE: number of latency entries
  max_evidence = 20 (configurable ceiling)

Rationale: Entries with more supporting evidence are more valuable.
```

### 4.3 Usage Score

```
usage_score = min(1.0, access_count / max_access)

Where:
  access_count = number of times entry has been retrieved
  max_access = 100 (configurable ceiling)

With exponential moving average decay:
if last_access is not None:
  days_since_access = (now - last_access).days
  decay = exp(-days_since_access / 30)  # 30-day half-life
  usage_score *= decay

Rationale: Frequently accessed entries are more valuable.
Recent access is weighted more heavily.
```

### 4.4 Completeness Score

```
completeness_score = present_fields / required_fields

Where:
  required_fields = type-specific required content fields (from memory_validator.py)
  present_fields = number of required fields present in content

Required fields per type:
  EPISODIC:  4 fields (question_a, question_b, pipeline_used, decision)
  SEMANTIC:  4 fields (concepts, entities, relations, intent_pattern)
  REASONING: 6 fields (reasoning_graph, premises, evidence_chains, hypotheses,
                       confidence_chain, reasoning_trace)
  DEBATE:    6 fields (agent_results, votes, conflicts, consensus,
                       disagreements, confidence_distribution)
  PERFORMANCE: 4 fields (latency_ms, pipeline_cost, routing_decision, memory_hit_rate)

Rationale: Complete entries are more valuable than partial ones.
```

---

## 5. Score Bounds

| Score Range | Interpretation | Typical Sources |
|---|---|---|
| 0.8 - 1.0 | Excellent | High confidence, complete, frequently accessed, well-supported |
| 0.6 - 0.8 | Good | Adequate confidence, mostly complete, moderate usage |
| 0.4 - 0.6 | Fair | Moderate confidence, some missing fields, low usage |
| 0.2 - 0.4 | Poor | Low confidence, sparse content, rarely accessed |
| 0.0 - 0.2 | Critical | Very low confidence, near-empty content, never accessed |

---

## 6. How Quality Affects Retrieval Ranking

Quality score is one component of the `CompositeRanker` formula:

```python
composite_score = (
    0.3 * recency_score
    + 0.3 * confidence_score
    + 0.2 * quality_score    # <-- quality factor
    + 0.2 * usage_score
)
```

Quality can also be used as the sole ranking criterion via `QualityRanker`:

```python
class QualityRanker(RetrievalRanker):
    def rank(self, entries, query):
        return sorted(entries, key=lambda e: e.quality_score, reverse=True)
```

---

## 7. How Quality Affects Forgetting

Quality score directly determines which entries survive the forgetting policies:

| Policy | Quality Threshold | Entries Below Threshold |
|---|---|---|
| Age Policy | `quality_threshold` (default 0.3) | Archived (even if young) |
| Quality Policy | `quality_threshold` (default 0.3) | Archived (after 7-day grace period) |
| Age + High Quality | `quality_threshold` | Exempt from age-based forgetting |

---

## 8. Quality Evolution Over Time

```
Entry Created:
  quality = compute(entry)  # Based on initial confidence + completeness

After Each Access:
  entry.metadata.access_count += 1
  entry.metadata.last_access = now
  # Usage-based quality component increases with access

After Each Update:
  entry.quality_score = compute(entry)  # Recalculated
  # Confidence may change, evidence may grow

After Consolidation:
  new_quality = max(parent_qualities)
  # Merged entry inherits the highest quality score

After Period of Disuse:
  usage decay reduces usage component
  quality declines until forgetting threshold reached
```

---

## 9. Examples

### Example 1: High-Quality Entry

```python
entry = MemoryEntry(
    confidence=0.95,
    content={
        "question_a": "How to install Python?",
        "question_b": "How to install Python on Ubuntu?",
        "pipeline_used": "ares_v2",
        "decision": "non_duplicate",
    },
    tags=["python", "install", "ubuntu"],
    metadata={"access_count": 45, "last_access": datetime.now()},
)

scorer = MemoryQualityScorer()
score = scorer.compute(entry)
# confidence:    0.95 * 0.40 = 0.380
# evidence:      0.00 * 0.25 = 0.000  (no evidence items in episodic)
# usage:         min(45/100, 1.0) * 0.15 = 0.068
# completeness:  4/4 * 0.20 = 0.200
# total:         0.648
```

### Example 2: Low-Quality Entry

```python
entry = MemoryEntry(
    confidence=0.35,
    content={
        "question_a": "Python?",
        # missing: question_b, pipeline_used, decision
    },
    tags=[],
    metadata={"access_count": 1, "last_access": datetime.now() - timedelta(days=200)},
)

scorer = MemoryQualityScorer()
score = scorer.compute(entry)
# confidence:    0.35 * 0.40 = 0.140
# evidence:      0.00 * 0.25 = 0.000
# usage:         0.00 * 0.15 = 0.000  (decayed to 0)
# completeness:  1/4 * 0.20 = 0.050
# total:         0.190  (below forgetting threshold of 0.3)
```

---

## 10. Configuration

| Parameter | Default | Component | Description |
|---|---|---|---|
| `weight.confidence` | 0.40 | Confidence | Weight for confidence component |
| `weight.evidence` | 0.25 | Evidence | Weight for evidence component |
| `weight.usage` | 0.15 | Usage | Weight for usage frequency component |
| `weight.completeness` | 0.20 | Completeness | Weight for completeness component |
| `max_evidence` | 20 | Evidence | Ceiling for evidence count normalization |
| `max_access` | 100 | Usage | Ceiling for access count normalization |
| `usage_half_life_days` | 30 | Usage | Exponential decay half-life for usage score |

Weights are configurable through `MemoryQualityScorer` constructor but are not yet exposed in `MemoryConfig`.

---

## 11. Limitations

- Fixed weights are not learned from data; may not reflect actual information value
- Usage decay is heuristic (exponential with 30-day half-life) rather than empirically calibrated
- No cross-entry quality comparisons (quality is absolute, not relative to type or source)
- No quality prediction for new entries (quality = 0 until evidence/usage accumulate)
- Completeness is structural (fields present) not semantic (field quality)

---

## 12. References

- Architecture: `MEMORY_ARCHITECTURE.md`
- Retrieval ranking: `RETRIEVAL_ENGINE.md`
- Forgetting policies: `FORGETTING_POLICY.md`
- Consolidation (quality merge): `MEMORY_CONSOLIDATION.md`
