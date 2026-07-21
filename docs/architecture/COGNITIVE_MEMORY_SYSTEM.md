# ARES Cognitive Memory System — Executive Overview

**Version:** 1.0
**Status:** Architecture Specification

---

## Abstract

The ARES Cognitive Memory System (CMS) is a deterministic, in-memory long-term cognitive memory architecture designed to store, retrieve, consolidate, version, and audit structured knowledge produced by the ARES duplicate question NLP pipeline. CMS provides five specialized memory types — Episodic, Semantic, Reasoning, Debate, and Performance — each capturing a distinct dimension of the system's knowledge about question pair evaluation. The architecture emphasizes explainability (via full lineage and audit trails), quality-aware retrieval (via composite quality scoring), and deterministic behavior (no LLM dependencies, no external database wrappers). This document provides an executive overview of the CMS architecture, design rationale, and integration points within the ARES pipeline.

---

## 1. Why Cognitive Memory for ARES

The ARES duplicate question NLP pipeline processes question pairs through multiple analytical stages: perception, linguistic analysis, multi-model inference, reasoning, multi-agent debate, and final decision. Each stage produces structured knowledge — predictions, confidence scores, reasoning chains, agent votes, and performance metrics — that is valuable beyond a single inference cycle.

CMS addresses five fundamental requirements:

| Requirement | Problem | CMS Solution |
|---|---|---|
| Persistent Knowledge | Each inference is stateless; no knowledge accumulates across requests | Five specialized memory types with versioned storage |
| Explainability | Decisions lack traceable provenance | Full lineage tracking with parent IDs, module chains, and audit logs |
| Auditability | No record of what decisions were made or why | Immutable audit log with every access, modification, and consolidation event recorded |
| Cross-Request Learning | Patterns across requests cannot be exploited | Quality scoring and consolidation enable knowledge accumulation |
| Performance Analysis | Bottlenecks and routing decisions are invisible | Performance memory captures latency, cost, and routing per request |

CMS is **not** a cache (it is long-term, quality-scored, and consolidated), **not** a vector database (it stores structured memory entries, not just embeddings), **not** an LLM memory system (it is fully deterministic), and **not** a graph database (the KnowledgeGraph is one component of a broader memory architecture).

---

## 2. System Architecture

```
                            ARES COGNITIVE MEMORY SYSTEM
  =====================================================================

                              +-------------------+
                              |   MemoryEngine    |  (Orchestrator)
                              +--------+----------+
                                       |
              +------------------------+------------------------+
              |                        |                        |
              v                        v                        v
     +----------------+     +------------------+     +------------------+
     |  MemoryConfig  |     |  MemoryStore     |     |  MemoryIndex     |
     |  (settings)    |     |  (in-memory)     |     |  (tag/type/src)  |
     +----------------+     +--------+---------+     +--------+---------+
                                       |                        |
              +------------------------+------------------------+
              |                        |                        |
              v                        v                        v
     +----------------+     +------------------+     +------------------+
     |  MemoryAudit   |     |  MemoryVersion   |     |  KnowledgeGraph  |
     |  (logging)     |     |  (versioning)     |     |  (semantic rel)  |
     +----------------+     +--------+---------+     +--------+---------+
                                       |                        |
              +------------------------+------------------------+
              |                        |                        |
              v                        v                        v
     +----------------+     +------------------+     +------------------+
     |  Consolidator  |     | ForgettingEngine  |     | QualityScorer   |
     |  (merge/dup)   |     | (age/quality/dup) |     | (composite)     |
     +----------------+     +------------------+     +------------------+
                                       |
              +------------------------+
              |
              v
     +------------------+
     | RetrievalEngine  |
     | + RetrievalRanker|
     | (recency/conf/   |
     |  quality/freq/   |
     |  composite)      |
     +------------------+
                                       |
              +------------------------+
              |
              v
     +------------------+
     | MemoryPlugin     |
     | (before_store/   |
     |  after_retrieve) |
     +------------------+
```

---

## 3. Five Memory Types

| Type | Enum Value | Purpose | Content Fields |
|---|---|---|---|
| Episodic | `MemoryType.EPISODIC` | Stores question pairs, timestamps, pipeline used, decision, confidence | `question_a`, `question_b`, `pipeline_used`, `decision` |
| Semantic | `MemoryType.SEMANTIC` | Stores concepts, entities, relations, intent patterns, semantic graphs | `concepts`, `entities`, `relations`, `intent_pattern` |
| Reasoning | `MemoryType.REASONING` | Stores reasoning graphs, premises, evidence chains, hypotheses, confidence chains | `reasoning_graph`, `premises`, `evidence_chains`, `hypotheses`, `confidence_chain`, `reasoning_trace` |
| Debate | `MemoryType.DEBATE` | Stores agent results, votes, conflicts, consensus, disagreements | `agent_results`, `votes`, `conflicts`, `consensus`, `disagreements`, `confidence_distribution` |
| Performance | `MemoryType.PERFORMANCE` | Stores latency, pipeline cost, routing decisions, memory hit rate | `latency_ms`, `pipeline_cost`, `routing_decision`, `memory_hit_rate` |

Each memory type is stored as a `MemoryEntry` (defined in `interfaces.py:44`) with the unified schema: `memory_id`, `version`, `timestamp`, `source_module`, `quality_score`, `confidence`, `lineage`, `tags`, `metadata`, `content`. Content validation is enforced by `DefaultMemoryValidator` (`memory_validator.py:10-16`) which checks for type-specific required fields.

---

## 4. Data Flows

### 4.1 Store Pipeline

```
Request: store(memory_type, content, tags, ...)
  |
  v
+-----------+     +----------+     +----------+     +---------+     +--------+     +---------+     +---------+
| Validate  | --> | Plugin   | --> | Version  | --> | Store   | --> | Index  | --> | Audit   | --> | Return  |
| (schema,  |     | (pre-    |     | (create  |     | (save   |     | (tag/  |     | (log    |     | (Store  |
|  bounds)  |     |  store)  |     |  initial |     |  to     |     |  type/ |     |  store  |     |  Result |
|           |     |          |     |  or inc  |     |  store) |     |  src)  |     |  event) |     |  with   |
+-----------+     +----------+     +----------+     +---------+     +--------+     +---------+     |  id/ver |
                                                                                                 +---------+
```

### 4.2 Query Pipeline

```
Request: retrieve(query)
  |
  v
+---------+     +----------+     +--------+     +-----------+     +---------+
| Audit   | --> | Retrieve | --> | Plugin | --> | Rank      | --> | Return  |
| (log    |     | (from    |     | (post- |     | (Recency, |     | (Memory |
|  query) |     |  store   |     |  retrieve|    |  Conf,    |     |  Result |
|         |     |  via     |     |         |     |  Quality, |     |  with   |
|         |     |  index)  |     |         |     |  Freq,    |     |  entries|
+---------+     +----------+     +--------+     |  Comp.)   |     |  + ms)  |
                                                +-----------+     +---------+
```

---

## 5. Integration Points with ARES Pipeline

| ARES Stage | CMS Interface | Memory Types Produced | Trigger |
|---|---|---|---|
| Perception Layer | `MemoryEngine.store()` | Episodic | After question pair analysis |
| Understanding Layer | `MemoryEngine.store()` | Semantic | After entity/intent extraction |
| Reasoning Layer | `MemoryEngine.store()` | Reasoning | After reasoning graph construction |
| Debate Engine (MADE) | `MemoryEngine.store()` | Debate | After agent debate completion |
| Routing Engine | `MemoryEngine.store()` | Performance | After routing decision |
| Decision Layer | `MemoryEngine.retrieve()` | All types | Before ensemble fusion |
| Learning Layer | `MemoryEngine.retrieve()` | Episodic, Performance | During adaptation cycles |

---

## 6. Design Rationale

### Deterministic, Not ML-Based

Every CMS operation is a deterministic function. The same inputs always produce the same outputs. This property is essential for reproducibility in NLP research:

- Quality scores are computed from fixed formulas, not learned weights
- Consolidation merges use deterministic duplicate detection rules
- Forgetting policies apply hard thresholds, not learned importance scores
- Ranking strategies are rule-based (recency, confidence, quality, frequency)

### In-Memory, Not Database-Backed

The CMS operates entirely in memory for Phase 6. This design choice provides:

- Sub-millisecond store/retrieve latency
- No external dependencies (no Redis, SQLite, or file system requirements)
- Simplified testing and debugging
- Thread-safe operations via `threading.Lock`

### Plugin Architecture

The `MemoryPlugin` ABC (`interfaces.py:255`) defines two hooks — `process_before_store` and `process_after_retrieve` — enabling pipeline stages to inject custom preprocessing or postprocessing logic without modifying CMS internals.

---

## 7. Key Innovations

| Innovation | Description | Location |
|---|---|---|
| Memory Lineage | Every entry tracks its provenance: `created_by`, `parent_ids`, `module_chain`, `reasoning_id`, `debate_id` | `interfaces.py:24-41` |
| Composite Quality Scoring | Quality = weighted combination of confidence, evidence, usage, completeness | `memory_quality.py` (documented in `QUALITY_SCORING.md`) |
| Deterministic Consolidation | Duplicate detection via content/tag similarity; merge via max quality + weighted confidence | `MEMORY_CONSOLIDATION.md` |
| Five-Type Taxonomy | Memories classified by cognitive function, not storage format | `MEMORY_TYPES.md` |
| Plugin Pre/Post Hooks | Extensible without modifying core | `interfaces.py:255-262` |
| Audit Immutability | All actions logged; audit log never cleared by default | `AUDIT_SYSTEM.md` |

---

## 8. Limitations and Future Work

### Current Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| In-memory only | No persistence across process restarts | Data can be serialized via `to_dict()` |
| No ML-based quality | Quality scores use fixed weights | Composite formula is configurable |
| No distributed support | Single-process only | Thread-safe but not multi-node |
| No cross-session memory | Memory resets on restart | Serialization planned for Phase 8 |
| No memory synthesis | Cannot generate new knowledge from existing entries | Research item |

### Future Work

- **Phase 7**: Connect CMS to inference — use retrieval results to inform ensemble weights and routing decisions
- **Phase 8**: Persistent storage — file-based and optional relational database backends
- **Phase 9**: Distributed memory — multi-process and multi-node support with consistency guarantees
- **Long-term**: ML-based quality scoring, automated memory synthesis, cross-session memory consolidation

---

## 9. Module Map

| Module | Path | Purpose |
|---|---|---|
| `interfaces.py` | `_memory/interfaces.py` | ABC definitions, dataclasses, enums |
| `memory_store.py` | `_memory/memory_store.py` | In-memory dictionary store with thread safety |
| `memory_index.py` | `_memory/memory_index.py` | Tag, type, source, text, filter indexing |
| `memory_configuration.py` | `_memory/memory_configuration.py` | Configuration dataclass and loader |
| `memory_query.py` | `_memory/memory_query.py` | Query builder with presets |
| `memory_result.py` | `_memory/memory_result.py` | Result dataclasses (Store, Delete, Consolidation) |
| `memory_validator.py` | `_memory/memory_validator.py` | Schema and bounds validation |
| `memory_serializer.py` | `_memory/memory_serializer.py` | Entry serialization |
| `memory_deserializer.py` | `_memory/memory_deserializer.py` | Entry deserialization |
| `memory_registry.py` | `_memory/memory_registry.py` | Type and plugin registries |
| `memory_metadata.py` | `_memory/memory_metadata.py` | Metadata tracking (access count, frequency) |
| `memory_statistics.py` | `_memory/memory_statistics.py` | Statistics computation |
| `plugins/__init__.py` | `_memory/plugins/__init__.py` | Default plugin implementation |

---

## References

- Detailed API: `MEMORY_ARCHITECTURE.md`
- Type specifications: `MEMORY_TYPES.md`
- Versioning design: `MEMORY_VERSIONING.md`
- Lineage system: `MEMORY_LINEAGE.md`
- Retrieval: `RETRIEVAL_ENGINE.md`
- Consolidation: `MEMORY_CONSOLIDATION.md`
- Forgetting: `FORGETTING_POLICY.md`
- Quality scoring: `QUALITY_SCORING.md`
- Audit: `AUDIT_SYSTEM.md`
- Benchmarks: `PERFORMANCE_BENCHMARKS.md`
- Research context: `docs/research/PHASE6_RESEARCH_SUMMARY.md`
