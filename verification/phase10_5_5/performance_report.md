# Performance Report — Phase 10.5.5

## Observability Diagnostics

The demo engine result dict now includes timing for each pipeline phase:

| Phase | Variable | Description |
|-------|----------|-------------|
| 1 Planning | `planning_time` | Goal creation + plan generation + validation + optimization |
| 2 Prediction | `prediction_time` | Inference dispatcher call |
| 2.5 Semantic | `semantic_time` | Entity ambiguity check |
| 3 Memory Write | `memory_write_time` | Store prediction result |
| 4 Memory Read | `memory_read_time` | Search memory entries |
| 5 Reflection | `reflection_time` | Trust/risk/recommendations |
| 6 Store Reflection | (included in memory total) | Store reflection result |
| 7 Orchestration | `execution_time` | Agent coordination (remaining agents) |
| Total | `total_time` | Full pipeline wall time |

## Backend Info

Available via `ARES.list_models()` which delegates to `InferenceDispatcher.list_models()`.

Model types and their backends:
- `classical-ml` → Week2InferenceService (sklearn-based)
- `transformer` → DuplicateQuestionInferenceService (HuggingFace)
- `bi-encoder` → SentenceTransformer
- `cross-encoder` → SentenceTransformer
- `ensemble` → Ensemble predictor

## Memory Performance

- `MemoryStore` capacity limits prevent unbounded growth
- FIFO eviction O(n) per tier (n = entries in tier)
- TTL sweep O(m) where m = total entries
- Query O(k) where k = matching entries

## Graph Generation

- O(v + e) for graph construction
- DFS-based cycle detection: O(v + e)
- BFS reachability: O(v + e)
