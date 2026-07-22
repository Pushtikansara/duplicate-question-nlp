from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ares.cli.app import app

runner = CliRunner()


class TestServe:
    def test_start_server_with_app_path(self):
        with patch("subprocess.run") as mock_run:
            result = runner.invoke(app, ["serve", "--app", "app/app.py", "--host", "0.0.0.0", "--port", "8080"])
            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_start_server_dev_mode(self):
        with patch("subprocess.run") as mock_run:
            result = runner.invoke(app, ["serve", "--app", "app/app.py", "--dev", "--port", "8501"])
            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_start_server_without_app_path(self):
        with patch("run_app.main") as mock_main:
            result = runner.invoke(app, ["serve"])
            assert result.exit_code == 0
            mock_main.assert_called_once()
