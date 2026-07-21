# Audit System — Immutable Action Logging for Cognitive Memory

---

## 1. Overview

The Audit System provides a complete, immutable log of every action performed on the CMS — storage, retrieval, updates, deletions, consolidation, and forgetting events. Each audit entry records the timestamp, affected memory ID, action type, originating module, and a free-text details field. The audit log is append-only and never cleared by default, ensuring a permanent record for debugging, explainability, and compliance.

---

## 2. Architecture

```
MemoryAudit (ABC, interfaces.py:231)
  |
  +-- log_access(memory_id, action, module, details) -> None
  +-- get_history(memory_id) -> list[dict]
  +-- get_recent_actions(limit) -> list[dict]
  |
  +-- DefaultMemoryAudit (implementation)
        +-- _log: list[AuditEntry]
        +-- _lock: threading.Lock
        +-- _by_memory_id: dict[str, list[AuditEntry]]

AuditEntry (internal dataclass):
  +-- timestamp: datetime
  +-- memory_id: str
  +-- action: str
  +-- module: str
  +-- details: str
```

---

## 3. Audit Entry Schema

```python
@dataclass
class AuditEntry:
    timestamp: datetime     # When the action occurred
    memory_id: str           # Affected memory (or "search", "consolidation" for bulk ops)
    action: str              # Action type (see below)
    module: str              # Module that performed the action
    details: str             # Free-text details
```

### Actions Logged

| Action | Trigger | Details Example |
|---|---|---|
| `store` | Entry stored | `"type=episodic, tags=[python, install], source=prediction_pipeline"` |
| `retrieve` | Entry retrieved by ID | `"memory_id=mem_001"` |
| `search` | Query executed | `"query_type=hybrid, types=[episodic], text=python"` |
| `update` | Entry content updated | `"updated decision from duplicate to non_duplicate"` |
| `delete` | Entry soft or hard deleted | `"soft_delete=true, source=user_request"` |
| `consolidate` | Entries merged | `"merged mem_001, mem_004, mem_007 into mem_012"` |
| `forget` | Entry archived or purged | `"archived mem_015 (age=120d, quality=0.25)"` |
| `restore` | Archived entry restored | `"restored mem_015 from archived"` |
| `index` | Index rebuilt | `"rebuilt index with 234 entries"` |

---

## 4. DefaultMemoryAudit Implementation

```python
class DefaultMemoryAudit(MemoryAudit):
    def __init__(self) -> None:
        self._log: list[AuditEntry] = []
        self._by_memory_id: dict[str, list[AuditEntry]] = {}
        self._lock = threading.Lock()
        self._never_clear = True  # Audit log is never cleared by default

    def log_access(self, memory_id: str, action: str, module: str, details: str = "") -> None:
        entry = AuditEntry(
            timestamp=datetime.now(),
            memory_id=memory_id,
            action=action,
            module=module,
            details=details,
        )
        with self._lock:
            self._log.append(entry)
            if memory_id not in ("search", "consolidation", "index"):
                self._by_memory_id.setdefault(memory_id, []).append(entry)

    def get_history(self, memory_id: str) -> list[dict]:
        with self._lock:
            entries = self._by_memory_id.get(memory_id, [])
            return [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "memory_id": e.memory_id,
                    "action": e.action,
                    "module": e.module,
                    "details": e.details,
                }
                for e in entries
            ]

    def get_recent_actions(self, limit: int = 100) -> list[dict]:
        with self._lock:
            recent = self._log[-limit:]
            return [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "memory_id": e.memory_id,
                    "action": e.action,
                    "module": e.module,
                    "details": e.details,
                }
                for e in recent
            ]

    def get_statistics(self) -> dict:
        with self._lock:
            action_counts = {}
            module_counts = {}
            for entry in self._log:
                action_counts[entry.action] = action_counts.get(entry.action, 0) + 1
                module_counts[entry.module] = module_counts.get(entry.module, 0) + 1
            return {
                "total_events": len(self._log),
                "unique_memories": len(self._by_memory_id),
                "action_counts": action_counts,
                "module_counts": module_counts,
            }
```

---

## 5. Audit Retrieval

### By Memory ID

```python
# Get all audit events for a specific memory
history = engine.get_audit_history("mem_001")
for event in history:
    print(f"{event['timestamp']} | {event['action']:12} | {event['module']:20} | {event['details']}")
# Output:
# 2026-07-21T10:00:00 | store        | prediction_pipeline   | type=episodic ...
# 2026-07-21T10:00:05 | update       | consolidator          | merged from ...
# 2026-07-21T10:00:10 | retrieve     | retrieval_engine      | memory_id=mem_001
```

### Recent Actions

```python
# Get the 10 most recent audit events
recent = engine.get_recent_actions(limit=10)
for event in recent:
    print(f"{event['timestamp']} | {event['action']:12} | {event['module']}")
```

### Audit Statistics

```python
stats = engine._audit.get_statistics()
print(f"Total audit events: {stats['total_events']}")
print(f"Unique memories tracked: {stats['unique_memories']}")
print(f"Actions: {stats['action_counts']}")
print(f"Modules: {stats['module_counts']}")
# Output:
# Total audit events: 1247
# Unique memories tracked: 893
# Actions: {'store': 500, 'retrieve': 400, 'search': 200, ...}
# Modules: {'prediction_pipeline': 500, 'retrieval_engine': 400, ...}
```

---

## 6. Integration with Memory Pipeline

The audit system is integrated at every point in the CMS pipeline:

```python
# Store pipeline
def store(self, ...):
    ...
    if self.config.enable_audit:
        self.audit.log_access(
            memory_id=result.memory_id,
            action="store",
            module=source_module,
            details=f"type={memory_type.value}, tags={tags}",
        )

# Retrieve pipeline
def retrieve(self, memory_id):
    if self.config.enable_audit:
        self.audit.log_access(memory_id, "retrieve", "MemoryEngine")
    return self.store.retrieve(memory_id)

# Search pipeline
def search(self, query):
    if self.config.enable_audit:
        self.audit.log_access(
            memory_id="search",
            action="search",
            module="MemoryEngine",
            details=f"query_type={query.query_type}, types={[t.value for t in query.memory_types] if query.memory_types else 'all'}, text='{query.text}'",
        )
    ...
```

---

## 7. Thread Safety

The `DefaultMemoryAudit` uses `threading.Lock` to ensure that concurrent `log_access()` calls do not corrupt the audit log:

```python
def log_access(self, ...):
    entry = AuditEntry(...)
    with self._lock:        # Serializes appends
        self._log.append(entry)
        self._by_memory_id.setdefault(memory_id, []).append(entry)
```

---

## 8. Never-Cleared Policy

By default, the audit log is never cleared. This design decision reflects the principle that audit data is essential for:

| Purpose | Why Never Clear |
|---|---|
| Explainability | Every decision can be traced through its audit trail |
| Debugging | Historical actions reveal how the system reached its current state |
| Compliance | Research systems require complete action logs |
| Scientific Reproducibility | Full action history enables exact reproduction of system behavior |

If memory pressure becomes a concern, the audit log can be explicitly cleared or truncated via a dedicated method (not exposed through the standard `MemoryEngine` API).

---

## 9. Examples

### Example 1: Full Trace for a Memory Entry

```python
# Store
engine.store(memory_type=MemoryType.EPISODIC, content=..., source_module="pipeline")
# Audit: "store | pipeline | type=episodic"

# Retrieve (twice)
engine.retrieve("mem_001")
engine.retrieve("mem_001")
# Audit: "retrieve | MemoryEngine | memory_id=mem_001" (x2)

# Update
engine.update("mem_001", content={"decision": "duplicate"})
# Audit: "update | MemoryEngine | updated decision"

# Consolidate
engine.consolidate()
# Audit: "consolidate | consolidator | merged mem_001, mem_004 into mem_012"

# Forget
engine.forget()
# Audit: "forget | forgetting_engine | archived mem_015 (age=120d, quality=0.25)"
```

### Example 2: Audit Query for Debugging

```python
def diagnose_memory(memory_id, engine):
    history = engine.get_audit_history(memory_id)
    print(f"Diagnostic for {memory_id}:")
    print(f"  Total events: {len(history)}")
    print(f"  Created: {history[0]['timestamp']} by {history[0]['module']}")
    print(f"  Last action: {history[-1]['action']} at {history[-1]['timestamp']}")
    updates = [h for h in history if h['action'] == 'update']
    print(f"  Updates: {len(updates)}")
    accesses = [h for h in history if h['action'] == 'retrieve']
    print(f"  Retrieves: {len(accesses)}")
```

---

## 10. Limitations

- Audit log is in-memory only (lost on process restart)
- No auditing of which user/session performed the action (single-process assumption)
- No filtering or search within audit entries (only retrieval by memory_id or recency)
- No audit log export or serialization
- Potential memory growth for long-running systems with many actions

---

## 11. References

- Architecture: `MEMORY_ARCHITECTURE.md`
- MemoryEngine integration: `MEMORY_ENGINE.md`
- Versioning (related immutable history): `MEMORY_VERSIONING.md`
- Lineage (related provenance): `MEMORY_LINEAGE.md`
