# Memory Architecture — ARES Cognitive Memory System

**Version:** 2.0
**Status:** Architecture Specification (CMS Phase 6)

---

## Abstract

This document provides the complete architecture specification for the ARES Cognitive Memory System (CMS), a deterministic in-memory long-term memory architecture for the ARES duplicate question NLP pipeline. The CMS is organized into ten interacting subsystems: MemoryEngine, MemoryStore, MemoryIndex, RetrievalEngine, Consolidator, Versioning, Audit, Forgetting, KnowledgeGraph, and Plugin system. Each subsystem is defined by an abstract interface contract, with default implementations provided. The architecture employs dependency injection, a layered plugin system, and thread-safe operations throughout.

---

## 1. Full System Architecture

```
                            CMS COMPONENT ARCHITECTURE
  =====================================================================

                            +-------------------------+
                            |     MemoryEngine        |  (Orchestrator)
                            |  - store()              |
                            |  - retrieve()           |
                            |  - search()             |
                            |  - get_statistics()     |
                            +-----------+-------------+
                                        |
              +-------------------------+-------------------------+
              |                 |                 |                |
              v                 v                 v                v
     +--------+----+   +-------+--------+   +----+--------+   +---+----------+
     | MemoryConfig|   | MemoryStore    |   | MemoryIndex  |   | MemoryAudit  |
     | - thresholds|   | - store()      |   | - index()    |   | - log_access |
     | - limits    |   | - retrieve()   |   | - search()   |   | - get_history|
     | - flags     |   | - update()     |   | - remove()   |   | - recent()   |
     +-------------+   | - delete()     |   +-------+------+   +------+-------+
                       | - list_all()   |           |                  |
                       +-------+--------+           |                  |
                               |                    |                  |
              +----------------+    +---------------+                  |
              |                     |                                  |
              v                     v                                  v
     +--------+----+   +-----------+--------+   +--------------------+
     | MemoryVersion|  | RetrievalEngine     |   | MemoryPlugin       |
     | - create()   |  | - retrieve()        |   | - before_store()   |
     | - history()  |  |   (from store)      |   | - after_retrieve() |
     +------+-------+  |   (filter via index) |   +--------------------+
            |          |   (rank via ranker)   |
            |          +-----------+-----------+
            |                      |
            v                      v
     +------+-------+   +---------+-----------+
     | MemoryLineage |   | RetrievalRanker    |
     | - created_by  |   | - RecencyRanker    |
     | - parent_ids  |   | - ConfidenceRanker |
     | - module_chain|   | - QualityRanker    |
     +------+-------+   | - FrequencyRanker   |
            |           | - CompositeRanker   |
            v           +--------------------+
     +------+-------+
     | Consolidator |
     | - find_dup() |
     | - merge()    |
     +------+-------+
            |
            v
     +------+-------+
     | Forgetting   |
     | - age policy |
     | - quality    |
     | - duplicate  |
     +------+-------+
            |
            v
     +------+-------+
     | QualityScorer|
     +--------------+
            |
            v
     +------+-------+
     |KnowledgeGraph|
     | - nodes      |
     | - edges      |
     | - traverse   |
     +--------------+
```

---

## 2. Layer Descriptions

### 2.1 MemoryEngine (Orchestrator)

The `MemoryEngine` is the primary public API for the CMS. It coordinates all subsystem interactions, manages the store pipeline, and provides unified error handling.

**Responsibilities:**
- Validate incoming entries via `MemoryValidator`
- Apply plugins via `MemoryPluginRegistry`
- Create versions via `MemoryVersioning`
- Store entries via `MemoryStore`
- Index entries via `MemoryIndex`
- Log all actions via `MemoryAudit`
- Route retrieval and search through `RetrievalEngine`
- Manage consolidation, forgetting, and statistics

### 2.2 MemoryStore (Persistence Layer)

The `MemoryStore` ABC (`interfaces.py:137`) defines the persistence contract. The `InMemoryMemoryStore` implementation uses a thread-safe `dict[str, MemoryEntry]` with a `threading.Lock`.

**Contract:**

| Method | Signature | Description |
|---|---|---|
| `store` | `(entry: MemoryEntry) -> str` | Persist entry, return memory_id |
| `retrieve` | `(memory_id: str) -> MemoryEntry | None` | Get entry by ID |
| `update` | `(entry: MemoryEntry) -> str` | Replace entry, increment version |
| `delete` | `(memory_id: str, soft: bool) -> bool` | Soft or hard delete |
| `list_by_type` | `(type, limit, offset) -> tuple[list, int]` | Paginated type query |
| `list_all` | `(limit, offset) -> tuple[list, int]` | Paginated full listing |
| `count` | `() -> int` | Active entry count |
| `clear` | `() -> None` | Remove all entries |

### 2.3 MemoryIndex (Index Layer)

The `MemoryIndex` ABC (`interfaces.py:171`) defines the indexing contract. `DefaultMemoryIndex` maintains five internal indices:

- `_by_type: dict[str, set[str]]` — type to ID mapping
- `_by_tag: dict[str, set[str]]` — tag to ID mapping
- `_by_source: dict[str, set[str]]` — source module to ID mapping
- `_quality_map: dict[str, float]` — ID to quality score
- `_confidence_map: dict[str, float]` — ID to confidence score

Search filters intersect candidate sets from type, tag, source, confidence, and quality filters, then applies text matching (`_text_match`) and metadata/content filter checks.

### 2.4 RetrievalEngine (Query Layer)

The `RetrievalEngine` ABC (`interfaces.py:189`) defines the query contract. The `DefaultRetrievalEngine` (specified in detail in `RETRIEVAL_ENGINE.md`) supports exact, tagged, confidence, text, and hybrid queries via `MemoryQuery`.

### 2.5 Consolidator (Maintenance Layer)

The `MemoryConsolidator` ABC (`interfaces.py:201`) defines duplicate detection and merging. Operations are invoked periodically or on demand.

### 2.6 Versioning (History Layer)

The `MemoryVersioning` ABC (`interfaces.py:211`) manages version creation and history retrieval. Versions are immutable; each update creates a new version record.

### 2.7 Audit (Observability Layer)

The `MemoryAudit` ABC (`interfaces.py:231`) logs every access and modification event. The audit log is append-only and never cleared by default.

### 2.8 ForgettingEngine (Lifecycle Layer)

The `ForgettingEngine` ABC (`interfaces.py:221`) applies age, quality, and duplicate policies to archive or remove stale entries.

### 2.9 KnowledgeGraph (Semantic Layer)

The `KnowledgeGraph` stores semantic relationships between concepts extracted from memory entries. It supports node/edge CRUD, neighbor traversal, and label/type-based search.

### 2.10 Plugin System (Extension Layer)

The `MemoryPlugin` ABC (`interfaces.py:255`) defines two hooks:

- `process_before_store(entry) -> entry` — transform or enrich entries before storage
- `process_after_retrieve(entry) -> entry` — transform or filter entries after retrieval

Plugins are registered via `MemoryPluginRegistry` and execute in registration order.

---

## 3. Interface Contracts

### 3.1 Core Dataclasses

| Dataclass | Defined In | Key Fields |
|---|---|---|
| `MemoryEntry` | `interfaces.py:44` | `memory_id`, `memory_type`, `version`, `timestamp`, `source_module`, `quality_score`, `confidence`, `lineage`, `tags`, `metadata`, `content`, `embedding`, `expires_at`, `status` |
| `MemoryLineage` | `interfaces.py:24` | `created_by`, `created_at`, `parent_ids`, `module_chain`, `reasoning_id`, `debate_id` |
| `MemoryQuery` | `interfaces.py:80` | `query_type`, `memory_types`, `tags`, `source_modules`, `min_confidence`, `min_quality`, `text`, `filters`, `limit`, `offset` |
| `MemoryResult` | `interfaces.py:108` | `entries`, `total_count`, `query_time_ms`, `query` |
| `MemoryStatistics` | `interfaces.py:124` | `total_entries`, `total_by_type`, `total_size_bytes`, `avg_quality`, `avg_confidence`, `oldest_entry`, `newest_entry`, `version_count`, `deleted_count` |
| `MemoryConfig` | `memory_configuration.py:8` | `max_entries`, `max_versions`, `default_ttl_days`, `enable_consolidation`, `enable_audit`, `enable_forgetting`, `auto_consolidate_interval`, `aging_threshold_days`, `quality_threshold`, `confidence_threshold`, `store_type` |

### 3.2 Result Types

| Result | Defined In | Key Fields |
|---|---|---|
| `StoreResult` | `memory_result.py:10` | `memory_id`, `success`, `version`, `message` |
| `DeleteResult` | `memory_result.py:26` | `memory_id`, `success`, `soft_deleted`, `message` |
| `ConsolidationResult` | `memory_result.py:42` | `merged_ids`, `new_entry`, `summary` |

### 3.3 Enums

| Enum | Values | Defined In |
|---|---|---|
| `MemoryType` | `EPISODIC`, `SEMANTIC`, `REASONING`, `DEBATE`, `PERFORMANCE` | `interfaces.py:10` |
| `MemoryStatus` | `ACTIVE`, `ARCHIVED`, `DELETED` | `interfaces.py:18` |
| `QueryType` | (string field) `"exact"`, `"semantic"`, `"hybrid"`, `"graph"`, `"similarity"` | `MemoryQuery.query_type` |

---

## 4. Dependency Injection Design

The CMS uses constructor-based dependency injection. Each component receives its dependencies at initialization rather than creating them internally.

```
MemoryEngine(
    store=InMemoryMemoryStore(),
    index=DefaultMemoryIndex(),
    versioning=DefaultMemoryVersioning(config),
    audit=DefaultMemoryAudit(),
    consolidator=DefaultMemoryConsolidator(),
    forgetting=DefaultForgettingEngine(config),
    validator=DefaultMemoryValidator(),
    plugin_registry=MemoryPluginRegistry(),
    ranker=CompositeRanker(),
    config=MemoryConfig(),
)
```

This design enables:
- **Testing**: Substitute mock implementations for any component
- **Extensibility**: Replace any subsystem without modifying others
- **Isolation**: Component failures are contained within their subsystem

---

## 5. Plugin Architecture

```
MemoryPlugin (ABC)
    |
    +-- process_before_store(entry) -> entry
    +-- process_after_retrieve(entry) -> entry | None

MemoryPluginRegistry
    |
    +-- register(plugin)
    +-- get_plugins() -> list[MemoryPlugin]
    +-- process_before_store(entry) -> entry  (chains all plugins)
    +-- process_after_retrieve(entry) -> entry (chains all plugins)
```

Plugins execute in registration order during the store and retrieve pipelines. The default plugin (`DefaultMemoryPlugin` in `plugins/__init__.py:6`) acts as a no-op pass-through.

---

## 6. Configuration System

The `MemoryConfig` dataclass (`memory_configuration.py:8`) centralizes all CMS configuration:

| Parameter | Default | Range | Description |
|---|---|---|---|
| `max_entries` | 10000 | [1, inf) | Maximum active entries |
| `max_versions` | 10 | [1, inf) | Maximum version history per entry |
| `default_ttl_days` | 365 | [1, inf) | Default TTL for new entries |
| `enable_consolidation` | True | bool | Enable automatic consolidation |
| `enable_audit` | True | bool | Enable audit logging |
| `enable_forgetting` | True | bool | Enable forgetting policies |
| `auto_consolidate_interval` | 1000 | [1, inf) | Stores between consolidation runs |
| `aging_threshold_days` | 90 | [1, inf) | Age threshold for forgetting |
| `quality_threshold` | 0.3 | [0.0, 1.0] | Min quality to avoid forgetting |
| `confidence_threshold` | 0.2 | [0.0, 1.0] | Min confidence to avoid forgetting |
| `store_type` | "in_memory" | str | Store implementation selector |

Configuration is loaded via `MemoryConfigLoader` (`memory_configuration.py:22`), which supports `load_default()` and `from_dict()`.

---

## 7. Thread Safety Model

All mutable state in the CMS is protected by `threading.Lock`:

| Component | Lock Scope | Granularity |
|---|---|---|
| `InMemoryMemoryStore` | Per-instance `_lock` | Method-level |
| `DefaultMemoryIndex` | None (read-only after init) | N/A |
| `DefaultMemoryAudit` | Per-instance `_lock` | Append-level |

The `MemoryEngine` does not introduce additional locks; it delegates to locked store methods. Concurrent `store()` calls are serialized at the store level. Reads (`retrieve`, `search`) acquire the same lock, ensuring consistent snapshots.

---

## 8. Memory Lifecycle

```
                              MEMORY LIFECYCLE
  =====================================================================

     +---------+
     |  Input  |
     +----+----+
          |
          v
     +---------+       +---------+       +---------+       +---------+
     | Validate| ----> | Plugin  | ----> | Version | ----> |  Store  |
     +---------+       +---------+       +---------+       +----+----+
          |                                                   |
          +---------------------------------------------------+
                                                              |
                                                              v
          +---------+       +---------+       +---------+
          | Forget  | <---- | Archive | <---- |  Index  |
          +----+----+       +---------+       +----+----+
               |                                   |
               v                                   v
          +---------+       +---------+       +---------+
          |  Purge  |       | Retrieve| <---- |  Query  |
          +---------+       +----+----+       +---------+
                                |
                                v
                          +---------+       +---------+       +---------+
                          |  Rank   | ----> | Return  | ----> |  Audit  |
                          +---------+       +---------+       +---------+

     Consolidation Loop:  Store --> Find Duplicates --> Merge --> Soft Delete
     Versioning:           Update --> Increment Version --> Store New Version
     Forgetting:           Timer/Trigger --> Age Check --> Quality Check --> Archive
```

### Lifecycle Phases

1. **Create**: `MemoryEntry` constructed with initial fields, version = 1
2. **Validate**: Schema and bounds checks via `DefaultMemoryValidator`
3. **Plugin**: Pre-store transformations via registered plugins
4. **Version**: Initial version assignment or version increment
5. **Store**: Persist to `InMemoryMemoryStore`
6. **Index**: Update tag, type, source indices
7. **Retrieve**: Query via `MemoryQuery`, filter via index, rank via `RetrievalRanker`
8. **Update**: Load, modify, re-store with version increment
9. **Version**: Previous version preserved in history
10. **Consolidate**: Duplicate detection, merge, soft delete originals
11. **Archive**: Status change to `ARCHIVED` via forgetting policies
12. **Forget**: Age, quality, or duplicate policy removes entry

---

## 9. Extension Points

| Extension Point | Interface | Mechanism |
|---|---|---|
| Custom Store Backend | `MemoryStore` | Implement ABC, inject into `MemoryEngine` |
| Custom Index Strategy | `MemoryIndex` | Implement ABC, inject into `MemoryEngine` |
| Custom Retrieval Strategy | `RetrievalEngine` | Implement ABC, inject into `MemoryEngine` |
| Custom Ranking Strategy | `RetrievalRanker` | Implement ABC, inject into `RetrievalEngine` |
| Custom Consolidation | `MemoryConsolidator` | Implement ABC, inject into `MemoryEngine` |
| Custom Versioning | `MemoryVersioning` | Implement ABC, inject into `MemoryEngine` |
| Custom Forgetting | `ForgettingEngine` | Implement ABC, inject into `MemoryEngine` |
| Custom Audit | `MemoryAudit` | Implement ABC, inject into `MemoryEngine` |
| Custom Validator | `MemoryValidator` | Implement ABC, inject into `MemoryEngine` |
| Store/Retrieve Plugins | `MemoryPlugin` | Register via `MemoryPluginRegistry` |
| New Memory Types | `MemoryType` enum | Add enum member, define content schema |

---

## 10. Serialization

All core dataclasses implement `to_dict()` methods for serialization:

| Class | `to_dict()` Coverage | Deserialization |
|---|---|---|
| `MemoryEntry` | All fields, nested `lineage.to_dict()` | `MemoryDeserializer.deserialize()` |
| `MemoryLineage` | All fields with ISO timestamps | `MemoryDeserializer` (nested) |
| `MemoryQuery` | All fields with type/value conversion | Constructor |
| `MemoryResult` | Nested entries and query | `MemoryDeserializer` |
| `StoreResult` | All fields | Constructor |
| `DeleteResult` | All fields | Constructor |
| `ConsolidationResult` | Merged IDs, new entry, summary | Constructor |

---

## 11. References

- System overview: `COGNITIVE_MEMORY_SYSTEM.md`
- Engine implementation: `MEMORY_ENGINE.md`
- Type specifications: `MEMORY_TYPES.md`
- Versioning: `MEMORY_VERSIONING.md`
- Lineage: `MEMORY_LINEAGE.md`
- Knowledge graph: `KNOWLEDGE_GRAPH.md`
- Retrieval: `RETRIEVAL_ENGINE.md`
- Consolidation: `MEMORY_CONSOLIDATION.md`
- Forgetting: `FORGETTING_POLICY.md`
- Quality scoring: `QUALITY_SCORING.md`
- Audit: `AUDIT_SYSTEM.md`
- Benchmarks: `PERFORMANCE_BENCHMARKS.md`
- Research: `docs/research/PHASE6_RESEARCH_SUMMARY.md`
