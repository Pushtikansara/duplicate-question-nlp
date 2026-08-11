from __future__ import annotations

from unittest.mock import patch

import pytest

from ares._result import PredictionResult
from ares.orchestration.exceptions import InputValidationError, ModelUnavailableError


def _result(
    prediction: str = "duplicate",
    label: int = 1,
    confidence: float = 0.95,
    model: str = "test-model",
) -> PredictionResult:
    return PredictionResult(
        predicted_label=label,
        prediction=prediction,
        confidence=confidence,
        prob_duplicate=confidence,
        prob_non_duplicate=1 - confidence,
        model_name=model,
        latency_ms=10.5,
        trust_score=0.9,
        trust_level="high",
        risk_level="low",
    )


class FakePredictionService:
    """Spy replacing the canonical prediction service in REST tests."""

    def __init__(self, result: PredictionResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, str, dict[str, object]]] = []
        self.batch_calls: list[dict[str, object]] = []

    def predict(self, question1: str, question2: str, **kwargs: object) -> PredictionResult:
        self.calls.append((question1, question2, kwargs))
        if self.error is not None:
            raise self.error
        return self.result

    def predict_batch(self, pairs: list[tuple[str, str]], **kwargs: object) -> list[object]:
        self.batch_calls.append({"pairs": pairs, **kwargs})
        return [self.result, self.error] if self.error else [self.result for _ in pairs]


@pytest.fixture
def predict_service():
    service = FakePredictionService(result=_result())
    with patch("ares.api.routers.predict.get_prediction_service", return_value=service):
        yield service


@pytest.mark.api
class TestPredictUsesOrchestrator:
    def test_predict_calls_prediction_service(self, test_client, auth_headers, predict_service):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "What is Python?", "question2": "What is Java?"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(predict_service.calls) == 1
        q1, q2, kwargs = predict_service.calls[0]
        assert q1 == "What is Python?"
        assert q2 == "What is Java?"

    def test_predict_default_params_are_none(self, test_client, auth_headers, predict_service):
        test_client.post(
            "/api/v1/predict",
            json={"question1": "q1?", "question2": "q2?"},
            headers=auth_headers,
        )
        _, _, kwargs = predict_service.calls[0]
        # The router resolves the configured default model and threshold
        # ('' and 0.5 in the test environment) exactly like the
        # pre-orchestration path did; an empty model is treated as
        # "use strategy default" by the orchestrator.
        assert kwargs["model"] in ("", None)
        assert kwargs["threshold"] == 0.5
        assert kwargs["reflect"] is None

    def test_predict_forwards_model_override(self, test_client, auth_headers, predict_service):
        test_client.post(
            "/api/v1/predict",
            json={"question1": "q1?", "question2": "q2?", "model": "Semantic Ensemble"},
            headers=auth_headers,
        )
        assert predict_service.calls[0][2]["model"] == "Semantic Ensemble"

    def test_predict_forwards_threshold_override(self, test_client, auth_headers, predict_service):
        test_client.post(
            "/api/v1/predict",
            json={"question1": "q1?", "question2": "q2?", "threshold": 0.7},
            headers=auth_headers,
        )
        assert predict_service.calls[0][2]["threshold"] == 0.7

    def test_predict_forwards_reflection(self, test_client, auth_headers, predict_service):
        test_client.post(
            "/api/v1/predict",
            json={"question1": "q1?", "question2": "q2?", "reflect": False},
            headers=auth_headers,
        )
        assert predict_service.calls[0][2]["reflect"] is False

    def test_predict_forwards_request_id_for_tracing(self, test_client, auth_headers, predict_service):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "q1?", "question2": "q2?"},
            headers=auth_headers,
        )
        request_id = response.json()["request_id"]
        assert predict_service.calls[0][2]["request_id"] == request_id


@pytest.mark.api
class TestPredictResponseCompatibility:
    def test_predict_response_schema_unchanged(self, test_client, auth_headers, predict_service):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "What is Python?", "question2": "What is Java?"},
            headers=auth_headers,
        )
        data = response.json()
        for field in (
            "question1",
            "question2",
            "predicted_label",
            "prediction",
            "prob_duplicate",
            "prob_non_duplicate",
            "confidence",
            "threshold",
            "model_label",
            "latency_ms",
            "trust_score",
            "trust_level",
            "risk_level",
            "request_id",
        ):
            assert field in data

    def test_predict_duplicate_response(self, test_client, auth_headers, predict_service):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "q1?", "question2": "q2?"},
            headers=auth_headers,
        )
        assert response.json()["prediction"] == "duplicate"
        assert response.json()["predicted_label"] == 1

    def test_predict_non_duplicate_response(self, test_client, auth_headers):
        with patch(
            "ares.api.routers.predict.get_prediction_service",
            return_value=FakePredictionService(result=_result(prediction="non-duplicate", label=0, confidence=0.2)),
        ):
            response = test_client.post(
                "/api/v1/predict",
                json={"question1": "q1?", "question2": "q2?"},
                headers=auth_headers,
            )
        assert response.json()["prediction"] == "non-duplicate"
        assert response.json()["predicted_label"] == 0


@pytest.mark.api
class TestPredictErrorMapping:
    def test_predict_invalid_input_unchanged(self, test_client, auth_headers, predict_service):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "", "question2": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_predict_validation_error_maps_to_400(self, test_client, auth_headers):
        service = FakePredictionService(result=_result(), error=InputValidationError("too long"))
        with patch("ares.api.routers.predict.get_prediction_service", return_value=service):
            response = test_client.post(
                "/api/v1/predict",
                json={"question1": "q1?", "question2": "q2?"},
                headers=auth_headers,
            )
        assert response.status_code == 400
        assert response.json()["detail"] == "too long"
        assert response.json()["error_code"] == "INPUT_VALIDATION_ERROR"

    def test_predict_model_unavailable_maps_to_503(self, test_client, auth_headers):
        service = FakePredictionService(result=_result(), error=ModelUnavailableError("model gone"))
        with patch("ares.api.routers.predict.get_prediction_service", return_value=service):
            response = test_client.post(
                "/api/v1/predict",
                json={"question1": "q1?", "question2": "q2?"},
                headers=auth_headers,
            )
        assert response.status_code == 503
        assert "error_code" in response.json()

    def test_predict_unexpected_error_maps_to_generic_500(self, test_client, auth_headers):
        service = FakePredictionService(result=_result(), error=RuntimeError("internal detail"))
        with patch("ares.api.routers.predict.get_prediction_service", return_value=service):
            response = test_client.post(
                "/api/v1/predict",
                json={"question1": "q1?", "question2": "q2?"},
                headers=auth_headers,
            )
        assert response.status_code == 500
        assert "internal detail" not in response.json()["detail"]


@pytest.mark.api
class TestPredictBatchUsesOrchestrator:
    def test_batch_calls_predict_batch(self, test_client, auth_headers, predict_service):
        response = test_client.post(
            "/api/v1/predict/batch",
            json={"pairs": [["q1?", "q2?"], ["q3?", "q4?"]]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(predict_service.batch_calls) == 1
        assert predict_service.batch_calls[0]["pairs"] == [("q1?", "q2?"), ("q3?", "q4?")]
        assert response.json()["success_count"] == 2

    def test_batch_counts_isolated_failures(self, test_client, auth_headers):
        service = FakePredictionService(result=_result(), error=ModelUnavailableError("down"))
        with patch("ares.api.routers.predict.get_prediction_service", return_value=service):
            response = test_client.post(
                "/api/v1/predict/batch",
                json={"pairs": [["q1?", "q2?"], ["q3?", "q4?"]]},
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["failure_count"] == 1

    def test_batch_forwards_overrides(self, test_client, auth_headers, predict_service):
        test_client.post(
            "/api/v1/predict/batch",
            json={"pairs": [["q1?", "q2?"]], "model": "Semantic Ensemble", "threshold": 0.8, "reflect": True},
            headers=auth_headers,
        )
        assert predict_service.batch_calls[0]["model"] == "Semantic Ensemble"
        assert predict_service.batch_calls[0]["threshold"] == 0.8
        assert predict_service.batch_calls[0]["reflect"] is True
