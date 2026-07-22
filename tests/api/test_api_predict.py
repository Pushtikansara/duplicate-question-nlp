from __future__ import annotations

import pytest

PREDICT_PAYLOAD = {"question1": "What is Python?", "question2": "What is Java?"}
BATCH_PAYLOAD = {
    "pairs": [
        ["What is Python?", "What is Java?"],
        ["How to code?", "How to program?"],
    ]
}


@pytest.mark.api
class TestPredictEndpoint:
    def test_predict_valid_data_returns_200(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        assert response.status_code == 200

    def test_predict_response_has_predicted_label(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "predicted_label" in data

    def test_predict_response_has_prediction(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert data["prediction"] == "duplicate"

    def test_predict_response_has_confidence(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert data["confidence"] == 0.95

    def test_predict_response_has_prob_duplicate(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "prob_duplicate" in data

    def test_predict_response_has_prob_non_duplicate(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "prob_non_duplicate" in data

    def test_predict_response_has_latency_ms(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "latency_ms" in data

    def test_predict_with_empty_questions_returns_422(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json={"question1": "", "question2": ""}, headers=auth_headers)
        assert response.status_code == 422

    def test_predict_with_missing_fields_returns_422(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json={}, headers=auth_headers)
        assert response.status_code == 422

    def test_predict_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD)
        assert response.status_code == 401

    def test_predict_with_same_questions_returns_422(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "same", "question2": "same"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "error_code" in data

    def test_predict_returns_request_id(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "request_id" in data

    def test_predict_returns_question_fields(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert data["question1"] == "What is Python?"
        assert data["question2"] == "What is Java?"

    def test_predict_returns_model_label(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "model_label" in data

    def test_predict_returns_threshold(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "threshold" in data


@pytest.mark.api
class TestPredictBatchEndpoint:
    def test_predict_batch_valid_returns_200(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict/batch", json=BATCH_PAYLOAD, headers=auth_headers)
        assert response.status_code == 200

    def test_predict_batch_returns_results_list(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict/batch", json=BATCH_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_predict_batch_returns_success_count(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict/batch", json=BATCH_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert data["success_count"] > 0

    def test_predict_batch_returns_total_latency(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict/batch", json=BATCH_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "total_latency_ms" in data

    def test_predict_batch_returns_average_latency(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict/batch", json=BATCH_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "average_latency_ms" in data

    def test_predict_batch_returns_failure_count(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict/batch", json=BATCH_PAYLOAD, headers=auth_headers)
        data = response.json()
        assert "failure_count" in data

    def test_predict_batch_empty_pairs_returns_422(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict/batch", json={"pairs": []}, headers=auth_headers)
        assert response.status_code == 422

    def test_predict_batch_multiple_results(self, test_client, auth_headers):
        payload = {"pairs": [["q1?", "q2?"], ["q3?", "q4?"], ["q5?", "q6?"]]}
        response = test_client.post("/api/v1/predict/batch", json=payload, headers=auth_headers)
        data = response.json()
        assert len(data["results"]) == 3

    def test_predict_batch_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/predict/batch", json=BATCH_PAYLOAD)
        assert response.status_code == 401


@pytest.mark.api
class TestPredictStreamEndpoint:
    def test_predict_stream_requires_auth(self, test_client):
        response = test_client.post("/api/v1/predict/stream", json=BATCH_PAYLOAD)
        assert response.status_code == 401

    def test_predict_stream_with_auth_returns_stream(self, test_client, auth_headers):
        response = test_client.post("/api/v1/predict/stream", json=BATCH_PAYLOAD, headers=auth_headers)
        assert response.status_code == 200
        ct = response.headers.get("content-type", "")
        assert "text/event-stream" in ct
