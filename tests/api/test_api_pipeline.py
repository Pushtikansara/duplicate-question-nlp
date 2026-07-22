from __future__ import annotations

import pytest

PIPELINE_PAYLOAD = {
    "question1": "What is Python?",
    "question2": "What is Java?",
    "enable_perception": True,
    "enable_routing": True,
    "enable_memory": True,
    "enable_semantic": True,
    "enable_reasoning": True,
    "enable_debate": True,
    "enable_reflection": True,
}


@pytest.mark.api
class TestPipelineEndpoint:
    def test_pipeline_valid_returns_200(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        assert response.status_code == 200

    def test_pipeline_returns_success_field(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "success" in data

    def test_pipeline_returns_question1(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert data["question1"] == "What is Python?"

    def test_pipeline_returns_question2(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert data["question2"] == "What is Java?"

    def test_pipeline_returns_prediction(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert data["prediction"] is not None

    def test_pipeline_returns_modules_executed(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "modules_executed" in data
        assert isinstance(data["modules_executed"], list)

    def test_pipeline_returns_modules_skipped(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "modules_skipped" in data
        assert isinstance(data["modules_skipped"], list)

    def test_pipeline_returns_total_latency(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "total_latency_ms" in data
        assert isinstance(data["total_latency_ms"], float)

    def test_pipeline_returns_module_latencies(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "module_latencies" in data
        assert isinstance(data["module_latencies"], dict)

    def test_pipeline_returns_confidence(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "confidence" in data

    def test_pipeline_returns_request_id(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "request_id" in data

    def test_pipeline_with_empty_questions_returns_422(self, test_client, auth_headers):
        response = test_client.post("/api/v1/pipeline", json={"question1": "", "question2": ""}, headers=auth_headers)
        assert response.status_code == 422

    def test_pipeline_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/pipeline", json=PIPELINE_PAYLOAD)
        assert response.status_code == 401

    def test_pipeline_disabled_perception_skips_it(self, test_client, auth_headers):
        payload = {**PIPELINE_PAYLOAD, "enable_perception": False}
        response = test_client.post("/api/v1/pipeline", json=payload, headers=auth_headers)
        data = response.json()
        assert "perception" in data["modules_skipped"]
