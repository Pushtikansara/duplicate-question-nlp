from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from duplicate_question_app._evaluation.ablation_engine import AblationEngine
from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner
from duplicate_question_app._evaluation.benchmark_suite import BenchmarkSuite
from duplicate_question_app._evaluation.calibration_metrics import (
    compute_confidence_histogram,
    compute_reliability_diagram,
)
from duplicate_question_app._evaluation.configuration import EvaluationConfig
from duplicate_question_app._evaluation.error_analyzer import ErrorAnalyzer
from duplicate_question_app._evaluation.evaluator import Evaluator
from duplicate_question_app._evaluation.latency_profiler import LatencyProfiler
from duplicate_question_app._evaluation.memory_profiler import MemoryProfiler
from duplicate_question_app._evaluation.metrics import (
    generate_evaluation_report,
)
from duplicate_question_app._evaluation.report_generator import ReportGenerator


class EvaluationEngine:
    def __init__(self, config: EvaluationConfig | None = None, output_dir: str = "evaluation_results") -> None:
        self.config = config or EvaluationConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.evaluator = Evaluator(self.config)
        self.latency_profiler = LatencyProfiler()
        self.memory_profiler = MemoryProfiler()
        self.error_analyzer = ErrorAnalyzer()
        self.report_gen = ReportGenerator(self.output_dir)
        self.benchmark_runner = BenchmarkRunner(self.config)
        self.benchmark_suite = BenchmarkSuite(self.config, str(self.output_dir))
        self.ablation_engine = AblationEngine(self.config.ablation)

    def run_full_evaluation(
        self,
        prediction_fn: Callable[[str, str], dict[str, Any]] | None = None,
        test_pairs: list[tuple[str, str, int]] | None = None,
        predictions_df: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config,
        }

        if predictions_df is not None:
            report_dir = self.output_dir / "evaluation_report"
            report_dir.mkdir(parents=True, exist_ok=True)
            eval_summary = generate_evaluation_report(
                predictions_df,
                report_dir,
                model_name="ARES",
                prob_col="prob_duplicate",
                pred_col="predicted_label",
                true_col="true_label",
            )
            results["classification"] = eval_summary

        if test_pairs and prediction_fn:
            benchmark_results = self.benchmark_suite.run(prediction_fn, test_pairs)
            results["benchmark"] = benchmark_results

        y_true_list = []
        y_prob_list = []

        if predictions_df is not None:
            y_true_list = (
                predictions_df["true_label"].values if "true_label" in predictions_df.columns else np.array([])
            )
            y_prob_list = (
                predictions_df["prob_duplicate"].values if "prob_duplicate" in predictions_df.columns else np.array([])
            )

        if len(y_true_list) > 0:
            cal_dir = self.output_dir / "calibration"
            cal_dir.mkdir(parents=True, exist_ok=True)
            cal_data = compute_reliability_diagram(np.array(y_true_list), np.array(y_prob_list))
            hist_data = compute_confidence_histogram(np.array(y_prob_list))
            results["calibration"] = {**cal_data, "confidence_histogram": hist_data}
            self.report_gen.generate_calibration_report(cal_data)

            error_df = self.error_analyzer.analyze_batch(
                predictions_df if predictions_df is not None else pd.DataFrame(),
            )
            if not error_df.empty:
                self.report_gen.generate_error_report(error_df)

        with open(self.output_dir / "evaluation_results.json", "w") as f:
            serializable = {}
            for k, v in results.items():
                if k != "config":
                    serializable[k] = v
            json.dump(serializable, f, indent=2, default=str)

        self.report_gen.generate_summary_report(results)
        return results
