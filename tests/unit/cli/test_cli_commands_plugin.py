from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from ares.cli.app import app
from ares.cli.commands.plugin import (
    _get_manager,
    _get_output,
)

runner = CliRunner()


@pytest.fixture
def mock_manager():
    with patch("ares.cli.commands.plugin.PluginManager") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_plugin():
    plugin = MagicMock()
    plugin.plugin_id = "test_plugin"
    plugin.status.name = "ACTIVE"
    plugin.metadata.name = "Test Plugin"
    plugin.metadata.version = "1.0.0"
    plugin.metadata.priority = 5
    plugin.metadata.author = "Author"
    plugin.metadata.description = "A test plugin"
    plugin.metadata.license = "MIT"
    plugin.metadata.capabilities = [MagicMock()]
    plugin.metadata.capabilities[0].name = "TEST"
    plugin.metadata.dependencies = []
    return plugin


class TestPlugin:
    def test_get_manager(self, mock_manager):
        pm = _get_manager()
        assert pm is not None

    def test_get_output(self, mock_plugin):
        output = _get_output(mock_plugin)
        assert output["id"] == "test_plugin"
        assert output["name"] == "Test Plugin"
        assert output["version"] == "1.0.0"
        assert output["status"] == "ACTIVE"

    def test_list_plugins(self, mock_manager, mock_plugin):
        mock_manager.list.return_value = [mock_plugin]
        result = runner.invoke(app, ["plugin", "list"])
        assert result.exit_code == 0
        assert "test_plugin" in result.output

    def test_list_plugins_empty(self, mock_manager):
        mock_manager.list.return_value = []
        result = runner.invoke(app, ["plugin", "list"])
        assert "No plugins found" in result.output

    def test_list_plugins_with_status_filter(self):
        from ares.plugins.types import PluginStatus

        with patch("ares.cli.commands.plugin.PluginManager") as mock_pm:
            mock_plugin = MagicMock()
            mock_plugin.plugin_id = "test_plugin"
            mock_plugin.status = PluginStatus.ACTIVE
            mock_plugin.metadata.name = "Test"
            mock_plugin.metadata.version = "1.0"
            mock_plugin.metadata.priority = 5
            mock_plugin.metadata.capabilities = []
            mock_plugin.metadata.dependencies = []
            instance = MagicMock()
            instance.list.return_value = [mock_plugin]
            mock_pm.return_value = instance
            result = runner.invoke(app, ["plugin", "list", "--status", "ACTIVE"])
            assert result.exit_code == 0
            assert "test_plugin" in result.output

    def test_uninstall_plugin_force(self, mock_manager):
        result = runner.invoke(app, ["plugin", "uninstall", "test_plugin", "--force"])
        assert result.exit_code == 0

    def test_enable_plugin(self, mock_manager):
        result = runner.invoke(app, ["plugin", "enable", "test_plugin"])
        assert result.exit_code == 0
        assert "Enabled" in result.output
        mock_manager.enable.assert_called_once_with("test_plugin")

    def test_disable_plugin(self, mock_manager):
        result = runner.invoke(app, ["plugin", "disable", "test_plugin"])
        assert result.exit_code == 0
        assert "Disabled" in result.output
        mock_manager.disable.assert_called_once_with("test_plugin")

    def test_inspect_plugin(self, mock_manager, mock_plugin):
        mock_manager.get.return_value = mock_plugin
        result = runner.invoke(app, ["plugin", "inspect", "test_plugin"])
        assert result.exit_code == 0
        assert "test_plugin" in result.output
        assert "Test Plugin" in result.output

    def test_search_plugins(self, mock_manager, mock_plugin):
        mock_manager.list.return_value = [mock_plugin]
        result = runner.invoke(app, ["plugin", "search", "test"])
        assert result.exit_code == 0
        assert "test_plugin" in result.output

    def test_search_plugins_no_results(self, mock_manager):
        plugin = MagicMock()
        plugin.plugin_id = "other"
        plugin.metadata.name = "Other"
        plugin.metadata.description = ""
        plugin.metadata.version = "1.0"
        plugin.status.name = "ACTIVE"
        mock_manager.list.return_value = [plugin]
        result = runner.invoke(app, ["plugin", "search", "nonexistent"])
        assert "No plugins matching" in result.output
