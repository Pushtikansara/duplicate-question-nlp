# Memory Consolidation — Duplicate Detection and Knowledge Merging

---

## 1. Overview

The Memory Consolidation subsystem is responsible for detecting duplicate or semantically related memory entries and merging them into consolidated entries that preserve the best information from each source. Consolidation is a core maintenance operation that prevents redundant storage, improves retrieval quality, and ensures that related knowledge is unified under a single, high-quality entry.

---

## 2. Architecture

```
Consolidation Pipeline
  =====================================================================

  Trigger: Manual call or automatic (every N store operations)
     |
     v
  +-----------------------+
  | 1. Collect Candidates |
  |    All active entries |
  +-----------------------+
     |
     v
  +-----------------------+
  | 2. Find Duplicates    |
  |    Group by:          |
  |    - Same memory_type |
  |    - Similar content  |
  |    - Overlapping tags |
  +-----------------------+
     |
     v
  +-----------------------+
  | 3. For Each Group:    |
  |    a. Select best QoS |
  |    b. Merge content   |
  |    c. Merge tags      |
  |    d. Merge lineage   |
  |    e. Compute new     |
  |       quality/conf    |
  +-----------------------+
     |
     v
  +-----------------------+
  | 4. Store Consolidated |
  |    Entry              |
  +-----------------------+
     |
     v
  +-----------------------+
  | 5. Soft Delete        |
  |    Originals          |
  +-----------------------+
     |
     v
  +-----------------------+
  | 6. Audit & Index      |
  |    Update             |
  +-----------------------+
```

---

## 3. Duplicate Detection

The `MemoryConsolidator` ABC (`interfaces.py:201`) defines two methods:

```python
class MemoryConsolidator(ABC):
    @abstractmethod
    def consolidate(self, entries: list[MemoryEntry], store: MemoryStore) -> list[str]:
        """Run consolidation on a list of entries, return IDs of consolidated entries."""
        ...

    @abstractmethod
    def find_duplicates(self, entries: list[MemoryEntry]) -> list[list[MemoryEntry]]:
        """Group entries into duplicate groups."""
        ...
```

### Default Consolidation Algorithm

```python
class DefaultMemoryConsolidator(MemoryConsolidator):
    def __init__(self, config: MemoryConfig | None = None):
        self.config = config or MemoryConfig()

    def find_duplicates(self, entries: list[MemoryEntry]) -> list[list[MemoryEntry]]:
        groups = []
        assigned = set()

        for i, a in enumerate(entries):
            if a.memory_id in assigned:
                continue
            group = [a]
            assigned.add(a.memory_id)

            for j, b in enumerate(entries):
                if b.memory_id in assigned:
                    continue
                if i != j and self._is_duplicate(a, b):
                    group.append(b)
                    assigned.add(b.memory_id)

            if len(group) > 1:
                groups.append(group)

        return groups
```

### Duplicate Criteria

Two entries are considered duplicates if:

1. **Same memory type** (`a.memory_type == b.memory_type`)
2. **Content similarity** — overlapping required content fields:
   - For EPISODIC: matching `question_a` and `question_b` (or high text overlap)
   - For SEMANTIC: overlapping concept names or entity references
   - For REASONING: matching reasoning graph structure
   - For DEBATE: matching decision and similar confidence distribution
   - For PERFORMANCE: matching routing decision
3. **Tag overlap** — at least one shared tag (configurable)

```python
def _is_duplicate(self, a: MemoryEntry, b: MemoryEntry) -> bool:
    if a.memory_type != b.memory_type:
        return False
    if a.status != MemoryStatus.ACTIVE or b.status != MemoryStatus.ACTIVE:
        return False

    content_score = self._content_similarity(a.content, b.content)
    tag_overlap = len(set(a.tags) & set(b.tags)) > 0

    return content_score > 0.7 and tag_overlap
```

---

## 4. Merge Strategies Per Memory Type

| Memory Type | Merge Strategy | Content Merge |
|---|---|---|
| EPISODIC | Keep most recent decision, union tags | Overwrite with latest content |
| SEMANTIC | Union of concepts, entities, relations | Deduplicate concepts by name; merge entity lists |
| REASONING | Union of premises, evidence chains | Deduplicate premises by statement; merge hypothesis lists |
| DEBATE | Average confidence, keep consensus | Merge agent results by agent name; union conflicts |
| PERFORMANCE | Average latency, keep latest routing | Aggregate metrics with mean |

### Example: Semantic Merge

```python
def _merge_semantic(self, entries: list[MemoryEntry]) -> dict:
    merged = {
        "concepts": [],
        "entities": [],
        "relations": [],
        "intent_pattern": entries[0].content.get("intent_pattern", ""),
    }
    seen_concepts = set()
    seen_entities = set()
    seen_relations = set()

    for entry in entries:
        for c in entry.content.get("concepts", []):
            if c["name"] not in seen_concepts:
                merged["concepts"].append(c)
                seen_concepts.add(c["name"])

        for e in entry.content.get("entities", []):
            key = (e["name"], e.get("category", ""))
            if key not in seen_entities:
                merged["entities"].append(e)
                seen_entities.add(key)

        for r in entry.content.get("relations", []):
            key = (r["source"], r["target"], r.get("relation", ""))
            if key not in seen_relations:
                merged["relations"].append(r)
                seen_relations.add(key)

    return merged
```

---

## 5. Quality Score Merging

```
new_quality_score = max(entry.quality_score for entry in group)
```

The highest quality score among the group is retained. This ensures that merging never reduces quality.

---

## 6. Confidence Merging

```
new_confidence = weighted_average(
    values = [entry.confidence for entry in group],
    weights = [entry.quality_score for entry in group]
)
```

Confidence is merged using a quality-weighted average, so entries with higher quality contribute more to the final confidence.

---

## 7. Lineage Preservation During Merge

```python
def _merge_lineage(self, entries: list[MemoryEntry]) -> MemoryLineage:
    return MemoryLineage(
        created_by="consolidator",
        created_at=datetime.now(),
        parent_ids=[e.memory_id for e in entries],
        module_chain=self._merge_module_chains(entries),
        reasoning_id=next(
            (e.lineage.reasoning_id for e in entries if e.lineage.reasoning_id), None
        ),
        debate_id=next(
            (e.lineage.debate_id for e in entries if e.lineage.debate_id), None
        ),
    )
```

All original memory IDs are recorded in `parent_ids`, preserving full provenance.

---

## 8. Tag Merging

```
new_tags = sorted(set(tag for entry in group for tag in entry.tags))
```

Tags from all entries in the group are unioned and sorted.

---

## 9. Soft Deletion of Originals

After consolidation, the original entries are soft-deleted:

```python
for entry in group:
    store.delete(entry.memory_id, soft=True)
    index.remove(entry.memory_id)
    audit.log_access(entry.memory_id, "consolidated",
                     "consolidator",
                     f"Merged into {new_entry.memory_id}")
```

Soft deletion preserves the entries in the store with `status = DELETED` for audit purposes but excludes them from normal queries.

---

## 10. Batch Consolidation Workflow

```python
def consolidate(self, entries: list[MemoryEntry], store: MemoryStore) -> list[str]:
    duplicate_groups = self.find_duplicates(entries)
    consolidated_ids = []

    for group in duplicate_groups:
        # 1. Identify the entry with the best metadata to serve as base
        base = max(group, key=lambda e: (e.quality_score, e.confidence))

        # 2. Merge content based on type
        merged_content = self._merge_content(group)

        # 3. Merge lineage
        merged_lineage = self._merge_lineage(group)

        # 4. Compute new quality and confidence
        new_quality = max(e.quality_score for e in group)
        new_confidence = self._weighted_confidence(group)

        # 5. Build new entry
        new_entry = MemoryEntry(
            memory_id="",  # Will be assigned
            memory_type=base.memory_type,
            version=1,
            timestamp=datetime.now(),
            source_module="consolidator",
            quality_score=new_quality,
            confidence=new_confidence,
            lineage=merged_lineage,
            tags=self._merge_tags(group),
            metadata={"consolidated_from": [e.memory_id for e in group]},
            content=merged_content,
        )

        # 6. Store the consolidated entry
        new_id = store.store(new_entry)

        # 7. Soft-delete originals
        for e in group:
            store.delete(e.memory_id, soft=True)

        consolidated_ids.append(new_id)

    return consolidated_ids
```

---

## 11. Configuration

| Parameter | Default | Description |
|---|---|---|
| `enable_consolidation` | True | Master switch for auto-consolidation |
| `auto_consolidate_interval` | 1000 | Store ops between auto-consolidation triggers |
| `enable_audit` | True | Log consolidation events |

---

## 12. Examples

### Example 1: Two Similar Episodic Entries

```
Entry A: question_a="Install Python", decision="non_duplicate", tags=["python", "install"]
Entry B: question_a="Install Python on Ubuntu", decision="non_duplicate", tags=["python", "install", "ubuntu"]

Consolidation Result:
  - content: merged question texts
  - decision: "non_duplicate" (same decision)
  - tags: ["install", "python", "ubuntu"]
  - quality_score: max(A.quality, B.quality)
  - lineage.parent_ids: ["mem_A", "mem_B"]
  - metadata.consolidated_from: ["mem_A", "mem_B"]
```

### Example 2: Triggering Consolidation

```python
engine = MemoryEngine(config=MemoryConfig(enable_consolidation=True))

# After many store operations...
result = engine.consolidate()
if result:
    print(f"Merged {len(result.merged_ids)} groups")
    for mid in result.merged_ids:
        entry = engine.retrieve(mid)
        print(f"  Created: {mid} from {entry.metadata['consolidated_from']}")
```

---

## 13. Limitations

- Duplicate detection uses simple content overlap, not semantic similarity
- No cross-type consolidation (e.g., linking an episodic entry to a related reasoning entry)
- No partial consolidation (must process all entries or none)
- No configurable similarity thresholds per memory type
- No consolidation undo (originals are soft-deleted but not automatically restorable)

---

## 14. References

- Architecture: `MEMORY_ARCHITECTURE.md`
- Lineage: `MEMORY_LINEAGE.md`
- Quality scoring: `QUALITY_SCORING.md`
- Forgetting (duplicate policy): `FORGETTING_POLICY.md`
- Audit: `AUDIT_SYSTEM.md`
