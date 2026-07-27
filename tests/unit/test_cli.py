from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from duplicate_question_app.cli import _ensure_project_root, main


class TestCLI:
    def test_ensure_project_root_returns_path(self):
        root = _ensure_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_main_output(self, capsys):
        with patch.object(sys, "argv", ["dqd"]):
            main()
            captured = capsys.readouterr()
            assert "Duplicate Question Detection" in captured.out
            assert "dqd-app" in captured.out

    def test_main_contains_version(self, capsys):
        with patch.object(sys, "argv", ["dqd"]):
            from duplicate_question_app import __version__

            main()
            captured = capsys.readouterr()
            assert __version__ in captured.out

    def test_run_app_imports(self):
        with patch("subprocess.run") as mock_run:
            from duplicate_question_app.cli import run_app

            run_app()
            mock_run.assert_called_once()

    @pytest.mark.cli
    def test_predict_no_file_exits(self):
        from duplicate_question_app.cli import predict

        with patch.object(sys, "argv", ["dqd-predict", "/nonexistent/file.csv"]):
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(SystemExit):
                    predict()

    def test_predict_with_csv_runs(self):
        import tempfile

        import pandas as pd

        from ares._result import PredictionResult

        df = pd.DataFrame({"question1": ["test"], "question2": ["test2"], "label": [1]})
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            fname = f.name
            df.to_csv(fname, index=False)
        fake_result = MagicMock(spec=PredictionResult)
        fake_result.predicted_label = 1
        fake_result.prediction = "Duplicate"
        fake_result.confidence = 0.9
        fake_result.prob_duplicate = 0.9
        fake_result.prob_non_duplicate = 0.1
        fake_result.model_name = "test"
        fake_result.latency_ms = 1.0
        with patch.object(sys, "argv", ["dqd-predict", fname]):
            with patch("duplicate_question_app.cli.InferenceDispatcher.predict", return_value=fake_result):
                from duplicate_question_app.cli import predict

                predict()

    def test_benchmark_imports(self):
        from duplicate_question_app.cli import benchmark

        with patch("subprocess.run") as mock_run, patch.object(sys, "argv", ["dqd-benchmark"]):
            # The benchmark script already exists from the Phase 5 commit
            benchmark()
            mock_run.assert_called_once()

    def test_predict_no_args(self):
        from duplicate_question_app.cli import predict

        with patch.object(sys, "argv", ["dqd-predict"]), pytest.raises((SystemExit, Exception)):
            predict()
