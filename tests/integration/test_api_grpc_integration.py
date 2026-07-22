from __future__ import annotations

import pytest


@pytest.mark.integration
class TestApiGrpcHealthConsistency:
    def test_health_endpoint_has_status(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "status" in data

    def test_grpc_health_has_status(self, grpc_service):
        result = grpc_service.health()
        assert "status" in result

    def test_both_return_comparable_version(self, test_client, grpc_service):
        grpc_result = grpc_service.version()
        response = test_client.get("/api/v1/version")
        api_result = response.json()
        assert "version" in grpc_result
        assert "version" in api_result

    def test_both_return_api_version(self, test_client, grpc_service):
        grpc_result = grpc_service.version()
        response = test_client.get("/api/v1/version")
        api_result = response.json()
        assert grpc_result.get("api_version") == api_result.get("api_version", "1.0.0")

    def test_both_return_python_version(self, test_client, grpc_service):
        grpc_result = grpc_service.version()
        response = test_client.get("/api/v1/version")
        api_result = response.json()
        assert isinstance(grpc_result.get("python_version"), str)
        assert isinstance(api_result.get("python_version"), str)

    def test_both_return_platform(self, test_client, grpc_service):
        grpc_result = grpc_service.version()
        response = test_client.get("/api/v1/version")
        api_result = response.json()
        assert isinstance(grpc_result.get("platform"), str)
        assert isinstance(api_result.get("platform"), str)

    def test_health_response_contains_components(self, test_client):
        response = test_client.get("/api/v1/health")
        api_data = response.json()
        assert "components" in api_data

    def test_grpc_health_contains_components(self, grpc_service):
        result = grpc_service.health()
        assert "components" in result


@pytest.mark.integration
class TestApiGrpcPredictConsistency:
    def test_api_predict_returns_predicted_label(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "q1", "question2": "q2"},
            headers=auth_headers,
        )
        data = response.json()
        assert "predicted_label" in data

    def test_grpc_predict_returns_predicted_label(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert "predicted_label" in result

    def test_both_return_question_fields(self, grpc_service):
        result = grpc_service.predict("What is Python?", "What is Java?")
        assert result["question1"] == "What is Python?"
        assert result["question2"] == "What is Java?"

    def test_api_predict_returns_prob_duplicate(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "q1", "question2": "q2"},
            headers=auth_headers,
        )
        data = response.json()
        assert "prob_duplicate" in data

    def test_grpc_predict_returns_prob_duplicate(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert "prob_duplicate" in result

    def test_both_return_confidence(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert "confidence" in result

    def test_api_predict_returns_confidence(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "q1", "question2": "q2"},
            headers=auth_headers,
        )
        data = response.json()
        assert "confidence" in data


@pytest.mark.integration
class TestApiGrpcPipelineConsistency:
    def test_api_pipeline_returns_success(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/pipeline",
            json={"question1": "q1", "question2": "q2"},
            headers=auth_headers,
        )
        data = response.json()
        assert "success" in data

    def test_grpc_pipeline_returns_success(self, grpc_service):
        result = grpc_service.run_pipeline("q1", "q2")
        assert "success" in result
        assert result["success"] is True
