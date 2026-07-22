from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ares.cli.app import app
from ares.cli.commands.profile import _to_chrome_trace

runner = CliRunner()


class TestProfile:
    def test_generate_profile(self):
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {"func": {"calls": 5, "total_time_ms": 100, "avg_time_ms": 20}}
            instance.get_report.return_value = [{"name": "func", "timestamp": 0, "elapsed_ms": 100}]
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["profile"])
            assert result.exit_code == 0
            assert "Profile generated" in result.output

    def test_generate_profile_with_output(self, tmp_path):
        out = tmp_path / "profile.json"
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            instance.get_report.return_value = []
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["profile", "--output", str(out)])
            assert result.exit_code == 0
            assert out.exists()
            assert "Profile saved" in result.output

    def test_generate_profile_chrome(self, tmp_path):
        out = tmp_path / "chrome.json"
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            instance.get_report.return_value = [{"name": "f", "timestamp": 1, "elapsed_ms": 100}]
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["profile", "--output", str(out), "--format", "chrome"])
            assert result.exit_code == 0
            assert out.exists()

    def test_show_metrics(self):
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {"func_a": {"calls": 10, "total_time_ms": 500, "avg_time_ms": 50}}
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["metrics", "show"])
            assert result.exit_code == 0
            assert "Profile Metrics" in result.output
            assert "func_a" in result.output

    def test_show_metrics_empty(self):
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["metrics", "show"])
            assert result.exit_code == 0
            assert "No metrics available" in result.output

    def test_export_metrics(self, tmp_path):
        out = tmp_path / "metrics.json"
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {"func": {"calls": 1, "total_time_ms": 10, "avg_time_ms": 10}}
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["metrics", "export", str(out)])
            assert result.exit_code == 0
            assert out.exists()

    def test_show_stats(self):
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {
                "f1": {"calls": 5, "total_time_ms": 100, "avg_time_ms": 20},
                "f2": {"calls": 3, "total_time_ms": 50, "avg_time_ms": 16},
            }
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["stats", "show"])
            assert result.exit_code == 0
            assert "Runtime Statistics" in result.output
            assert "8" in result.output

    def test_show_stats_empty(self):
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["stats", "show"])
            assert result.exit_code == 0
            assert "No statistics available" in result.output

    def test_export_stats(self, tmp_path):
        out = tmp_path / "stats.json"
        with patch("duplicate_question_app._profiling.Profiler") as mock_profiler:
            instance = MagicMock()
            instance.get_stats.return_value = {"func": {"calls": 1}}
            mock_profiler.return_value = instance
            result = runner.invoke(app, ["stats", "export", str(out)])
            assert result.exit_code == 0
            assert out.exists()

    def test_to_chrome_trace(self):
        profiles = [
            {"name": "func1", "timestamp": 1.0, "elapsed_ms": 50},
            {"name": "func2", "timestamp": 1.5, "elapsed_ms": 30},
        ]
        events = _to_chrome_trace(profiles)
        assert len(events) == 2
        assert events[0]["name"] == "func1"
        assert events[0]["ph"] == "X"
        assert events[0]["dur"] == 50000
