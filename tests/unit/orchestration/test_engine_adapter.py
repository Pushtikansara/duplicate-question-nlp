from __future__ import annotations

from typing import Any

import pytest

from ares.orchestration.engine_adapter import ARESPredictionEngine
from ares.orchestration.exceptions import (
    ModelTimeoutError,
    ModelUnavailableError,
    TaskExecutionError,
)


class _FakeARES:
    def __init__(self) -> None:
        self.error: Exception | None = None
        self.sleep = 0.0
        self.result: Any = "ok"
        self.built_config: dict[str, Any] = {}

    def with_model(self, name: str) -> _FakeARES:
        self.built_config["model"] = name
        return self

    def with_threshold(self, threshold: float) -> _FakeARES:
        self.built_config["threshold"] = threshold
        return self

    def with_reflection(self, enabled: bool = True) -> _FakeARES:
        self.built_config["reflect"] = enabled
        return self

    def with_semantic_validation(self, enabled: bool = True) -> _FakeARES:
        self.built_config["semantic_validation"] = enabled
        return self

    def predict(self, question1: str, question2: str) -> Any:
        import time

        if self.sleep:
            time.sleep(self.sleep)
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def fake_ares(monkeypatch: pytest.MonkeyPatch) -> _FakeARES:
    fake = _FakeARES()
    monkeypatch.setattr("ares.orchestration.engine_adapter.ARES", lambda: fake)
    return fake


class TestARESPredictionEngine:
    def test_predicts_with_configuration(self, fake_ares: _FakeARES) -> None:
        engine = ARESPredictionEngine(default_timeout_ms=5000)
        result = engine.predict("q1", "q2", model="Test Model", threshold=0.7, reflect=False)
        assert result == "ok"
        assert fake_ares.built_config == {
            "model": "Test Model",
            "threshold": 0.7,
            "reflect": False,
            "semantic_validation": True,
        }

    def test_default_threshold(self, fake_ares: _FakeARES) -> None:
        engine = ARESPredictionEngine(default_timeout_ms=5000)
        engine.predict("q1", "q2", model="Test Model")
        assert fake_ares.built_config["threshold"] == 0.5

    def test_timeout_raises_model_timeout_error(self, fake_ares: _FakeARES) -> None:
        fake_ares.sleep = 2.0
        engine = ARESPredictionEngine(default_timeout_ms=100)
        with pytest.raises(ModelTimeoutError):
            engine.predict("q1", "q2", model="Test Model")

    def test_no_models_runtime_error_mapped(self, fake_ares: _FakeARES) -> None:
        fake_ares.error = RuntimeError("No models available")
        engine = ARESPredictionEngine(default_timeout_ms=5000)
        with pytest.raises(ModelUnavailableError):
            engine.predict("q1", "q2", model="Test Model")

    def test_unknown_model_error_mapped(self, fake_ares: _FakeARES) -> None:
        fake_ares.error = ValueError("'Nope' is not in the model registry")
        engine = ARESPredictionEngine(default_timeout_ms=5000)
        with pytest.raises(ModelUnavailableError):
            engine.predict("q1", "q2", model="Test Model")

    def test_other_failures_wrapped_as_task_execution_error(self, fake_ares: _FakeARES) -> None:
        fake_ares.error = RuntimeError("weights missing")
        engine = ARESPredictionEngine(default_timeout_ms=5000)
        with pytest.raises(TaskExecutionError):
            engine.predict("q1", "q2", model="Test Model")

    def test_request_timeout_override(self, fake_ares: _FakeARES) -> None:
        fake_ares.sleep = 2.0
        engine = ARESPredictionEngine(default_timeout_ms=5000)
        with pytest.raises(ModelTimeoutError):
            engine.predict("q1", "q2", model="Test Model", timeout_ms=100)
