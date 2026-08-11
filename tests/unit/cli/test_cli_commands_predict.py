from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ares._result import PredictionResult
from ares.cli.app import app

runner = CliRunner()


def _result(prediction: str = "duplicate", label: int = 1, confidence: float = 0.95) -> PredictionResult:
    return PredictionResult(
        predicted_label=label,
        prediction=prediction,
        confidence=confidence,
        prob_duplicate=confidence,
        prob_non_duplicate=1 - confidence,
        model_name="test",
        latency_ms=100,
        trust_score=None,
    )


class FakePredictionService:
    """Records orchestrator call parameters for CLI predict."""

    def __init__(self, result: PredictionResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def predict(self, question1: str, question2: str, **kwargs: object) -> PredictionResult:
        self.calls.append((question1, question2, kwargs))
        if self.error is not None:
            raise self.error
        return self.result


def _patch_service(**kwargs):
    return patch("ares.cli.commands.predict.get_prediction_service", **kwargs)


class TestPredict:
    def test_predict(self):
        service = FakePredictionService(result=_result())
        with _patch_service(return_value=service):
            result = runner.invoke(app, ["predict", "q1", "q2"])
        assert result.exit_code == 0
        assert "duplicate" in result.output
        assert service.calls == [("q1", "q2", {"model": None, "threshold": None, "reflect": None})]

    def test_predict_json(self):
        service = FakePredictionService(result=_result())
        with _patch_service(return_value=service):
            result = runner.invoke(app, ["predict", "q1", "q2", "--json"])
        assert result.exit_code == 0
        assert "duplicate" in result.output

    def test_predict_with_reflection(self):
        result = _result(prediction="non-duplicate", label=0, confidence=0.8)
        result.trust_score = 0.9
        result.trust_level = "HIGH"
        result.risk_level = "LOW"
        service = FakePredictionService(result=result)
        with _patch_service(return_value=service):
            cli_result = runner.invoke(app, ["predict", "q1", "q2", "--reflect"])
        assert cli_result.exit_code == 0
        assert "non-duplicate" in cli_result.output
        assert "Trust:" in cli_result.output
        assert "Risk:" in cli_result.output
        assert service.calls[0][2]["reflect"] is True

    def test_predict_with_model(self):
        service = FakePredictionService(result=_result())
        with _patch_service(return_value=service):
            result = runner.invoke(app, ["predict", "q1", "q2", "--model", "custom_model"])
        assert result.exit_code == 0
        assert "duplicate" in result.output
        assert service.calls[0][2]["model"] == "custom_model"

    def test_predict_with_threshold(self):
        service = FakePredictionService(result=_result())
        with _patch_service(return_value=service):
            result = runner.invoke(app, ["predict", "q1", "q2", "--threshold", "0.7"])
        assert result.exit_code == 0
        assert service.calls[0][2]["threshold"] == 0.7

    def test_predict_failure(self):
        service = FakePredictionService(result=_result(), error=Exception("prediction failed"))
        with _patch_service(return_value=service):
            result = runner.invoke(app, ["predict", "q1", "q2"])
        assert result.exit_code != 0
