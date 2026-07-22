from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.api
class TestSystemInfoEndpoint:
    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_200(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        assert response.status_code == 200

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_version(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_python_version(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "python_version" in data

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_platform(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "platform" in data

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_cpu_cores(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "cpu_cores" in data
        assert isinstance(data["cpu_cores"], int)

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_memory_gb(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "memory_gb" in data
        assert isinstance(data["memory_gb"], float)

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_gpu_available(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "gpu_available" in data
        assert data["gpu_available"] is False

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_dependencies(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "dependencies" in data
        assert isinstance(data["dependencies"], dict)

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_config_file_count(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "config_file_count" in data

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_uptime(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "uptime_seconds" in data

    @patch("ares.api.routers.system.psutil.virtual_memory")
    @patch("ares.api.routers.system.torch.cuda.is_available")
    def test_system_info_returns_request_id(self, mock_cuda, mock_mem, test_client, admin_auth_headers):
        mock_cuda.return_value = False
        mock_mem.return_value.total = 8 * 1024**3
        response = test_client.get("/api/v1/system/info", headers=admin_auth_headers)
        data = response.json()
        assert "request_id" in data

    def test_system_info_without_auth_returns_401(self, test_client):
        response = test_client.get("/api/v1/system/info")
        assert response.status_code == 401

    def test_system_info_with_user_returns_403(self, test_client, auth_headers):
        response = test_client.get("/api/v1/system/info", headers=auth_headers)
        assert response.status_code == 403
