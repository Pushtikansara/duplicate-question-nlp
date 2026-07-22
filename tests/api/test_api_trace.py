from __future__ import annotations

import pytest

TRACE_PAYLOAD = {
    "question1": "What is Python?",
    "question2": "What is Java?",
}


@pytest.mark.api
class TestTraceEndpoint:
    def test_trace_returns_200(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        assert response.status_code == 200

    def test_trace_returns_trace_data(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "trace" in data

    def test_trace_returns_steps(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "steps" in data
        assert isinstance(data["steps"], list)

    def test_trace_steps_contain_preprocessing(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        data = response.json()
        step_names = [s["step"] for s in data["steps"]]
        assert "preprocessing" in step_names

    def test_trace_steps_contain_inference(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        data = response.json()
        step_names = [s["step"] for s in data["steps"]]
        assert "inference" in step_names

    def test_trace_steps_contain_postprocessing(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        data = response.json()
        step_names = [s["step"] for s in data["steps"]]
        assert "postprocessing" in step_names

    def test_trace_returns_total_latency(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "total_latency_ms" in data

    def test_trace_returns_request_id(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "request_id" in data

    def test_trace_empty_questions_returns_422(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json={"question1": "", "question2": ""}, headers=auth_headers)
        assert response.status_code == 422

    def test_trace_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD)
        assert response.status_code == 401

    def test_trace_trace_data_is_dict(self, test_client, auth_headers):
        response = test_client.post("/api/v1/trace", json=TRACE_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert isinstance(data["trace"], dict)
