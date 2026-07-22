from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ares.cli.commands.inspect import inspect_cmd


class TestInspect:
    def test_inspect_cmd(self, capsys):
        with (
            patch("duplicate_question_app._config.settings.get_app_paths") as mock_paths,
            patch("duplicate_question_app._config.settings.resolve_model_selection") as mock_resolve,
            patch(
                "duplicate_question_app._config.settings.MODEL_CHOICES",
                [MagicMock()],
            ),
        ):
            paths = MagicMock()
            paths.project_root = "/root"
            paths.data_dir = "/data"
            paths.models_dir = "/models"
            paths.results_dir = "/results"
            paths.config_dir = "/config"
            paths.logs_dir = "/logs"
            mock_paths.return_value = paths

            resolution = MagicMock()
            resolution.selected_label = "Week 4"
            resolution.week4.ready = True
            resolution.week4.path = "/w4"
            resolution.week3.ready = True
            resolution.week3.path = "/w3"
            mock_resolve.return_value = resolution

            inspect_cmd()
            captured = capsys.readouterr()
            assert "ARES System Inspection" in captured.out
            assert "Model Status" in captured.out
            assert "Paths" in captured.out
            assert "Week 4" in captured.out

    def test_inspect_failure(self):
        with patch(
            "duplicate_question_app._config.settings.get_app_paths",
            side_effect=Exception("fail"),
        ):
            with pytest.raises(SystemExit):
                inspect_cmd()
