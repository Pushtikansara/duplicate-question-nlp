# ARES Phase 7.5 REBAF: Research Evaluation Framework

## Purpose

REBAF (Research Evaluation and Benchmarking Assessment Framework) provides a
modular, extensible system for scientifically evaluating every cognitive
subsystem within the ARES duplicate-question pipeline. It measures
classification accuracy, per-module latency and memory, confidence
calibration, routing behavior, reasoning chain quality, multi-agent debate
consensus, memory integrity, and explainability completeness.

## Architecture Overview

The framework is organized as a flat package with specialized modules
coordinated by an `EvaluationEngine` top-level orchestrator. Plugins allow
third-party hook injection.

```
EvaluationEngine
  |-- Evaluator            (core metric computation)
  |-- BenchmarkRunner      (5-config benchmarking)
  |-- BenchmarkSuite       (full benchmark orchestration)
  |-- AblationEngine       (module ablation studies)
  |-- ReportGenerator      (MD/CSV/JSON/HTML output)
  |-- LatencyProfiler      (context-manager timing)
  |-- MemoryProfiler       (per-module memory tracking)
  |-- ErrorAnalyzer        (wraps error_analysis.py)
  |-- Visualization        (matplotlib/seaborn figures)
  +-- Plugins              (before/after hooks)
```

## File Listing

| File | Key Exports |
|---|---|
| `configuration.py` | `EvaluationConfig`, `BenchmarkConfig`, `AblationConfig` |
| `benchmark_result.py` | `BenchmarkResult`, `AblationResult`, `ClassificationMetrics`, `PerModuleMetrics`, `ModuleSpecificMetrics` |
| `evaluator.py` | `Evaluator` |
| `benchmark_runner.py` | `BenchmarkRunner` (5 configs) |
| `benchmark_suite.py` | `BenchmarkSuite` |
| `ablation_engine.py` | `AblationEngine` (5 targets) |
| `latency_profiler.py` | `LatencyProfiler` (context manager + snapshot) |
| `memory_profiler.py` | `MemoryProfiler`, `estimate_object_size` |
| `calibration_metrics.py` | `compute_reliability_diagram`, `compute_confidence_histogram`, `compute_brier_score`, `compute_log_loss` |
| `error_analyzer.py` | `ErrorAnalyzer` |
| `error_analysis.py` | `ErrorCategory`, `categorize_error`, `classify_hardness`, `mine_hard_examples` |
| `explainability_metrics.py` | `compute_explainability_score`, sub-scores |
| `routing_metrics.py` | `compute_routing_metrics` |
| `reasoning_metrics.py` | `compute_reasoning_metrics` |
| `debate_metrics.py` | `compute_debate_metrics` |
| `memory_metrics.py` | `compute_memory_metrics` |
| `report_generator.py` | `ReportGenerator` (10 report types) |
| `visualization.py` | `plot_latency_breakdown`, `plot_module_contribution`, `plot_ablation_comparison`, `plot_routing_distribution`, `plot_agent_agreement_heatmap` |
| `evaluation_engine.py` | `EvaluationEngine` |
| `metrics.py` | `evaluate_model`, `generate_evaluation_report`, `compare_models`, plotting |
| `plugins/__init__.py` | `EvaluationPlugin`, `DefaultEvaluationPlugin` |

## EvaluationEngine Orchestration

`EvaluationEngine.run_full_evaluation()` accepts either a `predictions_df`
(DataFrame with true_label, predicted_label, prob_duplicate) or raw
`test_pairs` + `prediction_fn`. It executes:

1. Classification metrics via `generate_evaluation_report()`
2. Benchmark suite across 5 configurations (if test_pairs provided)
3. Calibration analysis (reliability diagram + confidence histogram)
4. Error analysis via ErrorAnalyzer.analyze_batch()
5. Report generation (comparison, benchmark, calibration, error, summary)
6. JSON serialization of all results

## Key Metrics

### Classification (10 metrics)

- Accuracy, Precision, Recall, F1
- ROC-AUC, PR-AUC
- Brier Score, Log Loss
- ECE (Expected Calibration Error), MCE (Maximum Calibration Error)

Additional fields on `ClassificationMetrics`: MCC, Balanced Accuracy, Cohen
Kappa.

### Performance (4 metrics)

- Total Latency (ms)
- Total Memory (bytes)
- Throughput (samples/s)
- Per-module latency breakdown

### Module-Specific Metrics

- **Routing**: pipeline_selections, complexity_distribution,
  uncertainty_escalations, avg_latency_ms
- **Reasoning**: avg_premise_count, avg_hypothesis_count,
  avg_evidence_chain_length, avg_confidence, avg_uncertainty
- **Debate**: avg_agent_agreement, avg_consensus_confidence,
  conflict_frequency, avg_debate_duration_ms
- **Memory**: total_entries, avg_quality, avg_confidence, deleted_count
- **Explainability**: reasoning_completeness, evidence_completeness,
  debate_completeness, memory_usage, overall weighted score

## Export Formats

| Format | Trigger | Contents |
|---|---|---|
| CSV | `export_csv=True` | benchmark_comparison.csv, per-config false_positives/false_negatives |
| JSON | `export_json=True` | evaluation_results.json, benchmark_summary.json, per-config metrics |
| Markdown | `export_markdown=True` | benchmark_comparison.md, benchmark_report.md, ablation_report.md, error_report.md, latency_report.md, calibration_report.md, routing_report.md, memory_report.md, explainability_report.md, evaluation_summary.md |
| HTML | `export_html=True` | (reserved for future formatted output) |
| PNG | `generate_plots=True` | latency_breakdown, module_contribution, ablation_comparison, routing_distribution, agent_agreement_heatmap, plus per-config roc, pr, calibration, confusion_matrix, prediction_distribution, error_analysis |
