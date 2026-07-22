from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ares.cli.app import app

runner = CliRunner()


class TestBenchmark:
    def test_run_benchmark(self):
        with (
            patch("duplicate_question_app._evaluation.benchmark_runner.BenchmarkRunner") as mock_runner,
            patch("duplicate_question_app._evaluation.benchmark_suite.BenchmarkSuite") as mock_suite,
        ):
            instance = MagicMock()
            mock_runner.return_value = instance
            suite_instance = MagicMock()
            suite_instance.run_all.return_value = {"test": "result"}
            mock_suite.return_value = suite_instance
            result = runner.invoke(app, ["benchmark", "run"])
            assert result.exit_code == 0
            assert "Benchmark complete" in result.output

    def test_run_benchmark_with_config(self):
        with (
            patch("duplicate_question_app._evaluation.benchmark_runner.BenchmarkRunner") as mock_runner,
            patch("duplicate_question_app._evaluation.benchmark_suite.BenchmarkSuite") as mock_suite,
        ):
            instance = MagicMock()
            mock_runner.return_value = instance
            suite_instance = MagicMock()
            suite_instance.run_configuration.return_value = {"config_test": "result"}
            mock_suite.return_value = suite_instance
            result = runner.invoke(app, ["benchmark", "run", "--config", "fast"])
            assert result.exit_code == 0
            assert "Benchmark complete" in result.output

    def test_run_benchmark_with_output(self, tmp_path):
        out = tmp_path / "bench.json"
        with (
            patch("duplicate_question_app._evaluation.benchmark_runner.BenchmarkRunner") as mock_runner,
            patch("duplicate_question_app._evaluation.benchmark_suite.BenchmarkSuite") as mock_suite,
        ):
            instance = MagicMock()
            mock_runner.return_value = instance
            suite_instance = MagicMock()
            suite_instance.run_all.return_value = {"test": "result"}
            mock_suite.return_value = suite_instance
            result = runner.invoke(app, ["benchmark", "run", "--output", str(out)])
            assert result.exit_code == 0
            assert out.exists()

    def test_list_benchmarks_empty(self):
        with patch("duplicate_question_app._evaluation.benchmark_runner.BenchmarkRunner") as mock_runner:
            instance = MagicMock()
            instance.get_results.return_value = {}
            mock_runner.return_value = instance
            result = runner.invoke(app, ["benchmark", "list"])
            assert "No benchmark results" in result.output

    def test_list_benchmarks_with_results(self):
        with patch("duplicate_question_app._evaluation.benchmark_runner.BenchmarkRunner") as mock_runner:
            instance = MagicMock()
            instance.get_results.return_value = {
                "test_config": {
                    "total_latency_ms": 100,
                    "accuracy": 0.95,
                    "samples": 100,
                }
            }
            mock_runner.return_value = instance
            result = runner.invoke(app, ["benchmark", "list"])
            assert result.exit_code == 0
            assert "test_config" in result.output

    def test_compare_benchmarks(self):
        with patch("duplicate_question_app._evaluation.benchmark_runner.BenchmarkRunner") as mock_runner:
            instance = MagicMock()
            instance.get_results.return_value = {
                "a": {"total_latency_ms": 100, "accuracy": 0.9, "samples": 50},
                "b": {"total_latency_ms": 200, "accuracy": 0.95, "samples": 100},
            }
            mock_runner.return_value = instance
            result = runner.invoke(app, ["benchmark", "compare", "a", "b"])
            assert result.exit_code == 0
            assert "Comparison:" in result.output

    def test_compare_benchmarks_not_found(self):
        with patch("duplicate_question_app._evaluation.benchmark_runner.BenchmarkRunner") as mock_runner:
            instance = MagicMock()
            instance.get_results.return_value = {}
            mock_runner.return_value = instance
            result = runner.invoke(app, ["benchmark", "compare", "a", "b"])
            assert result.exit_code != 0
