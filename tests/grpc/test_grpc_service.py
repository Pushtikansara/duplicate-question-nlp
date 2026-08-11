from __future__ import annotations

from unittest.mock import patch

import pytest

from ares._result import PredictionResult
from ares.orchestration.exceptions import ModelUnavailableError, OrchestrationError


class SpyPredictionService:
    """Records orchestrator call parameters; returns a canned result."""

    def __init__(self, result: PredictionResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def predict(self, question1: str, question2: str, **kwargs: object) -> PredictionResult:
        self.calls.append((question1, question2, kwargs))
        if self.error is not None:
            raise self.error
        return self.result


def _result() -> PredictionResult:
    return PredictionResult(
        predicted_label=1,
        prediction="duplicate",
        confidence=0.95,
        prob_duplicate=0.95,
        prob_non_duplicate=0.05,
        model_name="test-model",
        latency_ms=10.5,
        trust_score=0.9,
        trust_level="high",
        risk_level="low",
    )


@pytest.mark.grpc
class TestAresGrpcServicePredict:
    def test_predict_returns_expected_fields(self, grpc_service):
        result = grpc_service.predict("What is Python?", "What is Java?")
        assert isinstance(result, dict)
        assert "question1" in result
        assert "question2" in result
        assert "predicted_label" in result
        assert "prediction" in result
        assert "prob_duplicate" in result
        assert "prob_non_duplicate" in result
        assert "confidence" in result
        assert "threshold" in result
        assert "model_label" in result
        assert "latency_ms" in result
        assert "timestamp" in result

    def test_predict_returns_correct_questions(self, grpc_service):
        result = grpc_service.predict("What is Python?", "What is Java?")
        assert result["question1"] == "What is Python?"
        assert result["question2"] == "What is Java?"

    def test_predict_returns_predicted_label(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert result["predicted_label"] == 1

    def test_predict_returns_prediction_string(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert result["prediction"] == "duplicate"

    def test_predict_returns_confidence(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert result["confidence"] == 0.95

    def test_predict_returns_threshold(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert result["threshold"] == 0.5

    def test_predict_returns_latency_ms(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert isinstance(result["latency_ms"], float)

    def test_predict_delegates_to_prediction_service(self, grpc_service):
        spy = SpyPredictionService(result=_result())
        with patch("ares.grpc.services.get_prediction_service", return_value=spy):
            grpc_service.predict("q1", "q2")
        assert len(spy.calls) == 1
        assert spy.calls[0][0] == "q1"
        assert spy.calls[0][1] == "q2"

    def test_predict_passes_model_parameter(self, grpc_service):
        spy = SpyPredictionService(result=_result())
        with patch("ares.grpc.services.get_prediction_service", return_value=spy):
            grpc_service.predict("q1", "q2", model="custom-model")
        assert spy.calls[0][2]["model"] == "custom-model"

    def test_predict_passes_threshold_parameter(self, grpc_service):
        spy = SpyPredictionService(result=_result())
        with patch("ares.grpc.services.get_prediction_service", return_value=spy):
            grpc_service.predict("q1", "q2", threshold=0.7)
        assert spy.calls[0][2]["threshold"] == 0.7

    def test_predict_passes_reflect_parameter(self, grpc_service):
        spy = SpyPredictionService(result=_result())
        with patch("ares.grpc.services.get_prediction_service", return_value=spy):
            grpc_service.predict("q1", "q2", reflect=False)
        assert spy.calls[0][2]["reflect"] is False

    def test_predict_passes_reflect_true(self, grpc_service):
        spy = SpyPredictionService(result=_result())
        with patch("ares.grpc.services.get_prediction_service", return_value=spy):
            grpc_service.predict("q1", "q2", reflect=True)
        assert spy.calls[0][2]["reflect"] is True

    def test_predict_without_params_passes_reflect_none(self, grpc_service):
        """Reflect is only applied when explicitly supplied: the orchestrator
        (not the gRPC layer) decides the default, so no unconditional
        reflection override is reintroduced here."""
        spy = SpyPredictionService(result=_result())
        with patch("ares.grpc.services.get_prediction_service", return_value=spy):
            grpc_service.predict("q1", "q2")
        assert spy.calls[0][2]["reflect"] is None
        assert spy.calls[0][2]["model"] is None
        assert spy.calls[0][2]["threshold"] is None

    def test_predict_propagates_orchestration_errors(self, grpc_service):
        spy = SpyPredictionService(result=_result(), error=ModelUnavailableError("model gone"))
        with patch("ares.grpc.services.get_prediction_service", return_value=spy):
            with pytest.raises(OrchestrationError):
                grpc_service.predict("q1", "q2")

    def test_predict_response_does_not_include_explanations(self, grpc_service):
        result = grpc_service.predict("q1", "q2")
        assert "explanations" not in result


@pytest.mark.grpc
class TestAresGrpcServiceBatch:
    def test_predict_batch_returns_results_list(self, grpc_service):
        requests = [{"question1": "q1", "question2": "q2"}, {"question1": "q3", "question2": "q4"}]
        result = grpc_service.predict_batch(requests)
        assert "results" in result
        assert isinstance(result["results"], list)
        assert len(result["results"]) == 2

    def test_predict_batch_returns_success_count(self, grpc_service):
        requests = [{"question1": "q1", "question2": "q2"}]
        result = grpc_service.predict_batch(requests)
        assert result["success_count"] == 1

    def test_predict_batch_returns_total_latency(self, grpc_service):
        requests = [{"question1": "q1", "question2": "q2"}]
        result = grpc_service.predict_batch(requests)
        assert "total_latency_ms" in result

    def test_predict_batch_delegates_to_prediction_service(self, grpc_service):
        spy = SpyPredictionService(result=_result())
        with patch("ares.grpc.services.get_prediction_service", return_value=spy):
            grpc_service.predict_batch([{"question1": "q1", "question2": "q2", "model": "m1"}])
        assert len(spy.calls) == 1
        assert spy.calls[0][2]["model"] == "m1"


@pytest.mark.grpc
class TestAresGrpcServiceHealth:
    def test_health_returns_status(self, grpc_service):
        result = grpc_service.health()
        assert "status" in result

    def test_health_returns_version(self, grpc_service):
        result = grpc_service.health()
        assert "version" in result

    def test_health_returns_uptime_seconds(self, grpc_service):
        result = grpc_service.health()
        assert "uptime_seconds" in result
        assert isinstance(result["uptime_seconds"], float)

    def test_health_returns_components(self, grpc_service):
        result = grpc_service.health()
        assert "components" in result
        assert isinstance(result["components"], dict)

    def test_health_components_contain_app(self, grpc_service):
        result = grpc_service.health()
        assert "app" in result["components"]

    def test_health_components_contain_torch(self, grpc_service):
        result = grpc_service.health()
        assert "torch" in result["components"]

    def test_health_components_contain_cuda(self, grpc_service):
        result = grpc_service.health()
        assert "cuda" in result["components"]

    def test_health_status_is_healthy_or_degraded(self, grpc_service):
        result = grpc_service.health()
        assert result["status"] in ("healthy", "degraded")


@pytest.mark.grpc
class TestAresGrpcServiceVersion:
    def test_version_returns_version_string(self, grpc_service):
        result = grpc_service.version()
        assert "version" in result
        assert isinstance(result["version"], str)

    def test_version_returns_api_version(self, grpc_service):
        result = grpc_service.version()
        assert "api_version" in result
        assert result["api_version"] == "1.0.0"

    def test_version_returns_python_version(self, grpc_service):
        result = grpc_service.version()
        assert "python_version" in result
        assert isinstance(result["python_version"], str)

    def test_version_returns_platform(self, grpc_service):
        result = grpc_service.version()
        assert "platform" in result
        assert isinstance(result["platform"], str)


@pytest.mark.grpc
class TestAresGrpcServicePipeline:
    def test_run_pipeline_returns_success(self, grpc_service):
        result = grpc_service.run_pipeline("q1", "q2")
        assert "success" in result
        assert result["success"] is True

    def test_run_pipeline_returns_modules_executed(self, grpc_service):
        result = grpc_service.run_pipeline("q1", "q2")
        assert "modules_executed" in result
        assert isinstance(result["modules_executed"], list)

    def test_run_pipeline_returns_total_latency(self, grpc_service):
        result = grpc_service.run_pipeline("q1", "q2")
        assert "total_latency_ms" in result
        assert isinstance(result["total_latency_ms"], float)


@pytest.mark.grpc
class TestAresGrpcServiceReflection:
    def test_run_reflection_returns_trust_score(self, grpc_service):
        result = grpc_service.run_reflection("q1", "q2")
        assert "trust_score" in result
        assert result["trust_score"] == 0.9

    def test_run_reflection_returns_trust_level(self, grpc_service):
        result = grpc_service.run_reflection("q1", "q2")
        assert "trust_level" in result

    def test_run_reflection_returns_risk_level(self, grpc_service):
        result = grpc_service.run_reflection("q1", "q2")
        assert "risk_level" in result
        assert result["risk_level"] == "low"
