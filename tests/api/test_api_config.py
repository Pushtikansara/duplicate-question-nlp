from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.api
class TestConfigEndpoint:
    def test_get_config_returns_sections(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._config.loader.load_all_configs") as mock_load:
            mock_load.return_value = {
                "app": {"key": "val"},
                "paths": {"data": "/tmp"},
                "inference": {"threshold": 0.5},
                "logging": {"level": "info"},
            }
            response = test_client.get("/api/v1/config", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sections" in data
        assert isinstance(data["sections"], dict)

    def test_get_config_with_section_param(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._config.loader.load_all_configs") as mock_load:
            mock_load.return_value = {"app": {"key": "val"}, "inference": {"threshold": 0.5}}
            response = test_client.get("/api/v1/config?section=app", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sections" in data

    def test_get_config_with_verbose(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._config.loader.load_all_configs") as mock_load:
            mock_load.return_value = {"app": {"key": "val"}, "other": {"nested": True}}
            response = test_client.get("/api/v1/config?verbose=true", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_get_config_returns_source(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._config.loader.load_all_configs") as mock_load:
            mock_load.return_value = {"app": {}}
            response = test_client.get("/api/v1/config", headers=admin_auth_headers)
        data = response.json()
        assert "source" in data
        assert data["source"] == "yaml"

    def test_get_config_returns_request_id(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._config.loader.load_all_configs") as mock_load:
            mock_load.return_value = {"app": {}}
            response = test_client.get("/api/v1/config", headers=admin_auth_headers)
        data = response.json()
        assert "request_id" in data

    def test_get_config_without_auth_returns_401(self, test_client):
        response = test_client.get("/api/v1/config")
        assert response.status_code == 401

    def test_get_config_with_user_returns_403(self, test_client, auth_headers):
        response = test_client.get("/api/v1/config", headers=auth_headers)
        assert response.status_code == 403

    def test_get_config_nonexistent_section_returns_404(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._config.loader.load_all_configs") as mock_load:
            mock_load.return_value = {"app": {}}
            response = test_client.get("/api/v1/config?section=nonexistent", headers=admin_auth_headers)
        assert response.status_code == 404


@pytest.mark.api
class TestConfigValidateEndpoint:
    def test_validate_config_returns_valid(self, test_client, admin_auth_headers):
        mock_config_dir = MagicMock()
        mock_config_dir.exists.return_value = True
        mock_config_dir.glob.return_value = []
        mock_cwd = MagicMock()
        mock_cwd.__truediv__.return_value = mock_config_dir
        with patch("ares.api.routers.config.Path.cwd", return_value=mock_cwd):
            response = test_client.post("/api/v1/config/validate", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert isinstance(data["valid"], bool)

    def test_validate_config_no_config_dir(self, test_client, admin_auth_headers):
        mock_config_dir = MagicMock()
        mock_config_dir.exists.return_value = False
        mock_cwd = MagicMock()
        mock_cwd.__truediv__.return_value = mock_config_dir
        with patch("ares.api.routers.config.Path.cwd", return_value=mock_cwd):
            response = test_client.post("/api/v1/config/validate", headers=admin_auth_headers)
        data = response.json()
        assert data["valid"] is False
        assert "configs/ directory not found" in data["errors"]

    def test_validate_config_returns_warnings(self, test_client, admin_auth_headers):
        mock_config_dir = MagicMock()
        mock_config_dir.exists.return_value = True
        mock_config_dir.glob.return_value = []
        mock_cwd = MagicMock()
        mock_cwd.__truediv__.return_value = mock_config_dir
        with patch("ares.api.routers.config.Path.cwd", return_value=mock_cwd):
            response = test_client.post("/api/v1/config/validate", headers=admin_auth_headers)
        data = response.json()
        assert "warnings" in data

    def test_validate_config_returns_errors(self, test_client, admin_auth_headers):
        mock_config_dir = MagicMock()
        mock_config_dir.exists.return_value = True
        mock_config_dir.glob.return_value = []
        mock_cwd = MagicMock()
        mock_cwd.__truediv__.return_value = mock_config_dir
        with patch("ares.api.routers.config.Path.cwd", return_value=mock_cwd):
            response = test_client.post("/api/v1/config/validate", headers=admin_auth_headers)
        data = response.json()
        assert "errors" in data

    def test_validate_config_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/config/validate")
        assert response.status_code == 401

    def test_validate_config_with_valid_yaml(self, test_client, admin_auth_headers):
        mock_yaml_file = MagicMock()
        mock_yaml_file.name = "test.yaml"
        mock_config_dir = MagicMock()
        mock_config_dir.exists.return_value = True
        mock_config_dir.glob.return_value = [mock_yaml_file]
        mock_cwd = MagicMock()
        mock_cwd.__truediv__.return_value = mock_config_dir
        with patch("ares.api.routers.config.Path.cwd", return_value=mock_cwd):
            with patch("builtins.open", MagicMock()):
                with patch("yaml.safe_load", return_value={}):
                    response = test_client.post("/api/v1/config/validate", headers=admin_auth_headers)
                    data = response.json()
                    assert data["valid"] is True
