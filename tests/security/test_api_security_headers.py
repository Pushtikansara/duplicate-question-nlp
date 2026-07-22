from __future__ import annotations

import pytest


@pytest.mark.security
class TestSecurityHeaders:
    def test_response_has_x_content_type_options(self, test_client):
        response = test_client.get("/api/v1/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_response_has_x_frame_options(self, test_client):
        response = test_client.get("/api/v1/health")
        assert response.headers.get("x-frame-options") == "DENY"

    def test_response_has_x_xss_protection(self, test_client):
        response = test_client.get("/api/v1/health")
        value = response.headers.get("x-xss-protection")
        assert value == "1; mode=block"

    def test_response_has_strict_transport_security(self, test_client):
        response = test_client.get("/api/v1/health")
        hsts = response.headers.get("strict-transport-security")
        assert hsts is not None
        assert "max-age=31536000" in hsts

    def test_response_has_cache_control(self, test_client):
        response = test_client.get("/api/v1/health")
        cc = response.headers.get("cache-control")
        assert cc == "no-store"

    def test_response_has_request_id_header(self, test_client):
        response = test_client.get("/api/v1/health")
        assert "x-request-id" in response.headers

    def test_response_has_processing_time(self, test_client):
        response = test_client.get("/api/v1/health")
        assert "x-processing-time-ms" in response.headers

    def test_all_endpoints_return_security_headers(self, test_client):
        response = test_client.get("/api/v1/version")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    def test_security_headers_on_auth_endpoint(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=auth_headers,
        )
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"

    def test_security_headers_on_error_response(self, test_client):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "", "question2": ""},
            headers={"Authorization": "Bearer invalid"},
        )
        assert "x-content-type-options" in response.headers

    def test_request_id_echoed_in_response(self, test_client):
        custom_id = "my-custom-request-id-12345"
        response = test_client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
        assert response.headers.get("x-request-id") == custom_id

    def test_processing_time_is_numeric(self, test_client):
        response = test_client.get("/api/v1/health")
        pt = response.headers.get("x-processing-time-ms", "0")
        assert float(pt) >= 0
