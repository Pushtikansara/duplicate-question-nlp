from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from duplicate_question_app._evaluation.ablation_engine import AblationEngine
from duplicate_question_app._evaluation.benchmark_result import (
    BenchmarkResult,
    ClassificationMetrics,
    PerModuleMetrics,
)
from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner
from duplicate_question_app._evaluation.calibration_metrics import (
    compute_brier_score,
    compute_confidence_histogram,
    compute_reliability_diagram,
)
from duplicate_question_app._evaluation.configuration import AblationConfig, BenchmarkConfig, EvaluationConfig
from duplicate_question_app._evaluation.debate_metrics import compute_debate_metrics
from duplicate_question_app._evaluation.error_analyzer import ErrorAnalyzer
from duplicate_question_app._evaluation.evaluation_engine import EvaluationEngine
from duplicate_question_app._evaluation.evaluator import Evaluator
from duplicate_question_app._evaluation.explainability_metrics import (
    compute_explainability_score,
    compute_reasoning_completeness,
)
from duplicate_question_app._evaluation.latency_profiler import LatencyProfiler
from duplicate_question_app._evaluation.memory_metrics import compute_memory_metrics
from duplicate_question_app._evaluation.memory_profiler import MemoryProfiler
from duplicate_question_app._evaluation.reasoning_metrics import compute_reasoning_metrics
from duplicate_question_app._evaluation.report_generator import ReportGenerator
from duplicate_question_app._evaluation.routing_metrics import compute_routing_metrics
from duplicate_question_app._evaluation.visualization import (
    plot_latency_breakdown,
    plot_module_contribution,
)


class TestEvaluationConfig:
    def test_default_config(self):
        cfg = EvaluationConfig()
        assert cfg.benchmark is not None
        assert cfg.ablation is not None
        assert cfg.classification_metrics is True

    def test_custom_benchmark_config(self):
        bc = BenchmarkConfig(name="test", num_runs=5)
        assert bc.name == "test"
        assert bc.num_runs == 5

    def test_ablation_config(self):
        ac = AblationConfig(modules_to_skip=["semantic", "made"])
        assert "semantic" in ac.modules_to_skip
        assert "made" in ac.modules_to_skip


class TestBenchmarkResult:
    def test_classification_metrics_to_dict(self):
        cm = ClassificationMetrics(accuracy=0.95, f1=0.94)
        d = cm.to_dict()
        assert d["accuracy"] == 0.95
        assert d["f1"] == 0.94

    def test_benchmark_result_to_dict(self):
        br = BenchmarkResult(config_name="test", modules_enabled=["ce"])
        d = br.to_dict()
        assert d["config_name"] == "test"
        assert d["modules_enabled"] == ["ce"]

    def test_per_module_metrics(self):
        pm = PerModuleMetrics(module_name="semantic", latency_ms=12.5)
        assert pm.module_name == "semantic"
        assert pm.latency_ms == 12.5


class TestLatencyProfiler:
    def test_measure_context(self):
        profiler = LatencyProfiler()
        with profiler.measure("test"):
            pass
        assert profiler.get_module_latency("test") > 0

    def test_multiple_measurements(self):
        profiler = LatencyProfiler()
        with profiler.measure("a"):
            pass
        with profiler.measure("b"):
            pass
        assert profiler.get_module_latency("a") > 0
        assert profiler.get_module_latency("b") > 0

    def test_summary(self):
        profiler = LatencyProfiler()
        with profiler.measure("x"):
            pass
        summary = profiler.get_summary()
        assert "total_ms" in summary
        assert "modules" in summary


class TestMemoryProfiler:
    def test_snapshot(self):
        profiler = MemoryProfiler()
        profiler.start()
        profiler.snapshot("test")
        assert len(profiler.snapshots) == 1

    def test_clear(self):
        profiler = MemoryProfiler()
        profiler.start()
        profiler.snapshot("test")
        profiler.clear()
        assert len(profiler.snapshots) == 0


class TestCalibrationMetrics:
    def test_brier_score_perfect(self):
        score = compute_brier_score(np.array([1, 0, 1]), np.array([1.0, 0.0, 1.0]))
        assert score == 0.0

    def test_brier_score_worst(self):
        score = compute_brier_score(np.array([1, 0]), np.array([0.0, 1.0]))
        assert score == 1.0

    def test_reliability_diagram(self):
        y_true = np.array([1, 0, 1, 0, 1])
        y_prob = np.array([0.9, 0.1, 0.8, 0.2, 0.7])
        diagram = compute_reliability_diagram(y_true, y_prob, n_bins=5)
        assert "ece" in diagram
        assert "mce" in diagram
        assert len(diagram["bin_centers"]) == 5

    def test_confidence_histogram(self):
        y_prob = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        hist = compute_confidence_histogram(y_prob, n_bins=10)
        assert "counts" in hist
        assert len(hist["edges"]) == 11


class TestErrorAnalyzer:
    def test_analyze_single(self):
        analyzer = ErrorAnalyzer()
        result = analyzer.analyze_single(
            q1="What is Python?",
            q2="What is Java?",
            predicted_label=1,
            prob_duplicate=0.95,
            true_label=0,
        )
        assert result["q1"] == "What is Python?"
        assert result["q2"] == "What is Java?"
        assert result["is_error"] is True
        assert len(result["error_categories"]) > 0

    def test_analyze_batch(self):
        analyzer = ErrorAnalyzer()
        df = pd.DataFrame(
            {
                "q1": ["What is Python?", "How to code?"],
                "q2": ["What is Java?", "How to program?"],
                "predicted_label": [1, 0],
                "prob_duplicate": [0.95, 0.10],
                "true_label": [0, 1],
            }
        )
        result = analyzer.analyze_batch(df)
        assert len(result) == 2


class TestExplainabilityMetrics:
    def test_reasoning_completeness_none(self):
        assert compute_reasoning_completeness(None) == 0.0

    def test_explainability_score_defaults(self):
        score = compute_explainability_score()
        assert score["overall"] == 0.0


class TestModuleMetrics:
    def test_routing_metrics_empty(self):
        metrics = compute_routing_metrics([])
        assert metrics["total_routes"] == 0

    def test_reasoning_metrics_empty(self):
        metrics = compute_reasoning_metrics([])
        assert metrics["total_reasoned"] == 0

    def test_debate_metrics_empty(self):
        metrics = compute_debate_metrics([])
        assert metrics["total_debates"] == 0

    def test_memory_metrics_none(self):
        metrics = compute_memory_metrics(None)
        assert metrics["available"] is False


class TestEvaluator:
    def test_evaluate_predictions(self):
        evaluator = Evaluator()
        y_true = np.array([1, 0, 1, 0, 1])
        y_pred = np.array([1, 0, 1, 0, 1])
        y_prob = np.array([0.9, 0.1, 0.85, 0.15, 0.95])
        result = evaluator.evaluate_predictions(y_true, y_pred, y_prob, config_name="test")
        assert result.config_name == "test"
        assert result.classification.accuracy == 1.0
        assert result.classification.f1 == 1.0

    def test_compare_configs(self):
        evaluator = Evaluator()
        y_true = np.array([1, 0, 1])
        evaluator.evaluate_predictions(y_true, y_true, np.array([0.9, 0.1, 0.9]), config_name="a")
        evaluator.evaluate_predictions(y_true, y_true, np.array([0.8, 0.2, 0.8]), config_name="b")
        df = evaluator.compare_configs()
        assert len(df) == 2
        assert "Config" in df.columns


class TestBenchmarkRunner:
    def test_configurations_exist(self):
        runner = BenchmarkRunner()
        assert "baseline" in runner.CONFIGURATIONS
        assert "config_a" in runner.CONFIGURATIONS
        assert "config_b" in runner.CONFIGURATIONS
        assert "config_c" in runner.CONFIGURATIONS
        assert "config_d_full" in runner.CONFIGURATIONS

    def test_run_configuration(self):
        runner = BenchmarkRunner()
        test_pairs = [("q1", "q2", 1), ("q3", "q4", 0)]
        result = runner.run_configuration("baseline", test_pairs=test_pairs)
        assert result.num_samples == 2
        assert result.config_name == "baseline"


class TestAblationEngine:
    def test_ablation_configs_exist(self):
        engine = AblationEngine()
        assert "no_routing" in engine.ABLATION_MODULES
        assert "no_semantic" in engine.ABLATION_MODULES
        assert "no_reasoning" in engine.ABLATION_MODULES
        assert "no_made" in engine.ABLATION_MODULES
        assert "no_memory" in engine.ABLATION_MODULES


class TestReportGenerator:
    def test_generate_comparison_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            gen = ReportGenerator(tmp)
            df = pd.DataFrame({"Config": ["a"], "F1": [0.95]})
            path = gen.generate_comparison_table(df)
            assert Path(path).exists()

    def test_generate_calibration_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            gen = ReportGenerator(tmp)
            data = {
                "ece": 0.05,
                "mce": 0.10,
                "bin_centers": [0.5],
                "bin_accuracies": [0.5],
                "bin_confidences": [0.5],
                "bin_counts": [10],
            }
            path = gen.generate_calibration_report(data)
            assert Path(path).exists()


class TestVisualization:
    def test_latency_breakdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "latency.png"
            plot_latency_breakdown({"a": 1.0, "b": 2.0}, path)
            assert path.exists()

    def test_module_contribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contribution.png"
            plot_module_contribution([{"module": "a", "f1_delta": 0.05}], path)
            assert path.exists()


class TestEvaluationEngine:
    def test_initialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = EvaluationEngine(output_dir=tmp)
            assert engine.config is not None
            assert engine.evaluator is not None

    def test_run_full_evaluation_with_df(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = EvaluationEngine(output_dir=tmp)
            df = pd.DataFrame(
                {
                    "q1": ["a", "b"],
                    "q2": ["c", "d"],
                    "true_label": [1, 0],
                    "predicted_label": [1, 0],
                    "prob_duplicate": [0.9, 0.1],
                }
            )
            results = engine.run_full_evaluation(predictions_df=df)
            assert "classification" in results
            assert "calibration" in results
