# Query Pipeline

*Version 1.0.0 — Phase 12.0*

---

## Purpose

The Query Pipeline orchestrates the end-to-end flow of transforming a raw question pair into a structured `QueryAnalysis` object. It is the entry point for the Query Understanding module and provides convenience methods for batch processing and dataframe conversion.

---

## Pipeline Stages

```
Input: (question_1, question_2)
          │
          ▼
    ┌─────────────┐
    │  Validation  │  TypeError if not str, ValueError if both empty
    └──────┬──────┘
           │
           ▼
    ┌──────────────┐
    │ Normalization │  lowercase, collapse whitespace, strip
    └──────┬───────┘
           │
           ▼
    ┌───────────────────┐
    │ Feature Extraction │  metadata, tokens, sentences, readability,
    │                    │  complexity, similarity
    └──────┬────────────┘
           │
           ▼
    ┌───────────────────┐
    │ Metadata Assembly │  QueryAnalysis dataclass
    └──────┬────────────┘
           │
           ▼
    ┌──────────────┐
    │    Return     │  QueryAnalysis object (JSON-serializable)
    └──────────────┘
```

---

## API Reference

### `QueryPipeline`

The main pipeline orchestrator.

```python
class QueryPipeline:
    def __init__(self, analyzer: QueryAnalyzer | None = None)
    def run(self, question_1: str, question_2: str) -> QueryAnalysis
    def run_batch(self, pairs: list[tuple[str, str]]) -> list[QueryAnalysis]
    def run_with_metadata(
        self, question_1: str, question_2: str,
        extra: dict[str, Any] | None = None
    ) -> QueryAnalysis
    def to_dataframe(self, analyses: list[QueryAnalysis]) -> pd.DataFrame | None
```

#### `__init__(analyzer)`

Creates a pipeline. If no analyzer is provided, a default `QueryAnalyzer()` is used. This allows dependency injection for testing or custom analysis configurations.

#### `run(question_1, question_2)`

Single-pair analysis. The primary entry point.

- Validates both inputs
- Delegates to `QueryAnalyzer.analyze()`
- Returns a `QueryAnalysis` object

#### `run_batch(pairs)`

Batch processing for multiple question pairs.

- Accepts `list[tuple[str, str]]`
- Returns `list[QueryAnalysis]`
- Processes each pair sequentially (no parallelism)

#### `run_with_metadata(question_1, question_2, extra)`

Single-pair analysis with additional metadata injection.

- Runs the standard `run()` flow
- Injects extra key-value pairs into the result object
- Only sets attributes that already exist on `QueryAnalysis` (silently skips unknown keys)

#### `to_dataframe(analyses)`

Converts a list of `QueryAnalysis` objects to a pandas DataFrame.

- Uses `pandas.json_normalize` with `sep="_"`
- Returns `None` if pandas is not installed
- Useful for downstream analysis, export, and visualization

---

## Usage Examples

### Basic Usage

```python
from ares.query_understanding import QueryPipeline

pipeline = QueryPipeline()
result = pipeline.run(
    "How to learn Python?",
    "Best way to learn programming"
)

print(result.metadata_1.word_count)     # 4
print(result.similarity.word_overlap_ratio)  # 0.3333
print(result.processing_time_ms)        # 1.23
```

### Batch Processing

```python
pairs = [
    ("What is Python?", "What is Java?"),
    ("How to code?", "Learn programming fast"),
]
results = pipeline.run_batch(pairs)
for r in results:
    print(r.metadata_1.language, r.complexity_1.overall)
```

### With Custom Analyzer

```python
from ares.query_understanding import QueryPipeline, QueryAnalyzer

custom_analyzer = QueryAnalyzer()
custom_analyzer.version = "2.0.0"

pipeline = QueryPipeline(analyzer=custom_analyzer)
result = pipeline.run("Q1?", "Q2?")
print(result.version)  # "2.0.0"
```

### Export to DataFrame

```python
results = pipeline.run_batch(pairs)
df = pipeline.to_dataframe(results)
print(df[["metadata_1_word_count", "similarity_word_overlap_ratio"]].describe())
```

---

## Error Handling

| Condition | Behavior |
|---|---|
| Both inputs empty | Raises `ValueError` from `validate_input` |
| Non-string input | Raises `TypeError` from `validate_input` |
| One input empty | Allowed — analysis proceeds with empty values |
| Null/missing extra metadata keys | Silently skipped in `run_with_metadata` |
| Pandas not installed | `to_dataframe` returns `None` |

---

## Integration Points

| Consumer | How to use |
|---|---|
| Prediction engine | Call `pipeline.run()` before `ARES.predict()`, attach `QueryAnalysis` metadata to prediction context |
| Routing engine | Use language, complexity, and content flags to route to appropriate model |
| Explainability | Reference similarity features and readability for explanation generation |
| Verification | Use per-question metadata to validate prediction consistency |
| Memory module | Store `QueryAnalysis.to_dict()` alongside prediction results for future retrieval |
| Monitoring | Log `QueryAnalysis` fields as structured metrics |

---

## Performance Characteristics

- **Single-pair analysis**: < 1ms for typical questions
- **Batch of 1000 pairs**: ~100ms (0.1ms per pair)
- **Memory**: `QueryAnalysis` object ~2 KB per pair
- **No ML inference**: All features are rule-based regex and string operations

---

## Future Enhancements

- Async batch processing (`run_batch_async`)
- Streaming pipeline events via EventBus
- Pluggable pre/post-processing hooks
- Caching for repeated identical inputs
- Configurable normalization strategies
