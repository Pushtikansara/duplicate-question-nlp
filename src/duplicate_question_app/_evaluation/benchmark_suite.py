from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner
from duplicate_question_app._evaluation.configuration import EvaluationConfig
from duplicate_question_app._evaluation.report_generator import ReportGenerator


class BenchmarkSuite:
    def __init__(
        self,
        config: EvaluationConfig | None = None,
        output_dir: str = "evaluation_results",
    ) -> None:
        self.config = config or EvaluationConfig()
        self.runner = BenchmarkRunner(self.config)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        prediction_fn: Callable[[str, str], dict[str, Any]] | None = None,
        test_pairs: list[tuple[str, str, int]] | None = None,
    ) -> dict[str, Any]:
        if test_pairs is None:
            test_pairs = []

        results = self.runner.run_all_configurations(prediction_fn, test_pairs)

        comparison = self.runner.get_comparison()

        comparison_path = self.output_dir / "benchmark_comparison.csv"
        comparison.to_csv(comparison_path, index=False)

        summary = {
            "timestamp": datetime.now().isoformat(),
            "num_configs": len(results),
            "num_test_pairs": len(test_pairs),
            "configs": {name: r.to_dict() for name, r in results.items()},
        }
        summary_path = self.output_dir / "benchmark_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        report_gen = ReportGenerator(self.output_dir)
        report_gen.generate_comparison_table(comparison)
        report_gen.generate_benchmark_report(results, comparison)

        return summary
