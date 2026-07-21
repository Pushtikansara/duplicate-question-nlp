# ARES — Adaptive Reasoning Engine for Semantic Understanding

## Pipeline

```
Question Pair → Perception → Adaptive Cognitive Router → Semantic Intelligence → Reasoning → MADE → CMS → Decision
```

## Completed Phases

### Phase 4: Multi-Agent Cognitive Debate Engine (MADE)
**Status:** Complete (137 tests)

8 deterministic agents, 3 voting strategies, conflict detection, consensus building.
- `_agents/` — 14 modules, 137 tests
- `docs/architecture/` — 8 publication-quality docs
- `PHASE4_COMPLETION.md` — completion report
- `docs/research/PHASE4_RESEARCH_SUMMARY.md` — research rationale

### Phase 5: Adaptive Cognitive Routing (ACR)
**Status:** Complete (120 tests)

Routes questions to appropriate pipeline tier based on complexity + uncertainty.
- `_routing/` — 15 modules, 120 tests
- `docs/architecture/` — 5 routing docs
- 4 pipeline tiers: CrossEncoder, Semantic+Reasoning, Full Cognitive, Uncertain

### Phase 6: Cognitive Memory System (CMS)
**Status:** Complete (355 tests)

Deterministic long-term cognitive memory with 5 memory types, knowledge graphs, versioning, audit, forgetting, consolidation.
- `_memory/` — 28 modules, 2,692 lines
- `tests/unit/memory/` — 25 test files, 355 tests
- `docs/architecture/` — 13 subsystem docs
- `docs/research/PHASE6_RESEARCH_SUMMARY.md` — research grounding
- `PHASE6_COMPLETION.md` — completion report

## Test Results
- **Total: 1,209 passed**, 2 failed (pre-existing: streamlit pages, week2_inference)
- No existing modules modified — all phases are standalone

## Five CMS Memory Types
| Type | Content | Purpose |
|---|---|---|
| Episodic | Question pairs, pipeline, decision, latency | Session recall |
| Semantic | Concepts, entities, relations, intent patterns | Reusable knowledge |
| Reasoning | Reasoning graphs, premises, evidence chains | Traceable logic |
| Debate | Agent results, votes, conflicts, consensus | Multi-perspective records |
| Performance | Latency, cost, routing, hit rates | System metrics |

## CMS Key Features
- **KnowledgeGraph** — graph traversal, neighbor lookup, build-from-memory
- **MemoryVersioning** — version chains, history, max-version enforcement
- **MemoryLineage** — ancestor/descendant traversal, merge tracking
- **Consolidation** — MD5-based duplicate detection, type-specific merge
- **ForgettingEngine** — age, quality, confidence, expiry policies
- **MemoryAudit** — per-entry and global action log
- **QualityScoring** — composite (confidence × evidence × usage × completeness)
- **5 RetrievalRankers** — recency, confidence, quality, usage frequency, composite
- **Plugin system** — MemoryPlugin ABC with before_store/after_retrieve hooks
