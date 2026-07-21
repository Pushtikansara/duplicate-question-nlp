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

        from duplicate_question_app._inference.transformer import ModelMetadata

        meta = ModelMetadata(
            model_dir=Path("/tmp"),
            model_label="T",
            model_version="1",
            decision_threshold=0.5,
            threshold_source="config",
            device="cpu",
            fallback_reason=None,
            load_errors=(),
            cache_key="k",
        )
        df = pd.DataFrame({"question1": ["test"], "question2": ["test2"], "label": [1]})
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            fname = f.name
            df.to_csv(fname, index=False)
        with patch.object(sys, "argv", ["dqd-predict", fname]):
            with patch("duplicate_question_app._inference.transformer.load_model_and_tokenizer") as mock_loader:
                mock_loader.return_value = (MagicMock(), MagicMock(), meta)
                with patch(
                    "duplicate_question_app._inference.transformer.DuplicateQuestionInferenceService"
                ) as mock_svc:
                    mock_instance = MagicMock()
                    mock_instance.predict_single.return_value = {
                        "predicted_label": 1,
                        "prob_duplicate": 0.9,
                        "prob_non_duplicate": 0.1,
                    }
                    mock_svc.return_value = mock_instance
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
