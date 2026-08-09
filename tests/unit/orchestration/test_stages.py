from __future__ import annotations

from typing import Any

import pytest

from ares._result import PredictionResult
from ares.orchestration.config import EngineConfiguration
from ares.orchestration.context import PipelineState, PredictionInput, RequestParams
from ares.orchestration.exceptions import (
    CacheError,
    InputValidationError,
    QueryUnderstandingError,
    StrategyResolutionError,
    TaskExecutionError,
)
from ares.orchestration.metadata import OrchestrationMetadata
from ares.orchestration.stages import (
    InputValidationStage,
    PredictionStage,
    QueryUnderstandingStage,
    ResultEnrichmentStage,
    StrategySelectionStage,
)
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.router_models import RoutingDecision


def _input(
    question1: str = "What is the capital of France?", question2: str = "Capital city of France?"
) -> PredictionInput:
    return PredictionInput(question1=question1, question2=question2)


def _state() -> PipelineState:
    return PipelineState()


def _metadata() -> OrchestrationMetadata:
    return OrchestrationMetadata()


def _analysis(strategy: str = "fast_lexical") -> QueryAnalysis:
    return QueryAnalysis(
        original_question_1="q1",
        original_question_2="q2",
        routing_decision=RoutingDecision(selected_strategy=strategy),
    )


class TestInputValidationStage:
    def test_valid_input_passes(self) -> None:
        stage = InputValidationStage()
        stage.run(_input(), _state(), _metadata())

    def test_empty_question_rejected(self) -> None:
        stage = InputValidationStage()
        with pytest.raises(InputValidationError):
            stage.run(_input(question1="   "), _state(), _metadata())

    def test_non_string_rejected(self) -> None:
        stage = InputValidationStage()
        with pytest.raises(InputValidationError):
            stage.run(_input(question1=123), _state(), _metadata())  # type: ignore[arg-type]

    def test_overlong_question_rejected(self) -> None:
        stage = InputValidationStage(max_question_length=10)
        with pytest.raises(InputValidationError):
            stage.run(_input(question1="x" * 11), _state(), _metadata())

    def test_control_characters_rejected(self) -> None:
        stage = InputValidationStage()
        with pytest.raises(InputValidationError):
            stage.run(_input(question1="hello\x00world"), _state(), _metadata())

    def test_newline_and_tab_allowed(self) -> None:
        stage = InputValidationStage()
        stage.run(_input(question1="hello\nworld\t!"), _state(), _metadata())

    def test_out_of_range_threshold_rejected(self) -> None:
        stage = InputValidationStage()
        invalid = PredictionInput(
            question1="What is the capital of France?",
            question2="Capital city of France?",
            request_params=RequestParams(threshold=1.5),
        )
        with pytest.raises(InputValidationError):
            stage.run(invalid, _state(), _metadata())

    def test_boundary_thresholds_accepted(self) -> None:
        stage = InputValidationStage()
        for value in (0.0, 1.0):
            valid = PredictionInput(
                question1="What is the capital of France?",
                question2="Capital city of France?",
                request_params=RequestParams(threshold=value),
            )
            stage.run(valid, _state(), _metadata())


class _FakeCache:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}
        self.gets: list[str] = []
        self.sets: list[str] = []

    def get(self, key: str) -> Any | None:
        self.gets.append(key)
        return self.store.get(key)

    def set(self, key: str, value: Any, ttl: int) -> None:
        self.sets.append(key)
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)

    def clear(self) -> None:
        self.store.clear()


class _FakeQueryPipeline:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.error: Exception | None = None

    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        self.calls.append((question_1, question_2))
        if self.error is not None:
            raise self.error
        return _analysis()


class TestQueryUnderstandingStage:
    def test_runs_pipeline_and_stores_analysis(self) -> None:
        pipeline = _FakeQueryPipeline()
        stage = QueryUnderstandingStage(pipeline)
        state = _state()
        stage.run(_input(), state, _metadata())
        assert state.query_analysis is not None
        assert pipeline.calls == [("What is the capital of France?", "Capital city of France?")]

    def test_pipeline_failure_wrapped(self) -> None:
        pipeline = _FakeQueryPipeline()
        pipeline.error = ValueError("boom")
        stage = QueryUnderstandingStage(pipeline)
        with pytest.raises(QueryUnderstandingError):
            stage.run(_input(), _state(), _metadata())

    def test_cache_miss_then_hit(self) -> None:
        pipeline = _FakeQueryPipeline()
        cache = _FakeCache()
        stage = QueryUnderstandingStage(pipeline, cache)
        metadata = _metadata()
        state = _state()
        stage.run(_input(), state, metadata)
        assert metadata.cache_hit is False
        assert len(cache.sets) == 1
        second_state = _state()
        stage.run(_input(), second_state, metadata)
        assert metadata.cache_hit is True
        assert len(pipeline.calls) == 1

    def test_skip_cache_never_touches_cache(self) -> None:
        pipeline = _FakeQueryPipeline()
        cache = _FakeCache()
        stage = QueryUnderstandingStage(pipeline, cache)
        input = PredictionInput(
            question1="What is the capital of France?",
            question2="Capital city of France?",
            request_params=RequestParams(skip_cache=True),
        )
        stage.run(input, _state(), _metadata())
        assert cache.gets == [] and cache.sets == []

    def test_fail_closed_raises_cache_error_on_read_failure(self) -> None:
        class BrokenCache(_FakeCache):
            def get(self, key: str) -> Any | None:
                raise RuntimeError("cache down")

        pipeline = _FakeQueryPipeline()
        stage = QueryUnderstandingStage(pipeline, BrokenCache(), fail_closed=True)
        with pytest.raises(CacheError):
            stage.run(_input(), _state(), _metadata())

    def test_cache_failure_ignored_without_fail_closed(self) -> None:
        class BrokenCache(_FakeCache):
            def get(self, key: str) -> Any | None:
                raise RuntimeError("cache down")

        pipeline = _FakeQueryPipeline()
        stage = QueryUnderstandingStage(pipeline, BrokenCache())
        state = _state()
        stage.run(_input(), state, _metadata())
        assert state.query_analysis is not None

    def test_skips_cache_when_no_provider(self) -> None:
        pipeline = _FakeQueryPipeline()
        stage = QueryUnderstandingStage(pipeline)
        stage.run(_input(), _state(), _metadata())
        assert len(pipeline.calls) == 1


class _FakeSelector:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[Any] = []

    def resolve(self, routing_decision: Any, request_params: Any = None) -> EngineConfiguration:
        self.calls.append((routing_decision, request_params))
        if self.error is not None:
            raise self.error
        return EngineConfiguration(
            model_name="Test Model",
            threshold=0.5,
            use_reflection=True,
        )


class TestStrategySelectionStage:
    def test_resolves_and_stores_config(self) -> None:
        selector = _FakeSelector()
        stage = StrategySelectionStage(selector)  # type: ignore[arg-type]
        state = _state()
        state.query_analysis = _analysis("baseline_classifier")
        stage.run(_input(), state, _metadata())
        assert state.engine_config is not None
        assert state.engine_config.model_name == "Test Model"

    def test_missing_analysis_raises(self) -> None:
        stage = StrategySelectionStage(_FakeSelector())  # type: ignore[arg-type]
        with pytest.raises(StrategyResolutionError):
            stage.run(_input(), _state(), _metadata())

    def test_resolution_error_propagates(self) -> None:
        selector = _FakeSelector(error=StrategyResolutionError("unknown strategy"))
        stage = StrategySelectionStage(selector)  # type: ignore[arg-type]
        state = _state()
        state.query_analysis = _analysis("nope")
        with pytest.raises(StrategyResolutionError):
            stage.run(_input(), state, _metadata())

    def test_unexpected_error_wrapped(self) -> None:
        selector = _FakeSelector(error=RuntimeError("registry exploded"))
        stage = StrategySelectionStage(selector)  # type: ignore[arg-type]
        state = _state()
        state.query_analysis = _analysis()
        with pytest.raises(StrategyResolutionError):
            stage.run(_input(), state, _metadata())


class _FakeEngine:
    def __init__(self, *, result: Any = None, error: Exception | None = None) -> None:
        self.result = result or _make_result()
        self.error = error
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
        self.calls.append((question1, question2, kwargs))
        if self.error is not None:
            raise self.error
        return self.result


def _make_result() -> PredictionResult:
    return PredictionResult(
        predicted_label=1,
        prediction="duplicate",
        confidence=0.9,
        prob_duplicate=0.9,
        prob_non_duplicate=0.1,
        model_name="Test Model",
        latency_ms=1.0,
    )


class TestPredictionStage:
    def test_predicts_with_engine_config(self) -> None:
        engine = _FakeEngine()
        stage = PredictionStage(engine)  # type: ignore[arg-type]
        state = _state()
        state.engine_config = EngineConfiguration(model_name="Test Model", threshold=0.6, use_reflection=False)
        stage.run(_input(), state, _metadata())
        assert state.prediction_result is not None
        assert engine.calls[0][2]["model"] == "Test Model"
        assert engine.calls[0][2]["threshold"] == 0.6
        assert engine.calls[0][2]["reflect"] is False

    def test_missing_engine_config_raises(self) -> None:
        stage = PredictionStage(_FakeEngine())  # type: ignore[arg-type]
        with pytest.raises(TaskExecutionError):
            stage.run(_input(), _state(), _metadata())

    def test_engine_error_wrapped_in_task_execution_error(self) -> None:
        engine = _FakeEngine(error=RuntimeError("inference crashed"))
        stage = PredictionStage(engine)  # type: ignore[arg-type]
        state = _state()
        state.engine_config = EngineConfiguration(model_name="Test Model")
        with pytest.raises(TaskExecutionError):
            stage.run(_input(), state, _metadata())

    def test_orchestration_error_re_raised_unchanged(self) -> None:
        from ares.orchestration.exceptions import ModelUnavailableError

        engine = _FakeEngine(error=ModelUnavailableError("model gone"))
        stage = PredictionStage(engine)  # type: ignore[arg-type]
        state = _state()
        state.engine_config = EngineConfiguration(model_name="Test Model")
        with pytest.raises(ModelUnavailableError):
            stage.run(_input(), state, _metadata())


class TestResultEnrichmentStage:
    def test_attaches_trace(self) -> None:
        stage = ResultEnrichmentStage()
        state = _state()
        state.prediction_result = _make_result()
        metadata = _metadata()
        metadata.add_stage("InputValidationStage", 1.2, _success())
        stage.run(_input(), state, metadata)
        trace = state.prediction_result.orchestration_trace
        assert trace is not None
        assert "InputValidationStage" in [s["name"] for s in trace["stages"]]

    def test_missing_result_raises(self) -> None:
        stage = ResultEnrichmentStage()
        with pytest.raises(TaskExecutionError):
            stage.run(_input(), _state(), _metadata())


def _success() -> Any:
    from ares.orchestration.types import StageStatus

    return StageStatus.SUCCESS
