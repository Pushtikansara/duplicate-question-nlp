from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

PROFILE_PAYLOAD = {
    "duration_seconds": 5,
    "include_memory": True,
    "include_cpu": True,
}


@pytest.mark.api
class TestProfileEndpoint:
    def test_profile_returns_200(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._profiling.Profiler") as MockProfiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            MockProfiler.return_value = instance
            response = test_client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=admin_auth_headers)
        assert response.status_code == 200

    def test_profile_returns_profile_data(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._profiling.Profiler") as MockProfiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            MockProfiler.return_value = instance
            response = test_client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=admin_auth_headers)
        data = response.json()
        assert "profile" in data
        assert isinstance(data["profile"], dict)

    def test_profile_returns_functions_list(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._profiling.Profiler") as MockProfiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            MockProfiler.return_value = instance
            response = test_client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=admin_auth_headers)
        data = response.json()
        assert "functions" in data
        assert isinstance(data["functions"], list)

    def test_profile_returns_total_time(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._profiling.Profiler") as MockProfiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            MockProfiler.return_value = instance
            response = test_client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=admin_auth_headers)
        data = response.json()
        assert "total_time_ms" in data

    def test_profile_returns_request_id(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._profiling.Profiler") as MockProfiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            MockProfiler.return_value = instance
            response = test_client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=admin_auth_headers)
        data = response.json()
        assert "request_id" in data

    def test_profile_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/profile", json=PROFILE_PAYLOAD)
        assert response.status_code == 401

    def test_profile_with_user_returns_403(self, test_client, auth_headers):
        response = test_client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=auth_headers)
        assert response.status_code == 403


@pytest.mark.api
class TestProfileMetricsEndpoint:
    def test_profile_metrics_returns_dict(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._profiling.Profiler") as MockProfiler:
            instance = MagicMock()
            instance.get_stats.return_value = {}
            MockProfiler.return_value = instance
            response = test_client.get("/api/v1/profile/metrics", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_profile_metrics_without_auth_returns_401(self, test_client):
        response = test_client.get("/api/v1/profile/metrics")
        assert response.status_code == 401
