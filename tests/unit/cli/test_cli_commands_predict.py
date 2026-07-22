from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ares.cli.app import app

runner = CliRunner()


class TestPredict:
    def test_predict(self):
        mock_result = MagicMock()
        mock_result.prediction = "duplicate"
        mock_result.confidence = 0.95
        mock_result.predicted_label = 1
        mock_result.model_name = "test"
        mock_result.latency_ms = 100
        mock_result.trust_score = None
        mock_result.to_dict.return_value = {"prediction": "duplicate", "confidence": 0.95}

        with patch("ares.ARES") as mock_ares:
            instance = MagicMock()
            instance.predict.return_value = mock_result
            mock_ares.return_value = instance
            result = runner.invoke(app, ["predict", "q1", "q2"])
            assert result.exit_code == 0
            assert "duplicate" in result.output

    def test_predict_json(self):
        mock_result = MagicMock()
        mock_result.prediction = "duplicate"
        mock_result.confidence = 0.95
        mock_result.predicted_label = 1
        mock_result.model_name = "test"
        mock_result.latency_ms = 100
        mock_result.trust_score = None
        mock_result.to_dict.return_value = {"prediction": "duplicate"}

        with patch("ares.ARES") as mock_ares:
            instance = MagicMock()
            instance.predict.return_value = mock_result
            mock_ares.return_value = instance
            result = runner.invoke(app, ["predict", "q1", "q2", "--json"])
            assert result.exit_code == 0
            assert "duplicate" in result.output

    def test_predict_with_reflection(self):
        mock_result = MagicMock()
        mock_result.prediction = "non-duplicate"
        mock_result.confidence = 0.8
        mock_result.predicted_label = 0
        mock_result.model_name = "test"
        mock_result.latency_ms = 100
        mock_result.trust_score = 0.9
        mock_result.trust_level = "HIGH"
        mock_result.risk_level = "LOW"
        mock_result.to_dict.return_value = {"prediction": "non-duplicate"}

        with patch("ares.ARES") as mock_ares:
            instance = MagicMock()
            instance.predict.return_value = mock_result
            mock_ares.return_value = instance
            result = runner.invoke(app, ["predict", "q1", "q2", "--reflect"])
            assert result.exit_code == 0
            assert "non-duplicate" in result.output
            assert "Trust:" in result.output
            assert "Risk:" in result.output

    def test_predict_with_model(self):
        mock_result = MagicMock()
        mock_result.prediction = "duplicate"
        mock_result.confidence = 0.9
        mock_result.predicted_label = 1
        mock_result.model_name = "custom"
        mock_result.latency_ms = 50
        mock_result.trust_score = None
        mock_result.to_dict.return_value = {"prediction": "duplicate"}

        with patch("ares.ARES") as mock_ares:
            instance = MagicMock()
            instance.predict.return_value = mock_result
            mock_ares.return_value = instance
            result = runner.invoke(app, ["predict", "q1", "q2", "--model", "custom_model"])
            assert result.exit_code == 0
            assert "duplicate" in result.output

    def test_predict_failure(self):
        with patch("ares.ARES") as mock_ares:
            instance = MagicMock()
            instance.predict.side_effect = Exception("prediction failed")
            mock_ares.return_value = instance
            result = runner.invoke(app, ["predict", "q1", "q2"])
            assert result.exit_code != 0
