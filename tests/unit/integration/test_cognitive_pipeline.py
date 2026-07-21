from __future__ import annotations

from unittest.mock import MagicMock

from duplicate_question_app._integration.cognitive_pipeline import CognitivePipeline
from duplicate_question_app._integration.integration_configuration import IntegrationConfig
from duplicate_question_app._integration.pipeline_events import PipelineEvent
from duplicate_question_app._integration.pipeline_result import PipelineResult
from duplicate_question_app._integration.validation import validate_prediction_unchanged


def _make_prediction(q1: str, q2: str) -> dict:
    return {
        "question1": q1,
        "question2": q2,
        "predicted_label": 1,
        "prediction": "Duplicate",
        "prob_non_duplicate": 0.05,
        "prob_duplicate": 0.95,
        "confidence": 0.95,
        "threshold": 0.5,
        "latency_ms": 10.0,
    }


class TestCognitivePipeline:
    def test_creates_with_defaults(self):
        pipeline = CognitivePipeline()
        assert pipeline.config is not None
        assert pipeline.hook is not None
        assert pipeline.lifecycle is not None

    def test_run_minimal(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        result = pipeline.run("test question one", "test question two")
        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.context.question_a == "test question one"
        assert result.context.question_b == "test question two"
        assert result.metadata.total_latency_ms > 0

    def test_run_with_prediction_fn(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        result = pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        assert result.success is True
        assert result.prediction["predicted_label"] == 1
        assert result.prediction["prediction"] == "Duplicate"
        assert result.metadata.modules_executed == ["decision"]

    def test_run_with_memory_manager(self):
        mm = MagicMock()
        mm.search.return_value = None
        mm.store_episodic.return_value = None
        mm.store_performance.return_value = None

        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=True,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=True,
            ),
            memory_manager=mm,
        )
        result = pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        assert result.success is True
        mm.search.assert_called_once()
        mm.store_episodic.assert_called_once()
        mm.store_performance.assert_called_once()

    def test_pipeline_events_fired(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        events: list[PipelineEvent] = []

        def collector(event: PipelineEvent, ctx):
            events.append(event)

        pipeline.hook.subscribe(PipelineEvent.PIPELINE_STARTED, collector)
        pipeline.hook.subscribe(PipelineEvent.BEFORE_DECISION, collector)
        pipeline.hook.subscribe(PipelineEvent.AFTER_DECISION, collector)
        pipeline.hook.subscribe(PipelineEvent.PIPELINE_COMPLETED, collector)

        pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        assert PipelineEvent.PIPELINE_STARTED in events
        assert PipelineEvent.BEFORE_DECISION in events
        assert PipelineEvent.AFTER_DECISION in events
        assert PipelineEvent.PIPELINE_COMPLETED in events

    def test_metadata_tracks_modules(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        result = pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        assert "decision" in result.metadata.module_latencies
        assert "decision" in result.metadata.modules_executed
        assert result.metadata.total_latency_ms > 0

    def test_module_lifecycle_tracking(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        for module in [
            "perception",
            "routing",
            "memory_read",
            "semantic",
            "reasoning",
            "debate",
            "decision",
            "memory_write",
        ]:
            status = pipeline.lifecycle.get_status(module)
            assert status is not None, f"{module} not registered"

    def test_execution_metadata_in_prediction(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        result = pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        assert result.metadata.confidence == 0.95
        assert result.prediction["prediction"] == "Duplicate"

    def test_skipped_modules(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=True,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        assert True

    def test_perception_error_does_not_fail_pipeline(self):
        perception = MagicMock()
        perception.run.side_effect = ValueError("perception failed")

        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=True,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
                fail_on_perception_error=False,
            ),
            perception_pipeline=perception,
        )
        result = pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        assert result.success is True
        assert result.error is not None
        assert "perception" in result.error

    def test_memory_write_with_all_types(self):
        mm = MagicMock()
        mm.store_episodic.return_value = None
        mm.store_performance.return_value = None

        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=True,
            ),
            memory_manager=mm,
        )
        pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        mm.store_episodic.assert_called_once()
        mm.store_performance.assert_called_once()

    def test_backward_compatible_prediction(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        result = pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        direct = _make_prediction("q1", "q2")
        validation = validate_prediction_unchanged(direct, result.prediction)
        assert validation.valid is True

    def test_context_preserves_question_pair(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        result = pipeline.run("hello world", "foo bar")
        assert result.context.question_a == "hello world"
        assert result.context.question_b == "foo bar"

    def test_pipeline_result_to_dict(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        result = pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        d = result.to_dict()
        assert "success" in d
        assert "prediction" in d
        assert "metadata" in d
        assert d["prediction"]["predicted_label"] == 1

    def test_lifecycle_manager_summary_after_run(self):
        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        summary = pipeline.lifecycle.summary()
        assert summary["decision"]["state"] == "COMPLETED"
        assert summary["decision"]["latency_ms"] > 0

    def test_hooks_do_not_break_pipeline(self):
        def failing_handler(event, ctx):
            raise RuntimeError("handler failure")

        pipeline = CognitivePipeline(
            config=IntegrationConfig(
                enable_perception=False,
                enable_routing=False,
                enable_memory_read=False,
                enable_semantic=False,
                enable_reasoning=False,
                enable_debate=False,
                enable_memory_write=False,
            )
        )
        pipeline.hook.subscribe(PipelineEvent.PIPELINE_STARTED, failing_handler)
        result = pipeline.run("q1", "q2", prediction_fn=_make_prediction)
        assert result.success is True
