from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BenchmarkConfig:
    name: str = "default"
    description: str = ""
    batch_size: int = 32
    num_runs: int = 3
    warmup_runs: int = 2
    timeout_seconds: int = 300
    output_dir: str = "evaluation_results"


@dataclass
class AblationConfig:
    modules_to_skip: list[str] = field(default_factory=list)
    rerun_baseline: bool = True
    compare_all: bool = True
    output_dir: str = "ablation_results"


@dataclass
class EvaluationConfig:
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)
    ablation: AblationConfig = field(default_factory=AblationConfig)
    classification_metrics: bool = True
    performance_metrics: bool = True
    module_specific_metrics: bool = True
    confidence_calibration: bool = True
    error_analysis: bool = True
    explainability_scoring: bool = True
    generate_plots: bool = True
    generate_reports: bool = True
    export_csv: bool = True
    export_json: bool = True
    export_markdown: bool = True
    export_html: bool = True
    output_dir: str = "evaluation_results"
    seed: int = 42
