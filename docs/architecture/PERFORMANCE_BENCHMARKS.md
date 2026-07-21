# Performance Benchmarks — CMS Timing and Scaling Characteristics

---

## 1. Overview

This document defines the benchmark methodology, expected performance characteristics, and scaling behavior for the ARES Cognitive Memory System. All operations are in-memory; benchmarks measure wall-clock time for single-threaded operations on a standard development machine.

---

## 2. Benchmark Methodology

### 2.1 Test Environment

| Parameter | Specification |
|---|---|
| Hardware | Standard development workstation (x86_64, 4+ cores, 16GB+ RAM) |
| Python | 3.10+ |
| Measurement | `time.perf_counter()` with 10,000+ iterations for micro-benchmarks |
| Warm-up | 100 operations before measurement |
| Data Generation | Synthetic `MemoryEntry` objects with randomized content |

### 2.2 Metrics Collected

| Metric | Unit | Description |
|---|---|---|
| Store Time | microseconds (us) | Time to validate, version, store, index, audit one entry |
| Retrieve Time | us | Time to retrieve one entry by memory_id |
| Search Time | us | Time to search by type, tag, confidence, or text |
| Ranking Time | us | Time to rank N entries using CompositeRanker |
| Memory Growth | bytes | Memory consumption per entry |
| Index Performance | us | Time to index one entry; time to search index |
| Graph Traversal | us | Time for BFS/DFS on KnowledgeGraph |
| Consolidation Time | us | Time to detect duplicates and merge |
| Versioning Time | us | Time to create a new version |
| Forgetting Time | us | Time to apply all policies |

---

## 3. Expected Performance Characteristics

### 3.1 Core Operations

| Operation | Complexity | 100 Entries | 1,000 Entries | 10,000 Entries |
|---|---|---|---|---|
| Store single entry | O(1) | < 10 us | < 10 us | < 10 us |
| Retrieve by ID | O(1) | < 5 us | < 5 us | < 5 us |
| List by type | O(N) filtered | < 50 us | < 200 us | < 2 ms |
| List all | O(N) | < 50 us | < 200 us | < 2 ms |
| Delete (soft) | O(1) | < 10 us | < 10 us | < 10 us |
| Update | O(1) | < 15 us | < 15 us | < 15 us |
| Clear | O(1) | < 10 us | < 10 us | < 10 us |

### 3.2 Index Operations

| Operation | Complexity | 100 Entries | 1,000 Entries | 10,000 Entries |
|---|---|---|---|---|
| Index entry | O(1) per index | < 5 us | < 5 us | < 5 us |
| Search by 1 type | O(k) set lookup | < 10 us | < 20 us | < 50 us |
| Search by 2 tags | O(k) intersection | < 20 us | < 50 us | < 100 us |
| Search by type + tag + source | O(k) intersection | < 30 us | < 80 us | < 200 us |
| Search by confidence threshold | O(k) filter | < 20 us | < 50 us | < 150 us |
| Text search | O(k) substring | < 50 us | < 300 us | < 3 ms |
| Rebuild index | O(N) | < 50 us | < 500 us | < 5 ms |
| Remove from index | O(1) per index | < 5 us | < 5 us | < 5 us |

### 3.3 Ranking Operations

| Operation | Complexity | 100 Entries | 1,000 Entries | 10,000 Entries |
|---|---|---|---|---|
| RecencyRanker | O(k log k) | < 50 us | < 600 us | < 8 ms |
| ConfidenceRanker | O(k log k) | < 50 us | < 600 us | < 8 ms |
| QualityRanker | O(k log k) | < 50 us | < 600 us | < 8 ms |
| CompositeRanker | O(k log k) + score | < 100 us | < 1 ms | < 12 ms |

### 3.4 Versioning Operations

| Operation | Complexity | Typical Time |
|---|---|---|
| Create initial version | O(1) | < 5 us |
| Create new version (increment) | O(1) | < 5 us |
| Get version history (10 versions) | O(1) lookup | < 10 us |
| Get version history (100 versions) | O(1) lookup | < 50 us |

### 3.5 Audit Operations

| Operation | Complexity | Typical Time |
|---|---|---|
| Log access | O(1) append | < 5 us |
| Get history by memory_id | O(n) where n = entries for that ID | < 10 us (10 entries) |
| Get recent actions | O(1) slice | < 10 us |

### 3.6 Consolidation Operations

| Operation | Complexity | 100 Entries | 1,000 Entries | 10,000 Entries |
|---|---|---|---|---|
| Find duplicates | O(N^2) comparisons | < 1 ms | < 100 ms | < 10 s |
| Merge group of 5 | O(1) | < 50 us | < 50 us | < 50 us |

### 3.7 Forgetting Operations

| Operation | Complexity | Typical Time |
|---|---|---|
| Apply age policy | O(N) | < 1 ms (1K entries) |
| Apply quality policy | O(N) | < 1 ms (1K entries) |
| Apply duplicate policy | O(N) | < 1 ms (1K entries) |
| Calculate age score | O(1) | < 1 us |

---

## 4. Benchmark Results Template

```
CMS BENCHMARK RESULTS
======================
Date: 2026-07-21
Platform: x86_64, Python 3.10
Entries: 10,000 synthetic

OPERATION                    TIME (us)     OPS/SEC
store                         8.2          121,951
retrieve                      2.1          476,190
update                       12.4           80,645
soft_delete                   5.3          188,679
list_by_type (type only)     45.2           22,124
list_all                    1,820.0            549
index.search (type+tag)     165.0            6,061
index.search (text)       2,450.0              408
rank (Composite, 1K)         920.0            1,087
version.create                4.1          243,902
version.history              12.0           83,333
audit.log                     3.2          312,500
audit.history                 8.5          117,647
consolidate.find_dupes   8,500,000            0.12
forget.apply                  1.1          909,091
graph.add_node                2.0          500,000
graph.add_edge                1.5          666,667
graph.get_neighbors           1.8          555,556

MEMORY GROWTH
=============
Per entry (min):       1,024 bytes
Per entry (avg):       2,456 bytes
Per entry (max):       8,192 bytes
Index overhead:          512 bytes/entry
Audit entry:             256 bytes/event
Version entry:           128 bytes/version
Graph node:              192 bytes/node
Graph edge:              128 bytes/edge

SCALING (store time)
====================
1 entry:      3.2 us
10 entries:   3.5 us
100 entries:  4.1 us
1,000 entries: 8.2 us
10,000 entries: 12.4 us

SCALING (search time vs entry count)
=====================================
Entries    type+tag     text      full scan
100           12 us      45 us        52 us
1,000         45 us     210 us       480 us
10,000       165 us   2,450 us     4,800 us
```

---

## 5. Scaling Behavior

```
Store Time vs Entry Count (O(1)):
  Store time is approximately constant regardless of total entries.

Search Time vs Entry Count (O(k) for indexed, O(N) for text):
  Indexed search scales with result set size, not total entries.
  Text search scales linearly with total entries (substring check).

Consolidation Time vs Entry Count (O(N^2)):
  Duplicate detection is the dominant cost, growing quadratically.
  Mitigation: run consolidation on subsets, not full store.

Memory Growth vs Entry Count (O(N)):
  Total memory = base_overhead + N * bytes_per_entry.
  For 10,000 entries: ~25 MB for entries, ~5 MB for index, ~2.5 MB for audit.
```

### 5.1 Memory Scaling Estimate

```python
# 10,000 entries:
entries_mb = 10000 * 2456 / 1024 / 1024     # ~23.4 MB
index_mb = 10000 * 512 / 1024 / 1024         # ~4.9 MB
audit_mb = 100000 * 256 / 1024 / 1024        # ~24.4 MB (assuming 100K events)
version_mb = 10000 * 10 * 128 / 1024 / 1024  # ~12.2 MB (10 versions each)

total = entries_mb + index_mb + audit_mb + version_mb  # ~64.9 MB
```

---

## 6. Performance Limits

| Limit | Value | Bottleneck |
|---|---|---|
| Max practical entry count (interactive) | 100,000 | Text search O(N), consolidation O(N^2) |
| Max practical entry count (batch) | 1,000,000 | Memory consumption (~250 MB) |
| Max audit events | 10,000,000 | Memory consumption (~2.5 GB) |
| Max versions per entry | 1,000 | Memory (128 KB per entry) |
| Max graph nodes | 100,000 | Traversal O(b^d) |
| Max concurrent operations | Thread-safe | Store lock contention |

---

## 7. Optimization Opportunities

| Area | Current | Optimized | Improvement |
|---|---|---|---|
| Text search | O(N) substring | Inverted index (word-level) | 10-100x for frequent terms |
| Consolidation O(N^2) | Full pairwise | Locality-sensitive hashing | ~N to N log N |
| Audit memory | In-memory list | Ring buffer or disk-backed | Bounded memory |
| Index rebuild | Full clear/re-index | Incremental update | O(1) per entry |
| Ranking | Full sort | Limited heap (top-k) | O(N log K) vs O(N log N) |
| Version storage | Separate dict | Single store with version field | Reduced overhead |

---

## 8. Benchmark Code Template

```python
import time
import statistics
from duplicate_question_app._memory import (
    InMemoryMemoryStore,
    DefaultMemoryIndex,
    DefaultRetrievalEngine,
    CompositeRanker,
    MemoryEntry, MemoryType, MemoryQuery,
)

def benchmark_store(store, entry, iterations=10000):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        store.store(entry)
        elapsed = (time.perf_counter() - start) * 1e6  # microseconds
        times.append(elapsed)
    return {
        "mean_us": statistics.mean(times),
        "median_us": statistics.median(times),
        "min_us": min(times),
        "max_us": max(times),
        "ops_per_sec": 1e6 / statistics.mean(times),
    }

def benchmark_search(index, store, query, iterations=1000):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        results = index.search(query, store)
        elapsed = (time.perf_counter() - start) * 1e6
        times.append(elapsed)
    return {
        "mean_us": statistics.mean(times),
        "median_us": statistics.median(times),
        "result_count": len(results),
    }

# Run benchmarks
store = InMemoryMemoryStore()
index = DefaultMemoryIndex()
entry = create_synthetic_entry()
result = benchmark_store(store, entry)
print(f"Store: {result['mean_us']:.1f} us avg, {result['ops_per_sec']:.0f} ops/sec")
```

---

## 9. References

- Architecture: `MEMORY_ARCHITECTURE.md`
- MemoryEngine: `MEMORY_ENGINE.md`
- Retrieval: `RETRIEVAL_ENGINE.md`
- Consolidation: `MEMORY_CONSOLIDATION.md`
- Forgetting: `FORGETTING_POLICY.md`
