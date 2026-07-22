from __future__ import annotations

import pytest


class TestHealthEndpoint:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_health_returns_200(self, test_client):
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.api
    def test_health_returns_status_field(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "status" in data

    @pytest.mark.api
    def test_health_returns_healthy_or_degraded(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert data["status"] in ("healthy", "degraded")

    @pytest.mark.api
    def test_health_returns_version(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    @pytest.mark.api
    def test_health_returns_uptime(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], float)

    @pytest.mark.api
    def test_health_returns_components(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "components" in data
        assert isinstance(data["components"], dict)

    @pytest.mark.api
    def test_health_returns_checks(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "checks" in data
        assert isinstance(data["checks"], dict)

    @pytest.mark.api
    def test_health_returns_request_id(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "request_id" in data

    @pytest.mark.api
    def test_health_components_contain_app(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "app" in data["components"]

    @pytest.mark.api
    def test_health_components_contain_torch(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "torch" in data["components"]


class TestVersionEndpoint:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_version_returns_200(self, test_client):
        response = test_client.get("/api/v1/version")
        assert response.status_code == 200

    @pytest.mark.api
    def test_version_returns_version_string(self, test_client):
        response = test_client.get("/api/v1/version")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    @pytest.mark.api
    def test_version_returns_python_version(self, test_client):
        response = test_client.get("/api/v1/version")
        data = response.json()
        assert "python_version" in data
        assert isinstance(data["python_version"], str)

    @pytest.mark.api
    def test_version_returns_platform(self, test_client):
        response = test_client.get("/api/v1/version")
        data = response.json()
        assert "platform" in data
        assert isinstance(data["platform"], str)

    @pytest.mark.api
    def test_version_returns_api_version(self, test_client):
        response = test_client.get("/api/v1/version")
        data = response.json()
        assert "api_version" in data
        assert data["api_version"] == "1.0.0"

    @pytest.mark.api
    def test_version_returns_request_id(self, test_client):
        response = test_client.get("/api/v1/version")
        data = response.json()
        assert "request_id" in data
        assert isinstance(data["request_id"], str)

    @pytest.mark.api
    def test_version_response_shape(self, test_client):
        response = test_client.get("/api/v1/version")
        data = response.json()
        expected_keys = {"version", "python_version", "platform", "api_version", "build", "timestamp", "request_id"}
        assert expected_keys.issubset(data.keys())

    @pytest.mark.api
    def test_version_build_can_be_none(self, test_client):
        response = test_client.get("/api/v1/version")
        data = response.json()
        assert data["build"] is None or isinstance(data["build"], str)

    @pytest.mark.api
    def test_health_uses_get_method(self, test_client):
        response = test_client.post("/api/v1/health")
        assert response.status_code == 405

    @pytest.mark.api
    def test_version_uses_get_method(self, test_client):
        response = test_client.post("/api/v1/version")
        assert response.status_code == 405
