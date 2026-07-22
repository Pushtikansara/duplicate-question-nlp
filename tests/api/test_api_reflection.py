from __future__ import annotations

import pytest

REFLECTION_PAYLOAD = {
    "question1": "What is Python?",
    "question2": "What is Java?",
}


@pytest.mark.api
class TestReflectionEndpoint:
    def test_reflection_returns_200(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        assert response.status_code == 200

    def test_reflection_returns_trust_score(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "trust_score" in data

    def test_reflection_returns_trust_level(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "trust_level" in data

    def test_reflection_returns_risk_level(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "risk_level" in data

    def test_reflection_returns_confidence(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "confidence" in data

    def test_reflection_returns_explanation(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "explanation" in data

    def test_reflection_returns_latency_ms(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "latency_ms" in data

    def test_reflection_returns_request_id(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "request_id" in data

    def test_reflection_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD)
        assert response.status_code == 401

    def test_reflection_empty_questions_returns_422(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json={"question1": "", "question2": ""}, headers=auth_headers)
        assert response.status_code == 422

    def test_reflection_returns_recommendations(self, test_client, auth_headers):
        response = test_client.post("/api/v1/reflection", json=REFLECTION_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "recommendations" in data
