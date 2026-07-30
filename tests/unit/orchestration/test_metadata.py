from __future__ import annotations

import dataclasses
import time

import pytest

from ares.orchestration.metadata import ExecutionMetadata, OrchestrationMetadata, PipelineResult, StageResult
from ares.orchestration.types import StageStatus


class TestStageResult:
    def test_create(self):
        result = StageResult(name="validate", status=StageStatus.SUCCESS, duration_ms=10.5)
        assert result.name == "validate"
        assert result.status == StageStatus.SUCCESS
        assert result.duration_ms == 10.5
        assert result.detail is None

    def test_with_detail(self):
        result = StageResult(
            name="predict",
            status=StageStatus.FAILED,
            duration_ms=100.0,
            detail={"error": "timeout", "attempt": 2},
        )
        assert result.detail == {"error": "timeout", "attempt": 2}

    def test_mutable(self):
        result = StageResult(name="test", status=StageStatus.SKIPPED, duration_ms=0.0)
        result.duration_ms = 5.0
        assert result.duration_ms == 5.0

    def test_str(self):
        result = StageResult(name="validate", status=StageStatus.SUCCESS, duration_ms=10.5)
        s = str(result)
        assert "validate" in s
        assert "SUCCESS" in s
        assert "10.5" in s or "10" in s


class TestOrchestrationMetadata:
    def test_defaults(self):
        meta = OrchestrationMetadata()
        assert meta.start_time == 0.0
        assert meta.stages == []
        assert meta.cache_hit is False

    def test_add_stage(self):
        meta = OrchestrationMetadata()
        meta.add_stage(name="validate", duration_ms=10.0, status=StageStatus.SUCCESS)
        assert len(meta.stages) == 1
        assert meta.stages[0].name == "validate"
        assert meta.stages[0].status == StageStatus.SUCCESS
        assert meta.stages[0].duration_ms == 10.0

    def test_add_stage_with_detail(self):
        meta = OrchestrationMetadata()
        meta.add_stage(
            name="predict",
            duration_ms=50.0,
            status=StageStatus.SUCCESS,
            detail={"model": "test"},
        )
        assert meta.stages[0].detail == {"model": "test"}

    def test_elapsed_ms_no_start(self):
        meta = OrchestrationMetadata()
        assert meta.elapsed_ms() == 0.0

    def test_elapsed_ms_with_start(self):
        meta = OrchestrationMetadata(start_time=time.time())
        elapsed = meta.elapsed_ms()
        assert elapsed > 0.0

    def test_to_trace_dict(self):
        meta = OrchestrationMetadata(start_time=1000.0)
        meta.cache_hit = True
        meta.add_stage(name="validate", duration_ms=10.0, status=StageStatus.SUCCESS)
        meta.add_stage(name="predict", duration_ms=50.0, status=StageStatus.FAILED, detail={"error": "timeout"})

        d = meta.to_trace_dict()
        assert d["start_time"] == 1000.0
        assert d["cache_hit"] is True
        assert len(d["stages"]) == 2
        assert d["stages"][0]["name"] == "validate"
        assert d["stages"][0]["status"] == "SUCCESS"
        assert d["stages"][1]["name"] == "predict"
        assert d["stages"][1]["status"] == "FAILED"
        assert d["stages"][1]["detail"] == {"error": "timeout"}


class TestExecutionMetadata:
    def test_defaults(self):
        meta = ExecutionMetadata()
        assert meta.request_id == ""
        assert meta.model_name == ""
        assert meta.strategy == ""
        assert meta.cache_hit is False
        assert meta.retry_count == 0
        assert meta.fallback_used is False
        assert meta.error is None
        assert meta.stages == []
        assert meta.total_duration_ms == 0.0
        assert meta.stage_timings == {}

    def test_create(self):
        meta = ExecutionMetadata(
            request_id="req_1",
            model_name="test_model",
            strategy="cross_encoder",
            cache_hit=True,
            retry_count=2,
            fallback_used=True,
            total_duration_ms=150.0,
            stage_timings={"validate": 10.0, "predict": 140.0},
        )
        assert meta.request_id == "req_1"
        assert meta.model_name == "test_model"
        assert meta.strategy == "cross_encoder"
        assert meta.cache_hit is True
        assert meta.retry_count == 2
        assert meta.fallback_used is True
        assert meta.total_duration_ms == 150.0
        assert meta.stage_timings == {"validate": 10.0, "predict": 140.0}

    def test_mutable(self):
        meta = ExecutionMetadata()
        meta.error = "something failed"
        assert meta.error == "something failed"
        meta.stages.append(StageResult(name="test", status=StageStatus.SUCCESS, duration_ms=5.0))
        assert len(meta.stages) == 1


class TestPipelineResult:
    def test_create(self):
        meta = OrchestrationMetadata()
        result = PipelineResult(prediction_result={"label": 1}, metadata=meta, status=StageStatus.SUCCESS)
        assert result.prediction_result == {"label": 1}
        assert result.metadata is meta
        assert result.status == StageStatus.SUCCESS

    def test_immutable(self):
        meta = OrchestrationMetadata()
        result = PipelineResult(prediction_result={"label": 1}, metadata=meta, status=StageStatus.SUCCESS)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.status = StageStatus.FAILED

    def test_with_prediction_result_object(self):
        meta = OrchestrationMetadata()

        class MockPrediction:
            pass

        pred = MockPrediction()
        result = PipelineResult(prediction_result=pred, metadata=meta, status=StageStatus.SUCCESS)
        assert result.prediction_result is pred


class TestPublicApi:
    def test_all_metadata_classes_exported(self):
        from ares.orchestration import ExecutionMetadata, OrchestrationMetadata, PipelineResult, StageResult

        assert OrchestrationMetadata is not None
        assert StageResult is not None
        assert ExecutionMetadata is not None
        assert PipelineResult is not None
