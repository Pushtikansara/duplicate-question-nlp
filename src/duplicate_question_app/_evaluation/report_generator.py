from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from duplicate_question_app._evaluation.benchmark_result import AblationResult, BenchmarkResult


class ReportGenerator:
    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_comparison_table(self, comparison_df: pd.DataFrame) -> Path:
        path = self.output_dir / "benchmark_comparison.csv"
        comparison_df.to_csv(path, index=False)
        md_path = self.output_dir / "benchmark_comparison.md"
        with open(md_path, "w") as f:
            f.write("# Benchmark Configuration Comparison\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(comparison_df.to_markdown(index=False, floatfmt=".4f"))
        return path

    def generate_benchmark_report(
        self,
        results: dict[str, BenchmarkResult],
        comparison_df: pd.DataFrame,
    ) -> Path:
        path = self.output_dir / "benchmark_report.md"
        with open(path, "w") as f:
            f.write("# ARES Benchmark Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write("## Configuration Comparison\n\n")
            f.write(comparison_df.to_markdown(index=False, floatfmt=".4f"))
            f.write("\n\n")
            for name, r in results.items():
                f.write(f"## {name}\n\n")
                f.write(f"- Modules: {', '.join(r.modules_enabled)}\n")
                f.write(f"- Samples: {r.num_samples}\n")
                f.write(f"- F1: {r.classification.f1:.4f}\n")
                f.write(f"- Accuracy: {r.classification.accuracy:.4f}\n")
                f.write(f"- ROC-AUC: {r.classification.roc_auc:.4f}\n")
                f.write(f"- ECE: {r.classification.ece:.4f}\n")
                f.write(f"- Total Latency: {r.total_latency_ms:.2f}ms\n\n")
        return path

    def generate_ablation_report(self, ablation_result: AblationResult) -> Path:
        path = self.output_dir / "ablation_report.md"
        with open(path, "w") as f:
            f.write("# ARES Ablation Study Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write("## Full ARES\n\n")
            full = ablation_result.full_config
            f.write(f"- F1: {full.classification.f1:.4f}\n")
            f.write(f"- Accuracy: {full.classification.accuracy:.4f}\n")
            f.write(f"- ROC-AUC: {full.classification.roc_auc:.4f}\n\n")
            f.write("## Ablated Configurations\n\n")
            rows = []
            for entry in ablation_result.contribution_ranking:
                rows.append(
                    {
                        "Module Removed": entry["module"],
                        "F1": f"{entry['f1_without']:.4f}",
                        "F1 Delta": f"{entry['f1_delta']:+.4f}",
                        "Accuracy": f"{entry['accuracy_without']:.4f}",
                    }
                )
            f.write(pd.DataFrame(rows).to_markdown(index=False))
            f.write("\n\n## Contribution Ranking\n\n")
            for i, entry in enumerate(ablation_result.contribution_ranking, 1):
                direction = "IMPROVES" if entry["f1_delta"] > 0 else "HURTS" if entry["f1_delta"] < 0 else "NEUTRAL"
                f.write(f"{i}. {entry['module']}: F1 delta = {entry['f1_delta']:+.4f} ({direction})\n")
        return path

    def generate_error_report(self, error_df: pd.DataFrame, title: str = "Error Analysis") -> Path:
        path = self.output_dir / "error_report.md"
        with open(path, "w") as f:
            f.write(f"# {title}\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"Total errors analyzed: {len(error_df)}\n\n")
            if not error_df.empty:
                cat_col = "error_categories"
                if cat_col in error_df.columns:
                    all_cats: dict[str, int] = {}
                    for cats in error_df[cat_col]:
                        if isinstance(cats, list):
                            for c in cats:
                                if isinstance(c, dict):
                                    name = c.get("name", "unknown")
                                    all_cats[name] = all_cats.get(name, 0) + 1
                    f.write("### Error Categories\n\n")
                    for name, count in sorted(all_cats.items(), key=lambda x: -x[1]):
                        f.write(f"- {name}: {count}\n")
        return path

    def generate_latency_report(self, latency_data: dict[str, Any]) -> Path:
        path = self.output_dir / "latency_report.md"
        with open(path, "w") as f:
            f.write("# Latency Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            for module, metrics in latency_data.items():
                f.write(f"## {module}\n\n")
                if isinstance(metrics, dict):
                    for k, v in metrics.items():
                        f.write(f"- {k}: {v}\n")
                else:
                    f.write(f"- Value: {metrics}\n")
                f.write("\n")
        return path

    def generate_performance_report(self, result: BenchmarkResult) -> Path:
        path = self.output_dir / "performance_report.md"
        with open(path, "w") as f:
            f.write(f"# Performance Report: {result.config_name}\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write("## Classification Metrics\n\n")
            cm = result.classification
            for field in ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "brier_score", "ece", "mce"]:
                f.write(f"- {field}: {getattr(cm, field, 0.0):.4f}\n")
            f.write("\n## Module Latency\n\n")
            for pm in result.per_module:
                f.write(f"- {pm.module_name}: {pm.latency_ms:.4f}ms\n")
            f.write(f"\n- Total: {result.total_latency_ms:.2f}ms\n")
            f.write(f"- Throughput: {result.throughput:.2f} samples/s\n")
        return path

    def generate_routing_report(self, routing_metrics: dict[str, Any]) -> Path:
        path = self.output_dir / "routing_report.md"
        with open(path, "w") as f:
            f.write("# Routing Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            for k, v in routing_metrics.items():
                f.write(f"- {k}: {v}\n")
        return path

    def generate_memory_report(self, memory_metrics: dict[str, Any]) -> Path:
        path = self.output_dir / "memory_report.md"
        with open(path, "w") as f:
            f.write("# Memory Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            for k, v in memory_metrics.items():
                f.write(f"- {k}: {v}\n")
        return path

    def generate_calibration_report(self, calibration_data: dict[str, Any]) -> Path:
        path = self.output_dir / "calibration_report.md"
        with open(path, "w") as f:
            f.write("# Confidence Calibration Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"- ECE: {calibration_data.get('ece', 0.0):.4f}\n")
            f.write(f"- MCE: {calibration_data.get('mce', 0.0):.4f}\n")
            if "bin_centers" in calibration_data:
                f.write("\n## Reliability Data\n\n")
                f.write("| Bin Center | Accuracy | Confidence | Count |\n")
                f.write("|------------|----------|------------|-------|\n")
                for i in range(len(calibration_data["bin_centers"])):
                    f.write(
                        f"| {calibration_data['bin_centers'][i]:.3f} "
                        f"| {calibration_data['bin_accuracies'][i]:.3f} "
                        f"| {calibration_data['bin_confidences'][i]:.3f} "
                        f"| {calibration_data['bin_counts'][i]} |\n"
                    )
        return path

    def generate_explainability_report(self, explainability_data: dict[str, Any]) -> Path:
        path = self.output_dir / "explainability_report.md"
        with open(path, "w") as f:
            f.write("# Explainability Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            for k, v in explainability_data.items():
                f.write(f"- {k}: {v}\n")
        return path

    def generate_summary_report(self, all_data: dict[str, Any]) -> Path:
        path = self.output_dir / "evaluation_summary.md"
        with open(path, "w") as f:
            f.write("# ARES Evaluation Summary\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            for section, data in all_data.items():
                f.write(f"## {section}\n\n")
                if isinstance(data, dict):
                    for k, v in data.items():
                        f.write(f"- {k}: {v}\n")
                elif isinstance(data, list):
                    for item in data:
                        f.write(f"- {item}\n")
                else:
                    f.write(f"{data}\n")
                f.write("\n")
        return path
