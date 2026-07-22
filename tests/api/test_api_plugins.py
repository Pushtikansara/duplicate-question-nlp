from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.api
class TestPluginsEndpoint:
    def test_list_plugins_returns_list(self, test_client, admin_auth_headers):
        with patch("ares.plugins.manager.PluginManager") as MockPM:
            instance = MagicMock()
            instance.list.return_value = []
            MockPM.return_value = instance
            response = test_client.get("/api/v1/plugins", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_plugins_without_auth_returns_401(self, test_client):
        response = test_client.get("/api/v1/plugins")
        assert response.status_code == 401

    def test_list_plugins_with_user_returns_403(self, test_client, auth_headers):
        response = test_client.get("/api/v1/plugins", headers=auth_headers)
        assert response.status_code == 403

    def test_list_plugins_returns_plugin_data(self, test_client, admin_auth_headers):
        with patch("ares.plugins.manager.PluginManager") as MockPM:
            mock_plugin = MagicMock()
            mock_plugin.to_dict.return_value = {"id": "plugin-1", "name": "Test", "version": "1.0"}
            mock_plugin.name = "Test"
            mock_plugin.status = "active"
            mock_plugin.version = "1.0"
            instance = MagicMock()
            instance.list.return_value = [mock_plugin]
            MockPM.return_value = instance
            response = test_client.get("/api/v1/plugins", headers=admin_auth_headers)
        data = response.json()
        assert isinstance(data, list)

    def test_get_plugin_returns_detail(self, test_client, admin_auth_headers):
        with patch("ares.plugins.manager.PluginManager") as MockPM:
            mock_plugin = MagicMock()
            mock_plugin.to_dict.return_value = {"id": "plugin-1", "name": "Test Plugin"}
            instance = MagicMock()
            instance.get.return_value = mock_plugin
            MockPM.return_value = instance
            response = test_client.get("/api/v1/plugins/plugin-1", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_plugin_not_found_returns_404(self, test_client, admin_auth_headers):
        with patch("ares.plugins.manager.PluginManager") as MockPM:
            instance = MagicMock()
            instance.get.return_value = None
            MockPM.return_value = instance
            response = test_client.get("/api/v1/plugins/nonexistent", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_enable_plugin_returns_ok(self, test_client, admin_auth_headers):
        with patch("ares.plugins.manager.PluginManager") as MockPM:
            instance = MagicMock()
            instance.enable = MagicMock()
            MockPM.return_value = instance
            response = test_client.post("/api/v1/plugins/test-plugin/enable", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["action"] == "enabled"

    def test_disable_plugin_returns_ok(self, test_client, admin_auth_headers):
        with patch("ares.plugins.manager.PluginManager") as MockPM:
            instance = MagicMock()
            instance.disable = MagicMock()
            MockPM.return_value = instance
            response = test_client.post("/api/v1/plugins/test-plugin/disable", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["action"] == "disabled"

    def test_uninstall_plugin_returns_ok(self, test_client, admin_auth_headers):
        with patch("ares.plugins.manager.PluginManager") as MockPM:
            instance = MagicMock()
            instance.uninstall = MagicMock()
            MockPM.return_value = instance
            response = test_client.delete("/api/v1/plugins/test-plugin", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["action"] == "uninstalled"
