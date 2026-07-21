# Retrieval Engine — Querying the Cognitive Memory System

---

## 1. Overview

The Retrieval Engine is the query interface for the ARES CMS. It transforms `MemoryQuery` objects into ranked, paginated `MemoryResult` responses by coordinating index-based filtering, optional ranking strategies, and result pagination. The engine supports five query types — exact match, tagged, confidence threshold, text search, and hybrid — enabling flexible retrieval patterns across all memory types.

---

## 2. Architecture

```
Retrieval Pipeline
  =====================================================================

  MemoryQuery
     |
     v
  +------------------+
  | DefaultRetrieval |
  | Engine           |
  |                  |
  |  1. Select Index |
  |     (or fallback) |
  |                  |
  |  2. Filter       |
  |     +-- type      |
  |     +-- tag       |
  |     +-- source    |
  |     +-- confidence|
  |     +-- quality   |
  |     +-- text      |
  |     +-- metadata  |
  |                  |
  |  3. Rank          |
  |     (if ranker)   |
  |                  |
  |  4. Paginate      |
  |     +-- offset    |
  |     +-- limit     |
  |                  |
  |  5. Measure       |
  |     query_time_ms |
  |                  |
  |  6. Return        |
  | MemoryResult      |
  +------------------+
```

---

## 3. Query Types

| Type | `query_type` Value | Description | Index Required |
|---|---|---|---|
| Exact | `"exact"` | Filter by memory_type, tags, source, confidence, quality | Yes (for filtering) |
| Tagged | `"exact"` | Use `tags` filter to find entries with matching tags | Yes |
| Confidence | `"exact"` | Use `min_confidence` and `min_quality` thresholds | Yes |
| Text | `"semantic"` | Full-text search across entry content and tags | No (linear scan if no index) |
| Hybrid | `"hybrid"` | Combine type/tag filters with text search | Yes |

---

## 4. DefaultRetrievalEngine

```python
class DefaultRetrievalEngine(RetrievalEngine):
    def __init__(self, ranker: RetrievalRanker | None = None) -> None:
        self._ranker = ranker

    def retrieve(
        self,
        query: MemoryQuery,
        store: MemoryStore,
        index: MemoryIndex | None = None,
        ranker: RetrievalRanker | None = None,
    ) -> MemoryResult:
        start_time = time.time()

        # Step 1: Use index if available
        if index:
            entries = index.search(query, store)
        else:
            entries = self._fallback_search(query, store)

        # Step 2: Apply ranker
        active_ranker = ranker or self._ranker
        if active_ranker:
            entries = active_ranker.rank(entries, query)

        # Step 3: Pagination
        total = len(entries)
        page = entries[query.offset : query.offset + query.limit]

        # Step 4: Measure
        elapsed_ms = (time.time() - start_time) * 1000

        return MemoryResult(
            entries=page,
            total_count=total,
            query_time_ms=elapsed_ms,
            query=query,
        )
```

---

## 5. Fallback Search (Without Index)

When no `MemoryIndex` is provided, the engine falls back to a linear scan:

```python
def _fallback_search(self, query, store):
    all_entries, _ = store.list_all(limit=100000)
    candidates = all_entries

    if query.memory_types:
        type_values = {mt.value for mt in query.memory_types}
        candidates = [e for e in candidates if e.memory_type.value in type_values]

    if query.tags:
        query_tags = set(query.tags)
        candidates = [e for e in candidates if query_tags & set(e.tags)]

    if query.source_modules:
        candidates = [e for e in candidates if e.source_module in query.source_modules]

    if query.min_confidence > 0:
        candidates = [e for e in candidates if e.confidence >= query.min_confidence]

    if query.min_quality > 0:
        candidates = [e for e in candidates if e.quality_score >= query.min_quality]

    if query.text:
        candidates = [e for e in candidates if self._text_match(e, query.text)]

    for key, value in query.filters.items():
        candidates = [
            e for e in candidates
            if e.metadata.get(key) == value or e.content.get(key) == value
        ]

    return candidates
```

---

## 6. RetrievalRanker Strategies

The `RetrievalRanker` ABC (`interfaces.py:195`) defines a single method:

```python
class RetrievalRanker(ABC):
    @abstractmethod
    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        ...
```

### Ranker Implementations

| Ranker | Strategy | Sort Key | Use Case |
|---|---|---|---|
| `RecencyRanker` | Most recent first | `entry.timestamp` (descending) | Latest events |
| `ConfidenceRanker` | Highest confidence first | `entry.confidence` (descending) | Most reliable results |
| `QualityRanker` | Highest quality first | `entry.quality_score` (descending) | Best curated results |
| `FrequencyRanker` | Most accessed first | `entry.metadata.access_count` | Frequently used entries |
| `CompositeRanker` | Weighted combination | `0.3*recency + 0.3*confidence + 0.2*quality + 0.2*frequency` | Balanced retrieval |

### CompositeRanker Formula

```python
class CompositeRanker(RetrievalRanker):
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or {
            "recency": 0.3,
            "confidence": 0.3,
            "quality": 0.2,
            "frequency": 0.2,
        }

    def rank(self, entries, query):
        now = datetime.now()

        def composite_score(entry):
            recency = 1.0 - (now - entry.timestamp).days / 365.0  # Normalized to [0, 1]
            recency = max(0.0, min(1.0, recency))
            usage = entry.metadata.get("access_count", 0) / 100.0 if entry.metadata else 0
            usage = min(1.0, usage)

            return (
                self.weights["recency"] * recency
                + self.weights["confidence"] * entry.confidence
                + self.weights["quality"] * entry.quality_score
                + self.weights["frequency"] * usage
            )

        return sorted(entries, key=composite_score, reverse=True)
```

---

## 7. Filter Logic

The `DefaultMemoryIndex.search()` method implements the following filter logic:

```
1.  Start with empty candidate set
2.  FOR each filter dimension present in query:
      a. Query index for matching IDs
      b. Intersect with candidate set (first dimension initializes it)
3.  IF no dimensions specified: use all indexed IDs
4.  APPLY confidence threshold (if > 0): filter by _confidence_map
5.  APPLY quality threshold (if > 0): filter by _quality_map
6.  APPLY text search (if query.text): linear scan content and tags
7.  APPLY metadata/content filters: linear scan remaining entries
8.  Return filtered list
```

Filter intersection is performed using Python `set` operations for O(1) lookup:

```python
# Type filter
type_ids = set()
for mt in query.memory_types:
    type_ids.update(self._by_type.get(mt.value, set()))
candidate_ids = type_ids if candidate_ids is None else candidate_ids & type_ids

# Tag filter
tag_ids = set()
for tag in query.tags:
    tag_ids.update(self._by_tag.get(tag, set()))
candidate_ids = tag_ids if candidate_ids is None else candidate_ids & tag_ids
```

---

## 8. Performance Characteristics

| Scenario | Complexity | Typical Time (10K entries) |
|---|---|---|
| Index search (type + tag) | O(k) where k = matched entries | < 0.1 ms |
| Index search (all dimensions) | O(k) set intersections | < 0.2 ms |
| Fallback linear scan (no index) | O(N) | ~5 ms |
| Text search (indexed) | O(k) text matches | ~0.5 ms |
| Text search (fallback) | O(N) text matches | ~5 ms |
| Ranking (CompositeRanker) | O(k log k) sort | ~0.5 ms |
| Full pipeline (indexed) | O(k log k) | < 1 ms |

---

## 9. Pagination

All retrieval results support pagination via `query.offset` and `query.limit`:

```python
query = MemoryQuery(
    memory_types=[MemoryType.EPISODIC],
    limit=20,
    offset=0,  # First page
)

result = engine.retrieve(query)
# result.entries -> first 20 entries
# result.total_count -> total matching entries (not just 20)

# Second page
query.offset = 20
result = engine.retrieve(query)
# result.entries -> entries 21-40
```

---

## 10. Query Builder Presets

The `MemoryQueryBuilder` (`memory_query.py:6`) provides factory methods for common query patterns:

```python
# By type
query = MemoryQueryBuilder.by_type(MemoryType.EPISODIC, limit=50)

# By tags
query = MemoryQueryBuilder.by_tags(["python", "installation"])

# By confidence threshold
query = MemoryQueryBuilder.by_confidence(min_confidence=0.8)

# By source module
query = MemoryQueryBuilder.by_source("debate_engine")

# Text search
query = MemoryQueryBuilder.text_search("install python ubuntu")

# Hybrid (text + type filter)
query = MemoryQueryBuilder.hybrid(
    text="python",
    memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
)
```

---

## 11. Examples

### Example 1: Find High-Confidence Episodic Memories

```python
engine = RetrievalEngine()
query = MemoryQuery(
    query_type="exact",
    memory_types=[MemoryType.EPISODIC],
    min_confidence=0.9,
    limit=10,
)
result = engine.retrieve(query, store, index)

for entry in result.entries:
    print(f"{entry.memory_id}: {entry.content['decision']} "
          f"(conf={entry.confidence:.2f}, quality={entry.quality_score:.2f})")
```

### Example 2: Text Search with Hybrid Query

```python
query = MemoryQuery(
    query_type="hybrid",
    memory_types=[MemoryType.EPISODIC],
    text="install python",
    tags=["tutorial"],
    limit=20,
)
result = engine.retrieve(query, store, index)
# Returns entries matching "install python" in content that are also tagged "tutorial"
```

### Example 3: Retrieval with Composite Ranking

```python
ranker = CompositeRanker(weights={
    "recency": 0.4,
    "confidence": 0.3,
    "quality": 0.2,
    "frequency": 0.1,
})
engine = DefaultRetrievalEngine(ranker=ranker)

query = MemoryQueryBuilder.by_type(MemoryType.DEBATE)
result = engine.retrieve(query, store, index)
# Results ranked: recent debates with high confidence and quality prioritized
```

---

## 12. Limitations

- No BM25 or TF-IDF text ranking (simple substring matching only)
- No semantic/embedding-based similarity search in Phase 6
- No faceted search or aggregation queries
- No query caching for repeated identical queries
- No support for boolean operators (AND/OR/NOT) in text search

---

## 13. References

- Architecture: `MEMORY_ARCHITECTURE.md`
- Query builder: `memory_query.py`
- Index source: `memory_index.py`
- Ranking quality: `QUALITY_SCORING.md`
- Knowledge graph (for graph queries): `KNOWLEDGE_GRAPH.md`
