# ARES Performance Analysis

## LatencyProfiler

`LatencyProfiler` provides a context manager-based timing system for
measuring per-module execution latency with microsecond precision.

### Context Manager API

```python
from duplicate_question_app._evaluation import LatencyProfiler

profiler = LatencyProfiler()

with profiler.measure("semantic"):
    semantic_result = semantic_module.process(q1, q2)

with profiler.measure("reasoning"):
    reasoning_result = reasoning_module.infer(q1, q2, semantic_result)
```

### Snapshot API

```python
profiler.start()
# ... work ...
profiler.snapshot("cross_encoder")
# ... more work ...
profiler.snapshot("routing")

summary = profiler.get_summary()
# {"total_ms": 35.2, "modules": {"cross_encoder": 15.1, "routing": 20.1}, "num_snapshots": 2}
```

### Features

- Thread-safe (uses `threading.Lock`)
- Returns `LatencySnapshot` objects with module name, elapsed ms, and
  timestamp
- Accumulates multiple measurements per module
- `get_module_latency(name)` returns total for a single module
- `clear()` resets all measurements

## MemoryProfiler

`MemoryProfiler` tracks per-module memory delta from a baseline snapshot.

```python
from duplicate_question_app._evaluation import MemoryProfiler

profiler = MemoryProfiler()
profiler.start()

profiler.snapshot("cross_encoder")
# delta_bytes = current - baseline

delta = profiler.get_module_memory("cross_encoder")
total = profiler.get_total_memory()
```

The module also exports `estimate_object_size()` for recursive deep size
estimation of arbitrary Python objects (handles dicts, lists, tuples, sets,
and objects with `__dict__`).

## Per-Module Latency Tracking

During benchmarking, per-module latencies are stored in `PerModuleMetrics`
objects, each containing:

- `module_name`: str
- `latency_ms`: float
- `memory_bytes`: int
- `cpu_percent`: float
- `throughput`: float

## Latency Breakdown Visualization

`plot_latency_breakdown()` generates a horizontal bar chart showing each
module's contribution to total inference time.

### Example Latency Data (measured)

| Module | Latency (ms) |
|---|---|
| CrossEncoder | 15.0 |
| Semantic | 5.0 |
| Reasoning | 8.0 |
| MADE | 7.0 |
| Routing | 2.0 |
| Memory I/O | 3.0 |
| **Total** | **40.0** |

```python
from pathlib import Path
from duplicate_question_app._evaluation.visualization import plot_latency_breakdown

latencies = {
    "CrossEncoder": 15.0,
    "Semantic": 5.0,
    "Reasoning": 8.0,
    "MADE": 7.0,
    "Routing": 2.0,
    "Memory I/O": 3.0,
}
plot_latency_breakdown(latencies, Path("latency_breakdown.png"))
```

## Report Generation

`ReportGenerator.generate_performance_report()` produces a markdown document
with classification metrics and per-module latency for a single benchmark
result.
