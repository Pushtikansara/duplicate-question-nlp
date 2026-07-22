from __future__ import annotations

from unittest.mock import patch

import pytest

from ares.api.dependencies import get_security_manager
from ares.api.models import UserRole


@pytest.mark.api
class TestAuthentication:
    def test_request_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/predict", json={"question1": "a", "question2": "b"})
        assert response.status_code == 401

    def test_request_without_auth_returns_401_detail(self, test_client):
        response = test_client.get("/api/v1/memory")
        assert response.status_code == 401

    def test_request_with_invalid_bearer_token_returns_401(self, test_client):
        headers = {"Authorization": "Bearer invalidtoken123"}
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=headers,
        )
        assert response.status_code == 401

    def test_request_with_expired_token_returns_401(self, test_client):
        from datetime import timedelta

        sm = get_security_manager()
        token = sm.create_access_token("user", UserRole.USER, expires_delta=timedelta(seconds=-1))
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=headers,
        )
        assert response.status_code == 401

    def test_request_with_bad_scheme_returns_401(self, test_client):
        headers = {"Authorization": "Basic sometoken"}
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=headers,
        )
        assert response.status_code == 401

    def test_request_without_any_credential_returns_401(self, test_client):
        response = test_client.get("/api/v1/system/info")
        assert response.status_code == 401

    def test_request_with_valid_auth_succeeds(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_request_with_api_key_succeeds(self, test_client):
        sm = get_security_manager()
        api_key = sm.create_api_key("test-client", UserRole.USER)
        headers = {"X-API-Key": api_key}
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_request_with_invalid_api_key_returns_401(self, test_client):
        headers = {"X-API-Key": "ares_invalid.1234567890abcdef1234567890abcdef"}
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=headers,
        )
        assert response.status_code == 401

    def test_admin_endpoint_with_user_role_returns_403(self, test_client, auth_headers):
        response = test_client.get("/api/v1/config", headers=auth_headers)
        assert response.status_code == 403

    def test_admin_endpoint_with_admin_role_succeeds(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._config.loader.load_all_configs") as mock_load:
            mock_load.return_value = {"app": {"key": "value"}}
            response = test_client.get("/api/v1/config", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_public_endpoint_health_no_auth_needed(self, test_client):
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_public_endpoint_version_no_auth_needed(self, test_client):
        response = test_client.get("/api/v1/version")
        assert response.status_code == 200
