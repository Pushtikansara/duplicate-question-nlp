from __future__ import annotations

import json
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from ares.cli.app import app
from ares.cli.commands.config import (
    _get_global_config_path,
    _get_project_config_path,
    _load_config_section,
)

runner = CliRunner()


class TestConfig:
    def test_get_global_config_path(self):
        path = _get_global_config_path()
        assert str(path).endswith(".ares/config.toml")

    def test_get_project_config_path(self):
        path = _get_project_config_path()
        assert str(path).endswith(".ares.toml")

    def test_load_config_section(self):
        cfg = _load_config_section("app")
        assert isinstance(cfg, dict)

    def test_load_config_section_nonexistent(self):
        cfg = _load_config_section("nonexistent_section_xyz")
        assert isinstance(cfg, dict)

    def test_show_config(self):
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0

    def test_show_config_section(self):
        result = runner.invoke(app, ["config", "show", "app"])
        assert result.exit_code == 0

    def test_show_config_verbose(self):
        result = runner.invoke(app, ["config", "show", "--verbose"])
        assert result.exit_code == 0

    def test_validate_config(self):
        result = runner.invoke(app, ["config", "validate"])
        assert result.exit_code == 0

    def test_export_config_json(self, tmp_path):
        out = tmp_path / "config.json"
        result = runner.invoke(app, ["config", "export", str(out), "--format", "json"])
        assert result.exit_code == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert isinstance(data, dict)

    def test_export_config_yaml(self, tmp_path):
        out = tmp_path / "config.yaml"
        result = runner.invoke(app, ["config", "export", str(out), "--format", "yaml"])
        assert result.exit_code == 0
        assert out.exists()
        data = yaml.safe_load(out.read_text())
        assert isinstance(data, dict)

    def test_edit_config(self):
        with patch("subprocess.run") as mock_run:
            with patch.dict("os.environ", {"EDITOR": "vim"}):
                result = runner.invoke(app, ["config", "edit"])
                assert result.exit_code == 0
                mock_run.assert_called_once()

    def test_edit_config_default_editor(self):
        with patch("subprocess.run") as mock_run:
            with patch.dict("os.environ", {}, clear=True):
                result = runner.invoke(app, ["config", "edit"])
                assert result.exit_code == 0
                args = mock_run.call_args[0][0]
                assert args[0] == "vi"

    def test_config_global_path_home(self):
        path = _get_global_config_path()
        assert ".ares" in str(path)

    def test_config_project_path_cwd(self):
        path = _get_project_config_path()
        assert ".ares.toml" in str(path)
