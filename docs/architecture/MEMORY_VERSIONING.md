# Memory Versioning — Immutable History for Cognitive Memory

---

## 1. Overview

The ARES CMS implements an append-only versioning system for memory entries. Every update to a memory entry creates a new version, preserving the full history of changes. Versioning ensures that the CMS maintains an immutable audit trail of how knowledge evolved over time, which is essential for scientific reproducibility and explainability.

---

## 2. Architecture

```
Versioning System
  |
  +-- MemoryVersioning (ABC, interfaces.py:211)
  |     +-- create_version(entry, parent_id) -> MemoryEntry
  |     +-- get_version_history(memory_id, store) -> list[MemoryEntry]
  |
  +-- DefaultMemoryVersioning (implementation)
        +-- _version_store: dict[str, list[MemoryEntry]]
        +-- _version_counter: dict[str, int]
```

The versioning system stores all versions in a separate `_version_store` dictionary, independent of the main `MemoryStore`. This ensures that version history is not affected by soft deletions of the active entry.

---

## 3. Design

### Version Rules

| Rule | Description | Rationale |
|---|---|---|
| Monotonically Increasing | Each new version increments by exactly 1 | Provides clear ordering of changes |
| Immutable History | Old versions are never modified or deleted | Preserves audit trail for explainability |
| Parent Tracking | Each version records its parent via lineage | Enables full provenance reconstruction |
| Max Versions | Configurable cap (`max_versions` in `MemoryConfig`) | Prevents unbounded memory growth |
| Version 1 = Initial | All entries start at version 1 | Consistent baseline |

### Version Flow

```
Initial Store:
  entry.version = 1
  _version_store[id] = [entry]
  entry stored in MemoryStore with version=1

First Update:
  existing.version += 1  (now version 2)
  _version_store[id].append(existing)
  existing stored in MemoryStore with version=2

Second Update:
  existing.version += 1  (now version 3)
  _version_store[id].append(existing)
  existing stored in MemoryStore with version=3

Max Versions Reached (e.g., max_versions=10):
  oldest version removed from _version_store[id]
  append new version
  _version_store[id] size = max_versions
```

### Thread Safety

The `DefaultMemoryVersioning` implementation maintains its own lock to ensure atomic version increments and consistent history appends.

---

## 4. Implementation Details

### create_version

```python
def create_version(self, entry: MemoryEntry, parent_id: str | None = None) -> MemoryEntry:
    with self._lock:
        if not entry.memory_id:
            entry.memory_id = str(uuid.uuid4())
            entry.version = 1
            self._init_version_history(entry)
        else:
            history = self._version_store.get(entry.memory_id, [])
            entry.version = len(history) + 1
            self._append_version(entry)
        return entry
```

### get_version_history

```python
def get_version_history(self, memory_id: str, store: MemoryStore) -> list[MemoryEntry]:
    with self._lock:
        history = list(self._version_store.get(memory_id, []))
        # Also include current version from store if not in history
        current = store.retrieve(memory_id)
        if current and (not history or current.version > history[-1].version):
            history.append(current)
        return sorted(history, key=lambda e: e.version)
```

### Version Enforcement

```python
# In InMemoryMemoryStore.update():
def update(self, entry: MemoryEntry) -> str:
    with self._lock:
        existing = self._store.get(entry.memory_id)
        if existing is None:
            raise KeyError(f"Memory {entry.memory_id} not found for update")
        entry.version = existing.version + 1  # Auto-increment
        entry.timestamp = datetime.now()      # Update timestamp
        self._store[entry.memory_id] = entry
        return entry.memory_id
```

---

## 5. Configuration

| Parameter | Default | Description |
|---|---|---|
| `max_versions` | 10 | Maximum versions retained per memory entry |

When the version history exceeds `max_versions`, the oldest version is removed from the version store. The current version in `MemoryStore` is always preserved.

---

## 6. Examples

### Initial Store

```python
entry = MemoryEntry(
    memory_id="mem_001",
    memory_type=MemoryType.EPISODIC,
    version=0,
    content={"question_a": "What is Python?", "decision": "N/A"},
    ...
)

entry = versioning.create_version(entry)
# entry.version == 1
# _version_store["mem_001"] == [entry_v1]
```

### Update (New Version)

```python
# After prediction completes, update the entry
entry.content["decision"] = "non_duplicate"
entry.content["confidence"] = 0.87

updated = store.update(entry)
versioning.create_version(updated)
# updated.version == 2
# _version_store["mem_001"] == [entry_v1, entry_v2]
```

### Version History Retrieval

```python
history = versioning.get_version_history("mem_001", store)
for v in history:
    print(f"Version {v.version}: {v.timestamp} - {v.content.get('decision')}")
# Output:
#   Version 1: 2026-07-21T10:00:00 - N/A
#   Version 2: 2026-07-21T10:00:05 - non_duplicate
```

---

## 7. Design Rationale

### Append-Only, Immutable History

The decision to make version history append-only and immutable is grounded in the following requirements:

| Requirement | How Versioning Supports It |
|---|---|
| Scientific Reproducibility | Every state of every memory entry is recoverable |
| Audit Compliance | No information is ever destroyed, only superseded |
| Error Recovery | Mistakes can be reverted by retrieving prior versions |
| Explainability | The evolution of a memory can be traced over time |
| Lineage Integrity | Parent references point to specific versions |

### Why Not In-Place Updates

In-place updates (modifying the entry without preserving history) would make the CMS unsuitable for research applications where provenance matters. The append-only design adds negligible overhead (one dictionary append per update) while providing substantial audit benefits.

---

## 8. Limitations

- Version history is in-memory only (lost on process restart)
- Max versions enforcement discards oldest versions, not smart (no importance-based retention)
- No branching support (git-like branching/merging across versions)
- No diff/change summary tracking beyond what metadata provides

---

## 9. References

- Architecture overview: `MEMORY_ARCHITECTURE.md`
- Lineage tracking: `MEMORY_LINEAGE.md`
- Audit system: `AUDIT_SYSTEM.md`
- Consolidation (version impacts): `MEMORY_CONSOLIDATION.md`
