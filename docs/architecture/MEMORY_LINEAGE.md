# Memory Lineage — Provenance Tracking for Cognitive Memory

---

## 1. Overview

The ARES CMS implements a full lineage tracking system that records the provenance of every memory entry. Lineage provides a complete chain of custody for each memory — who created it, what it was derived from, which modules processed it, and which reasoning or debate session produced it. This enables full explainability, auditability, and scientific reproducibility for all stored knowledge.

---

## 2. Architecture

Lineage is represented by the `MemoryLineage` dataclass (`interfaces.py:24`):

```python
@dataclass
class MemoryLineage:
    created_by: str                # Module or agent that created the entry
    created_at: datetime           # Original creation timestamp
    parent_ids: list[str]          # IDs of parent entries (for derived memories)
    module_chain: list[str]        # Ordered list of modules that processed this memory
    reasoning_id: str | None       # ID of the reasoning session that produced this memory
    debate_id: str | None          # ID of the debate session that produced this memory
```

---

## 3. Lineage Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `created_by` | `str` | Identifier of the source that created this entry | `"prediction_pipeline"`, `"entity_agent"`, `"consolidator"` |
| `created_at` | `datetime` | Timestamp of original creation (not last update) | `2026-07-21T10:00:00` |
| `parent_ids` | `list[str]` | Memory IDs of parent entries (empty for original entries) | `["mem_001", "mem_003"]` |
| `module_chain` | `list[str]` | Ordered list of processing modules | `["perception", "reasoning", "debate"]` |
| `reasoning_id` | `str \| None` | Links to a specific reasoning trace | `"reasoning_4f8a"` |
| `debate_id` | `str \| None` | Links to a specific debate trace | `"debate_7c2b"` |

---

## 4. Ancestor Traversal

The lineage system supports traversing the ancestor chain of any memory entry:

```
get_ancestors(entry, store) -> list[MemoryEntry]

Algorithm:
  ancestors = []
  queue = list(entry.lineage.parent_ids)
  visited = set()

  while queue:
    parent_id = queue.pop(0)
    if parent_id in visited:
      continue
    visited.add(parent_id)
    parent = store.retrieve(parent_id)
    if parent:
      ancestors.append(parent)
      queue.extend(parent.lineage.parent_ids)

  return ancestors  # Ordered from nearest to farthest
```

---

## 5. Descendant Traversal

Descendant traversal finds all entries that directly or indirectly derive from a given entry:

```
get_descendants(entry_id, store) -> list[MemoryEntry]

Algorithm:
  all_entries = store.list_all()
  descendants = []
  queue = [entry_id]
  visited = set()

  while queue:
    current_id = queue.pop(0)
    if current_id in visited:
      continue
    visited.add(current_id)
    for candidate in all_entries:
      if current_id in candidate.lineage.parent_ids:
        descendants.append(candidate)
        queue.append(candidate.memory_id)

  return descendants
```

---

## 6. Lineage During Consolidation

When the `MemoryConsolidator` merges duplicate entries, lineage is preserved in the consolidated entry:

```
Original entries:
  Entry A: lineage.parent_ids = []
  Entry B: lineage.parent_ids = []

Consolidated entry C:
  lineage.created_by = "consolidator"
  lineage.parent_ids = [A.memory_id, B.memory_id]
  lineage.module_chain = A.lineage.module_chain + ["consolidation"]
  lineage.reasoning_id = A.lineage.reasoning_id or B.lineage.reasoning_id
  lineage.debate_id = A.lineage.debate_id or B.lineage.debate_id
```

This ensures that the provenance of both original entries is preserved in the consolidated result.

---

## 7. Lineage During Versioning

Each version update extends the lineage:

```
Initial:
  Entry v1: lineage.parent_ids = []

First Update:
  Entry v2: lineage.parent_ids = ["mem_001"]  # Points to v1

Second Update:
  Entry v3: lineage.parent_ids = ["mem_001"]  # Still points to original (or could point to v2)
```

The versioning system records versions independently, while lineage tracks conceptual parentage (which entry was this derived from).

---

## 8. Provenance Queries

### Full Provenance of an Entry

```python
def get_provenance(entry_id, store, versioning):
    entry = store.retrieve(entry_id)
    if not entry:
        return None

    return {
        "entry": entry.to_dict(),
        "ancestors": [e.to_dict() for e in get_ancestors(entry, store)],
        "descendants": [e.to_dict() for e in get_descendants(entry_id, store)],
        "version_history": [e.to_dict() for e in versioning.get_version_history(entry_id, store)],
        "module_path": entry.lineage.module_chain,
        "reasoning_link": entry.lineage.reasoning_id,
        "debate_link": entry.lineage.debate_id,
    }
```

### Module Chain Extraction

```python
chain = entry.lineage.module_chain
# ["perception", "reasoning", "debate"]
# Indicates the entry was: perceived -> reasoned about -> debated
```

---

## 9. Examples

### Example 1: Original Entry from Prediction Pipeline

```python
lineage = MemoryLineage(
    created_by="prediction_pipeline",
    created_at=datetime.now(),
    parent_ids=[],
    module_chain=["perception", "linguistic_analysis", "inference"],
    reasoning_id=None,
    debate_id=None,
)
```

### Example 2: Derived Entry from Consolidation

```python
lineage = MemoryLineage(
    created_by="consolidator",
    created_at=datetime.now(),
    parent_ids=["mem_001", "mem_004", "mem_007"],
    module_chain=["perception", "linguistic_analysis", "inference", "consolidation"],
    reasoning_id="reasoning_abc123",
    debate_id="debate_def456",
)
```

### Example 3: Traversing Ancestors

```python
consolidated = store.retrieve("mem_012")
# consolidated.lineage.parent_ids = ["mem_001", "mem_004", "mem_007"]

ancestors = get_ancestors(consolidated, store)
# len(ancestors) == 3
# ancestors[0].memory_id == "mem_001"
```

---

## 10. Research Value

| Research Requirement | How Lineage Supports It |
|---|---|
| Explainability | Every decision can be traced back to its source through `module_chain` and `parent_ids` |
| Audit | Full chain of custody for every memory entry |
| Scientific Reproducibility | Original creation timestamp and source module are always available |
| Error Analysis | Mispredictions can be traced to the reasoning or debate session that produced them |
| Impact Assessment | Descendant traversal reveals which downstream entries are affected by an upstream change |
| Consolidation Transparency | Merged entries clearly indicate their parent sources |

---

## 11. Lineage Merging Rules

| Source A | Source B | Merged Result |
|---|---|---|
| `parent_ids: [a]` | `parent_ids: [b]` | `parent_ids: [a, b]` |
| `module_chain: [m1, m2]` | `module_chain: [m1, m3]` | `module_chain: [m1, m2, m3, "consolidation"]` |
| `reasoning_id: r1` | `reasoning_id: r2` | `reasoning_id: r1` (first non-None wins) |
| `debate_id: d1` | `debate_id: None` | `debate_id: d1` (first non-None wins) |
| `created_by: "agent_a"` | `created_by: "agent_b"` | `created_by: "consolidator"` |

---

## 12. Serialization

```python
lineage = MemoryLineage(
    created_by="pipeline",
    created_at=datetime(2026, 7, 21, 10, 0, 0),
    parent_ids=["mem_001"],
    module_chain=["perception"],
    reasoning_id=None,
    debate_id=None,
)

lineage.to_dict()
# Returns:
# {
#     "created_by": "pipeline",
#     "created_at": "2026-07-21T10:00:00",
#     "parent_ids": ["mem_001"],
#     "module_chain": ["perception"],
#     "reasoning_id": None,
#     "debate_id": None,
# }
```

---

## 13. References

- Architecture: `MEMORY_ARCHITECTURE.md`
- Versioning: `MEMORY_VERSIONING.md`
- Consolidation: `MEMORY_CONSOLIDATION.md`
- Audit: `AUDIT_SYSTEM.md`
- Interface source: `interfaces.py:24-41`
