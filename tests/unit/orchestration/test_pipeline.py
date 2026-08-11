from __future__ import annotations

from typing import Any

import pytest

from ares.orchestration.cancellation import CancellationToken
from ares.orchestration.config import EngineConfiguration
from ares.orchestration.context import PipelineState, PredictionInput, RequestParams
from ares.orchestration.exceptions import (
    InvalidStageConfigurationError,
    ModelUnavailableError,
    RunCancelledError,
    TaskExecutionError,
)
from ares.orchestration.interfaces import PipelineStage
from ares.orchestration.metadata import ExecutionMetadata, OrchestrationMetadata
from ares.orchestration.pipeline import Pipeline
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
from ares.orchestration.stage_registry import StageRegistry
from ares.orchestration.types import StageStatus


class RecordingStage(PipelineStage):
    def __init__(self, name: str, error: Exception | None = None, fail_attempts: int | None = None) -> None:
        self._name = name
        self.error = error
        self.fail_attempts = fail_attempts
        self.runs: list[int] = []

    @property
    def name(self) -> str:
        return self._name

    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None:
        self.runs.append(len(self.runs) + 1)
        if self.error is None:
            return
        if self.fail_attempts is None or len(self.runs) <= self.fail_attempts:
            raise self.error


def _input() -> PredictionInput:
    return PredictionInput(question1="a", question2="b", request_params=RequestParams())


def _state() -> PipelineState:
    return PipelineState()


def _metadata() -> OrchestrationMetadata:
    return OrchestrationMetadata()


def _registry(stages: list[RecordingStage]) -> StageRegistry:
    registry = StageRegistry()
    for stage in stages:
        registry.register(stage)
    return registry


class _Recorder:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any] | None]] = []

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append((event_type, payload))


class TestPipelineExecution:
    def test_runs_all_stages_in_order(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B"), RecordingStage("C")]
        pipeline = Pipeline(_registry(stages))
        pipeline.execute(_input(), _state(), _metadata())
        assert [s.runs for s in stages] == [[1], [1], [1]]

    def test_empty_registry_raises(self) -> None:
        pipeline = Pipeline(StageRegistry())
        with pytest.raises(InvalidStageConfigurationError):
            pipeline.execute(_input(), _state(), _metadata())

    def test_metadata_records_stage_results(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B")]
        pipeline = Pipeline(_registry(stages))
        metadata = _metadata()
        pipeline.execute(_input(), _state(), metadata)
        assert [s.name for s in metadata.stages] == ["A", "B"]
        assert all(s.status == StageStatus.SUCCESS for s in metadata.stages)
        assert all(s.duration_ms >= 0.0 for s in metadata.stages)

    def test_failed_stage_stops_pipeline(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B", error=TaskExecutionError("boom"))]
        pipeline = Pipeline(_registry(stages))
        metadata = _metadata()
        with pytest.raises(TaskExecutionError):
            pipeline.execute(_input(), _state(), metadata)
        assert metadata.stages[1].status == StageStatus.FAILED
        assert metadata.stages[1].detail == {"error": "boom"}

    def test_state_error_set_on_failure(self) -> None:
        stages = [RecordingStage("A", error=TaskExecutionError("boom"))]
        pipeline = Pipeline(_registry(stages))
        state = _state()
        with pytest.raises(TaskExecutionError):
            pipeline.execute(_input(), state, _metadata())
        assert state.error == "boom"

    def test_execution_metadata_finalized_on_success_and_failure(self) -> None:
        stages = [RecordingStage("A")]
        pipeline = Pipeline(_registry(stages))
        for failing in (False, True):
            if failing:
                stage = RecordingStage("A", error=TaskExecutionError("boom"))
                pipeline = Pipeline(_registry([stage]))
            state = _state()
            execution = ExecutionMetadata(request_id="req-1")
            state.execution_metadata = execution
            with pytest.raises(Exception) if failing else _no_raise():
                pipeline.execute(_input(), state, _metadata())
            assert len(execution.stages) == 1
            assert execution.total_duration_ms >= 0.0
            assert "A" in execution.stage_timings
            assert execution.error == ("boom" if failing else None)


class _NoRaise:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: Any) -> None:
        return None


def _no_raise() -> _NoRaise:
    return _NoRaise()


class TestRetries:
    def test_stage_retried_until_success(self) -> None:
        stage = RecordingStage("A", error=TaskExecutionError("boom"), fail_attempts=2)
        pipeline = Pipeline(
            _registry([stage]),
            retry_policy=DefaultRetryPolicy(max_attempts=3, backoff_ms=0),
        )
        pipeline.execute(_input(), _state(), _metadata())
        assert stage.runs == [1, 2, 3]

    def test_retry_exhaustion_propagates_error(self) -> None:
        stage = RecordingStage("A", error=TaskExecutionError("boom"))
        pipeline = Pipeline(
            _registry([stage]),
            retry_policy=DefaultRetryPolicy(max_attempts=2, backoff_ms=0),
        )
        with pytest.raises(TaskExecutionError):
            pipeline.execute(_input(), _state(), _metadata())
        assert stage.runs == [1, 2]

    def test_retry_count_recorded_in_execution_metadata(self) -> None:
        stage = RecordingStage("A", error=TaskExecutionError("boom"))
        pipeline = Pipeline(
            _registry([stage]),
            retry_policy=DefaultRetryPolicy(max_attempts=3, backoff_ms=0),
        )
        state = _state()
        execution = ExecutionMetadata(request_id="req")
        state.execution_metadata = execution
        with pytest.raises(TaskExecutionError):
            pipeline.execute(_input(), state, _metadata())
        assert execution.retry_count == 2

    def test_non_retryable_error_not_retried(self) -> None:
        from ares.orchestration.exceptions import InputValidationError

        stage = RecordingStage("A", error=InputValidationError("bad input"))
        pipeline = Pipeline(
            _registry([stage]),
            retry_policy=DefaultRetryPolicy(max_attempts=3, backoff_ms=0),
        )
        with pytest.raises(InputValidationError):
            pipeline.execute(_input(), _state(), _metadata())
        assert stage.runs == [1]

    def test_no_retry_policy_means_no_retry(self) -> None:
        stage = RecordingStage("A", error=TaskExecutionError("boom"))
        pipeline = Pipeline(_registry([stage]))
        with pytest.raises(TaskExecutionError):
            pipeline.execute(_input(), _state(), _metadata())
        assert stage.runs == [1]

    def test_retry_takes_backoff(self) -> None:
        stage = RecordingStage("A", error=TaskExecutionError("boom"), fail_attempts=1)
        pipeline = Pipeline(
            _registry([stage]),
            retry_policy=DefaultRetryPolicy(max_attempts=2, backoff_ms=50),
        )
        started = _now()
        pipeline.execute(_input(), _state(), _metadata())
        assert _now() - started >= 0.05


class _Clock:
    @staticmethod
    def now() -> float:
        import time

        return time.time()


def _now() -> float:
    return _Clock.now()


class TestFallback:
    def test_fallback_swaps_config_and_reruns_stage(self) -> None:
        class FailingOnceEngine:
            def __init__(self) -> None:
                self.calls: list[str] = []

            def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
                self.calls.append(kwargs.get("model", ""))
                if len(self.calls) == 1:
                    raise ModelUnavailableError("model unavailable")
                return "predicted"

        class PredictionStage(PipelineStage):
            name = "PredictionStage"

            def run(
                self,
                input: PredictionInput,
                state: PipelineState,
                metadata: OrchestrationMetadata,
            ) -> None:
                engine_config = state.engine_config
                state.prediction_result = engine.predict(
                    input.question1, input.question2, model=engine_config.model_name
                )

        engine = FailingOnceEngine()
        selection = RecordingStage("StrategySelectionStage")
        prediction = PredictionStage()
        registry = StageRegistry()
        registry.register(selection)
        registry.register(prediction)
        state = _state()
        state.engine_config = EngineConfiguration(model_name="Primary")
        pipeline = Pipeline(
            registry,
            fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback"),
        )
        pipeline.execute(_input(), state, _metadata())
        assert engine.calls == ["Primary", "Fallback"]
        assert state.fallback_used is True
        assert state.engine_config.model_name == "Fallback"

    def test_fallback_used_only_once(self) -> None:
        class AlwaysFailingEngine:
            def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
                raise ModelUnavailableError("model unavailable")

        class PredictionStage(PipelineStage):
            name = "PredictionStage"

            def run(
                self,
                input: PredictionInput,
                state: PipelineState,
                metadata: OrchestrationMetadata,
            ) -> None:
                engine.predict(input.question1, input.question2, model=state.engine_config.model_name)

        engine = AlwaysFailingEngine()
        registry = StageRegistry()
        registry.register(RecordingStage("StrategySelectionStage"))
        registry.register(PredictionStage())
        pipeline = Pipeline(
            registry,
            fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback"),
        )
        state = _state()
        state.engine_config = EngineConfiguration(model_name="Primary")
        with pytest.raises(ModelUnavailableError):
            pipeline.execute(_input(), state, _metadata())
        assert state.fallback_used is True

    def test_fallback_not_applied_to_non_prediction_stage(self) -> None:
        stage = RecordingStage("EarlyStage", error=TaskExecutionError("boom"))
        pipeline = Pipeline(
            _registry([stage]),
            fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback"),
        )
        state = _state()
        with pytest.raises(TaskExecutionError):
            pipeline.execute(_input(), state, _metadata())
        assert state.fallback_used is False

    def test_no_fallback_policy_propagates(self) -> None:
        stage = RecordingStage("PredictionStage", error=TaskExecutionError("boom"))
        pipeline = Pipeline(_registry([stage]))
        with pytest.raises(TaskExecutionError):
            pipeline.execute(_input(), _state(), _metadata())

    def test_fallback_publishes_event(self) -> None:
        class PredictionStage(PipelineStage):
            name = "PredictionStage"

            def run(
                self,
                input: PredictionInput,
                state: PipelineState,
                metadata: OrchestrationMetadata,
            ) -> None:
                raise ModelUnavailableError("model unavailable")

        recorder = _Recorder()
        registry = StageRegistry()
        registry.register(PredictionStage())
        state = _state()
        state.engine_config = EngineConfiguration(model_name="Primary")
        pipeline = Pipeline(
            registry,
            fallback_policy=DefaultFallbackPolicy(fallback_model="Fallback"),
            event_publisher=recorder,
        )
        with pytest.raises(ModelUnavailableError):
            pipeline.execute(_input(), state, _metadata())
        event_types = [event for event, _ in recorder.events]
        assert "orchestration.fallback" in event_types


class TestCancellation:
    def test_cancelled_token_aborts_pipeline(self) -> None:
        stage = RecordingStage("A")
        token = CancellationToken()
        token.cancel("user cancelled")
        pipeline = Pipeline(_registry([stage]))
        with pytest.raises(RunCancelledError):
            pipeline.execute(_input(), _state(), _metadata(), cancellation_token=token)
        assert stage.runs == []

    def test_cancellation_after_stage(self) -> None:
        class CancelDuringRun(PipelineStage):
            name = "A"

            def run(
                self,
                input: PredictionInput,
                state: PipelineState,
                metadata: OrchestrationMetadata,
            ) -> None:
                token.cancel("stop now")

        token = CancellationToken()
        stages = [CancelDuringRun(), RecordingStage("B")]
        pipeline = Pipeline(_registry(stages))
        with pytest.raises(RunCancelledError):
            pipeline.execute(_input(), _state(), _metadata(), cancellation_token=token)
        assert stages[1].runs == []


class TestEvents:
    def test_stage_lifecycle_events(self) -> None:
        recorder = _Recorder()
        stages = [RecordingStage("A")]
        pipeline = Pipeline(_registry(stages), event_publisher=recorder)
        pipeline.execute(_input(), _state(), _metadata())
        types = [event for event, _ in recorder.events]
        assert types == ["orchestration.stage.started", "orchestration.stage.complete"]

    def test_aborted_stage_publishes_abort_event(self) -> None:
        recorder = _Recorder()
        stage = RecordingStage("A", error=TaskExecutionError("boom"))
        pipeline = Pipeline(_registry([stage]), event_publisher=recorder)
        with pytest.raises(TaskExecutionError):
            pipeline.execute(_input(), _state(), _metadata())
        types = [event for event, _ in recorder.events]
        assert "orchestration.stage.aborted" in types


class TestPipelineSkipStages:
    def test_skip_stages_excludes_named_stages(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B"), RecordingStage("C")]
        pipeline = Pipeline(_registry(stages))
        pipeline.execute(_input(), _state(), _metadata(), skip_stages=("B",))
        assert stages[0].runs == [1]
        assert stages[1].runs == []
        assert stages[2].runs == [1]

    def test_skip_stages_multiple_names(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B"), RecordingStage("C")]
        pipeline = Pipeline(_registry(stages))
        pipeline.execute(_input(), _state(), _metadata(), skip_stages=("A", "C"))
        assert stages[0].runs == []
        assert stages[1].runs == [1]
        assert stages[2].runs == []

    def test_skip_stages_empty_tuple_runs_all(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B")]
        pipeline = Pipeline(_registry(stages))
        pipeline.execute(_input(), _state(), _metadata(), skip_stages=())
        assert [s.runs for s in stages] == [[1], [1]]

    def test_skip_stages_nonexistent_name_runs_all(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B")]
        pipeline = Pipeline(_registry(stages))
        pipeline.execute(_input(), _state(), _metadata(), skip_stages=("nonexistent",))
        assert [s.runs for s in stages] == [[1], [1]]

    def test_skip_stages_records_metadata_correctly(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B"), RecordingStage("C")]
        pipeline = Pipeline(_registry(stages))
        metadata = _metadata()
        pipeline.execute(_input(), _state(), metadata, skip_stages=("B",))
        assert [s.name for s in metadata.stages] == ["A", "C"]

    def test_skip_stages_preserves_state(self) -> None:
        stages = [RecordingStage("A"), RecordingStage("B")]
        pipeline = Pipeline(_registry(stages))
        state = _state()
        pipeline.execute(_input(), state, _metadata(), skip_stages=("B",))
        assert state.error is None
