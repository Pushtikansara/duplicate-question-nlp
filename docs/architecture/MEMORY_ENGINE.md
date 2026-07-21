# MemoryEngine — Orchestration Deep Dive

---

## 1. Overview

The `MemoryEngine` is the central orchestrator of the ARES Cognitive Memory System. It provides a unified public API for all memory operations — store, retrieve, search, update, delete, consolidate, forget, and statistics — while coordinating the interactions between validation, plugins, versioning, store, index, audit, and ranking subsystems.

---

## 2. Architecture

```
MemoryEngine
  |
  +-- store(entry) -> StoreResult
  +-- retrieve(memory_id) -> MemoryEntry | None
  +-- search(query) -> MemoryResult
  +-- update(memory_id, content_modifications) -> StoreResult
  +-- delete(memory_id) -> DeleteResult
  +-- consolidate() -> ConsolidationResult | None
  +-- forget() -> list[str]
  +-- get_statistics() -> MemoryStatistics
  +-- get_audit_history(memory_id) -> list[dict]
  +-- get_recent_actions(limit) -> list[dict]
  +-- get_version_history(memory_id) -> list[MemoryEntry]
  |
  +-- Dependencies (injected):
       store: MemoryStore
       index: MemoryIndex
       versioning: MemoryVersioning
       audit: MemoryAudit
       consolidator: MemoryConsolidator
       forgetting: ForgettingEngine
       validator: MemoryValidator
       plugin_registry: MemoryPluginRegistry
       ranker: RetrievalRanker
       config: MemoryConfig
```

---

## 3. Store Pipeline

```
store(entry)
  |
  +-> 1. VALIDATE
  |      validator.validate(entry)
  |      If invalid: raise ValueError with error messages
  |
  +-> 2. PLUGIN (PRE)
  |      plugin_registry.process_before_store(entry)
  |      Each registered plugin transforms the entry in order
  |
  +-> 3. VERSION
  |      versioning.create_version(entry)
  |      Sets version = 1, generates memory_id if empty
  |
  +-> 4. STORE
  |      store.store(entry)
  |      Thread-safe persistence to in-memory dict
  |
  +-> 5. INDEX
  |      index.index_entry(entry)
  |      Updates type, tag, source, quality, confidence indices
  |
  +-> 6. AUDIT
  |      audit.log_access(entry.memory_id, "store", source_module)
  |
  +-> 7. CONSOLIDATION CHECK
  |      if config.enable_consolidation:
  |        increment store counter
  |        if counter >= config.auto_consolidate_interval:
  |          trigger consolidate()
  |
  +-> 8. RETURN
       StoreResult(memory_id=id, success=True, version=v, message="")
```

### Pseudocode

```
def store(self, memory_type, content, tags, source_module, confidence,
          lineage=None, metadata=None) -> StoreResult:
    entry = MemoryEntry(
        memory_id="",
        memory_type=memory_type,
        version=0,
        timestamp=datetime.now(),
        source_module=source_module,
        quality_score=QualityScorer.compute(entry),
        confidence=confidence,
        lineage=lineage or MemoryLineage(...),
        tags=tags,
        metadata=metadata or {},
        content=content,
    )

    is_valid, errors = self.validator.validate(entry)
    if not is_valid:
        raise ValueError(f"Validation failed: {errors}")

    entry = self.plugin_registry.process_before_store(entry)
    entry = self.versioning.create_version(entry)
    memory_id = self.store.store(entry)
    self.index.index_entry(entry)

    if self.config.enable_audit:
        self.audit.log_access(memory_id, "store", source_module)

    return StoreResult(memory_id=memory_id, success=True,
                       version=entry.version, message="Stored")
```

---

## 4. Retrieve Pipeline

```
retrieve(memory_id)
  |
  +-> 1. AUDIT
  |      audit.log_access(memory_id, "retrieve", "MemoryEngine")
  |
  +-> 2. RETRIEVE FROM STORE
  |      entry = store.retrieve(memory_id)
  |      If None: return None
  |
  +-> 3. PLUGIN (POST)
  |      plugin_registry.process_after_retrieve(entry)
  |
  +-> 4. RETURN
       entry
```

---

## 5. Search Pipeline

```
search(query)
  |
  +-> 1. AUDIT
  |      audit.log_access("search", "MemoryEngine")
  |
  +-> 2. INDEX SEARCH
  |      entries = index.search(query, store)
  |
  +-> 3. RANK
  |      ranked = ranker.rank(entries, query)
  |
  +-> 4. PAGINATE
  |      page = ranked[query.offset : query.offset + query.limit]
  |
  +-> 5. MEASURE
  |      query_time = elapsed_ms()
  |
  +-> 6. RETURN
       MemoryResult(entries=page, total_count=len(entries),
                    query_time_ms=query_time, query=query)
```

---

## 6. Update Pipeline

```
update(memory_id, new_content, new_tags=None, new_metadata=None, ...)
  |
  +-> 1. RETRIEVE EXISTING
  |      existing = store.retrieve(memory_id)
  |      If None: raise KeyError
  |
  +-> 2. MERGE FIELDS
  |      existing.content.update(new_content)
  |      if new_tags: existing.tags = new_tags
  |      if new_metadata: existing.metadata.update(new_metadata)
  |
  +-> 3. PRESERVE LINEAGE
  |      existing.lineage.parent_ids.append(memory_id)
  |
  +-> 4. REVALIDATE
  |      validator.validate(existing)
  |
  +-> 5. STORE (increments version)
  |      store.update(existing)
  |
  +-> 6. REINDEX
  |      index.index_entry(existing)
  |
  +-> 7. AUDIT
  |      audit.log_access(memory_id, "update", source_module)
  |
  +-> 8. RETURN
       StoreResult(...)
```

---

## 7. Public Methods — Complete Signatures

```python
class MemoryEngine:
    def __init__(
        self,
        store: MemoryStore = InMemoryMemoryStore(),
        index: MemoryIndex = DefaultMemoryIndex(),
        versioning: MemoryVersioning | None = None,
        audit: MemoryAudit | None = None,
        consolidator: MemoryConsolidator | None = None,
        forgetting: ForgettingEngine | None = None,
        validator: MemoryValidator = DefaultMemoryValidator(),
        plugin_registry: MemoryPluginRegistry | None = None,
        ranker: RetrievalRanker = CompositeRanker(),
        config: MemoryConfig | None = None,
    ) -> None: ...

    def store(
        self,
        memory_type: MemoryType,
        content: dict[str, Any],
        tags: list[str] | None = None,
        source_module: str = "",
        confidence: float = 1.0,
        lineage: MemoryLineage | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoreResult: ...

    def retrieve(self, memory_id: str) -> MemoryEntry | None: ...

    def search(self, query: MemoryQuery) -> MemoryResult: ...

    def update(
        self,
        memory_id: str,
        content: dict[str, Any],
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        source_module: str = "",
    ) -> StoreResult: ...

    def delete(self, memory_id: str) -> DeleteResult: ...

    def consolidate(self) -> ConsolidationResult | None: ...

    def forget(self) -> list[str]: ...

    def get_statistics(self) -> MemoryStatistics: ...

    def get_audit_history(self, memory_id: str) -> list[dict]: ...

    def get_recent_actions(self, limit: int = 100) -> list[dict]: ...

    def get_version_history(self, memory_id: str) -> list[MemoryEntry]: ...

    def add_plugin(self, plugin: MemoryPlugin) -> None: ...
```

---

## 8. Error Handling

| Error Condition | Raised | Handling |
|---|---|---|
| Invalid entry fields | `ValueError` | Validation errors listed in message |
| Missing memory_id on update | `KeyError` | "Memory {id} not found for update" |
| Store failure | `RuntimeError` | Propagated from store implementation |
| Plugin failure | `Exception` | Propagated (plugins should handle internally) |
| Query with invalid type | `ValueError` | Invalid memory_type in filter |

The `MemoryEngine` does not catch exceptions internally. Callers should handle exceptions at the pipeline boundary.

---

## 9. Configuration Options

See `MEMORY_ARCHITECTURE.md` Section 6 for full configuration reference. The `MemoryConfig` dataclass parameters that directly affect `MemoryEngine` behavior:

| Parameter | Effect on MemoryEngine |
|---|---|
| `enable_audit` | Controls whether audit logging occurs in store/retrieve pipelines |
| `enable_consolidation` | Controls the auto-consolidation trigger in the store pipeline |
| `enable_forgetting` | Controls whether `forget()` performs any action |
| `auto_consolidate_interval` | Number of store operations between automatic consolidation triggers |

---

## 10. Examples

### Storing an Episodic Memory

```python
engine = MemoryEngine()

result = engine.store(
    memory_type=MemoryType.EPISODIC,
    content={
        "question_a": "How to install Python?",
        "question_b": "How to install Python on Ubuntu?",
        "pipeline_used": "ares_pipeline_v2",
        "decision": "non_duplicate",
    },
    tags=["python", "installation", "ubuntu"],
    source_module="prediction_pipeline",
    confidence=0.87,
    lineage=MemoryLineage(
        created_by="prediction_pipeline",
        created_at=datetime.now(),
        module_chain=["perception", "reasoning", "debate"],
    ),
)
# result.memory_id -> "uuid-here"
# result.version -> 1
```

### Searching with a Query

```python
query = MemoryQueryBuilder.by_tags(["python", "installation"])
result = engine.search(query)
# result.entries -> [MemoryEntry, ...]
# result.total_count -> 5
# result.query_time_ms -> 0.45
```

### Hybrid Search

```python
query = MemoryQueryBuilder.hybrid(
    text="install python ubuntu",
    memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
)
result = engine.search(query)
```

---

## 11. Limitations

- Sequential pipeline: validation, plugin, version, store, index, audit execute in sequence
- No batch store: each `store()` call processes one entry
- No transactional rollback: if indexing fails after store, entry remains stored but unindexed
- Single-threaded orchestration: store lock serializes concurrent writes

---

## 12. References

- Architecture overview: `COGNITIVE_MEMORY_SYSTEM.md`
- Full architecture: `MEMORY_ARCHITECTURE.md`
- Type specifications: `MEMORY_TYPES.md`
- Versioning: `MEMORY_VERSIONING.md`
- Retrieval: `RETRIEVAL_ENGINE.md`
- Quality scoring: `QUALITY_SCORING.md`
