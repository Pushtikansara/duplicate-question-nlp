from __future__ import annotations

import json

from typer.testing import CliRunner

from ares.cli.app import app
from ares.cli.commands.export import (
    _export_config,
    _export_plugins,
    _export_stats,
    _export_version,
)

runner = CliRunner()


class TestExport:
    def test_export_version(self):
        result = _export_version()
        assert "ares" in result
        assert "python" in result

    def test_export_config(self):
        result = _export_config()
        assert isinstance(result, dict)

    def test_export_plugins(self):
        result = _export_plugins()
        assert isinstance(result, list)

    def test_export_stats(self):
        result = _export_stats()
        assert isinstance(result, dict)

    def test_export_cmd(self, tmp_path):
        out = tmp_path / "export.json"
        result = runner.invoke(app, ["export", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert "version" in data

    def test_export_custom_sections(self, tmp_path):
        out = tmp_path / "partial.json"
        result = runner.invoke(app, ["export", str(out), "--sections", "version,config"])
        assert result.exit_code == 0
        assert out.exists()

    def test_export_cmd_yaml(self, tmp_path):
        out = tmp_path / "export.yaml"
        result = runner.invoke(app, ["export", str(out), "--format", "yaml"])
        assert result.exit_code == 0
        assert out.exists()
