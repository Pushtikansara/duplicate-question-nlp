# ARES Benchmarking Guide

## Benchmark Configurations

`BenchmarkRunner.CONFIGURATIONS` defines 5 configurations that progressively
enable ARES cognitive modules:

| Config Key | Display Name | Modules Enabled | Routing | Semantic | Reasoning | MADE | Memory |
|---|---|---|---|---|---|---|---|
| `baseline` | Baseline (CrossEncoder) | cross_encoder | - | - | - | - | - |
| `config_a` | Config A (+Semantic) | cross_encoder, semantic | - | + | - | - | - |
| `config_b` | Config B (+Reasoning) | cross_encoder, semantic, reasoning | - | + | + | - | - |
| `config_c` | Config C (+MADE) | cross_encoder, semantic, reasoning, made | - | + | + | + | - |
| `config_d_full` | Config D (Full ARES) | cross_encoder, routing, semantic, reasoning, made, memory | + | + | + | + | + |

## Running Benchmarks

### Using BenchmarkRunner (single-config or all)

```python
from duplicate_question_app._evaluation import BenchmarkRunner, EvaluationConfig

config = EvaluationConfig()
runner = BenchmarkRunner(config)

# Single configuration
result = runner.run_configuration(
    "config_d_full",
    prediction_fn=my_pipeline.predict,
    test_pairs=[(q1, q2, label) for q1, q2, label in dataset],
)

# All 5 configurations
results = runner.run_all_configurations(
    prediction_fn=my_pipeline.predict,
    test_pairs=test_pairs,
)

# Get comparison DataFrame
comparison_df = runner.get_comparison()
```

### Using BenchmarkSuite (full orchestration)

```python
from duplicate_question_app._evaluation import BenchmarkSuite

suite = BenchmarkSuite(output_dir="evaluation_results")
summary = suite.run(
    prediction_fn=my_pipeline.predict,
    test_pairs=test_pairs,
)
```

`BenchmarkSuite.run()` automatically:
1. Runs all 5 configurations via `BenchmarkRunner.run_all_configurations()`
2. Exports benchmark_comparison.csv
3. Exports benchmark_summary.json
4. Generates benchmark_comparison.md (markdown table)
5. Generates benchmark_report.md (per-config detail)

## Interpreting Results

The comparison table contains per-configuration rows with columns:

| Config | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC | Brier | Log Loss | ECE | MCE |
|---|---|---|---|---|---|---|---|---|---|---|

Key interpretation guidelines:

- **F1 progression**: increasing F1 across A->D indicates positive
  contribution from each added module. A plateau may suggest redundancy.
- **ROC-AUC vs PR-AUC**: PR-AUC is more informative for class-imbalanced
  duplicate detection tasks.
- **ECE/MCE**: lower is better. Increasing ECE across configurations may
  indicate overconfidence from added complexity.
- **Brier/Log Loss**: lower is better. These are proper scoring rules
  sensitive to both discrimination and calibration.

## Example Usage

```python
import pandas as pd
from duplicate_question_app._evaluation import (
    EvaluationConfig, BenchmarkSuite, BenchmarkRunner,
)

config = EvaluationConfig(
    classification_metrics=True,
    performance_metrics=True,
    generate_plots=True,
    export_csv=True,
    export_markdown=True,
)

test_pairs = [
    ("What is Python?", "What is Java?", 0),
    ("How to sort a list?", "How to sort an array?", 1),
]

def dummy_predict(q1, q2):
    # Replace with actual ARES pipeline call
    return {"predicted_label": 1, "prob_duplicate": 0.85}

suite = BenchmarkSuite(config, output_dir="eval_output")
summary = suite.run(dummy_predict, test_pairs)

comparison = pd.read_csv("eval_output/benchmark_comparison.csv")
print(comparison.to_markdown(index=False))
```
