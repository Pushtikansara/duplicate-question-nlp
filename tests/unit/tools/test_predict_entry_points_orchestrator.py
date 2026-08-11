from __future__ import annotations

import asyncio
from unittest.mock import patch

from ares._result import PredictionResult


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


class SpyPredictionService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def predict(self, question1: str, question2: str, **kwargs: object) -> PredictionResult:
        self.calls.append((question1, question2, kwargs))
        return _result()


class TestPredictToolUsesOrchestrator:
    def test_execute_delegates_to_prediction_service(self) -> None:
        from ares.tools.builtin.predict_tool import PredictTool

        spy = SpyPredictionService()
        tool = PredictTool()
        with patch("ares.tools.builtin.predict_tool.get_prediction_service", return_value=spy):
            result = asyncio.run(tool.execute({"question1": "q1", "question2": "q2"}))
        assert result.status.name == "AVAILABLE"
        assert result.result["prediction"] == "duplicate"
        assert spy.calls[0][2]["model"] is None

    def test_execute_forwards_overrides(self) -> None:
        from ares.tools.builtin.predict_tool import PredictTool

        spy = SpyPredictionService()
        tool = PredictTool()
        with patch("ares.tools.builtin.predict_tool.get_prediction_service", return_value=spy):
            asyncio.run(
                tool.execute(
                    {
                        "question1": "q1",
                        "question2": "q2",
                        "model": "Semantic Ensemble",
                        "threshold": 0.8,
                        "reflect": False,
                    }
                )
            )
        assert spy.calls[0][2]["model"] == "Semantic Ensemble"
        assert spy.calls[0][2]["threshold"] == 0.8
        assert spy.calls[0][2]["reflect"] is False

    def test_execute_requires_questions(self) -> None:
        from ares.tools.builtin.predict_tool import PredictTool

        tool = PredictTool()
        result = asyncio.run(tool.execute({"question1": "", "question2": ""}))
        assert result.status.name == "ERROR"


class TestPredictAgentUsesOrchestrator:
    def test_execute_delegates_to_prediction_service(self) -> None:
        from ares.agents.builtin.predict_agent import PredictAgent

        spy = SpyPredictionService()
        agent = PredictAgent()
        with patch("ares.agents.builtin.predict_agent.get_prediction_service", return_value=spy):
            output = asyncio.run(agent.execute({"question1": "q1", "question2": "q2"}))
        assert output.status.name == "SUCCESS"
        assert output.result["prediction"] == "duplicate"
        assert spy.calls[0][2]["model"] is None

    def test_execute_forwards_context_model(self) -> None:
        from ares.agents.builtin.predict_agent import PredictAgent

        spy = SpyPredictionService()
        agent = PredictAgent()
        with patch("ares.agents.builtin.predict_agent.get_prediction_service", return_value=spy):
            asyncio.run(
                agent.execute(
                    {
                        "question1": "q1",
                        "question2": "q2",
                        "context": {"model": "Semantic Ensemble", "threshold": 0.7},
                        "reflect": True,
                    }
                )
            )
        assert spy.calls[0][2]["model"] == "Semantic Ensemble"
        assert spy.calls[0][2]["threshold"] == 0.7
        assert spy.calls[0][2]["reflect"] is True

    def test_execute_failure_returns_error_status(self) -> None:
        from ares.agents.builtin.predict_agent import PredictAgent

        agent = PredictAgent()
        output = asyncio.run(agent.execute({"question1": "", "question2": ""}))
        assert output.status.name == "FAILURE"
