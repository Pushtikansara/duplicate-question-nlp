"""Tests for the Perception Pipeline orchestrator."""

from __future__ import annotations

from duplicate_question_app._perception.pipeline import PerceptionPipeline


class TestPerceptionPipeline:
    def test_pipeline_processes_text(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("How do I install Python on Ubuntu?")
        assert result.success
        assert result.representation is not None
        assert result.representation.language == "en"
        assert len(result.representation.tokens) > 0

    def test_pipeline_produces_normalized_text(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("  What is AI?  ")
        assert result.success
        assert result.representation is not None
        assert "artificial intelligence" in result.representation.normalized_text

    def test_pipeline_timing(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("Hello world")
        assert result.timing_ms > 0
        assert len(result.stages) > 0

    def test_pipeline_empty_text(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("")
        assert not result.success

    def test_pipeline_metadata(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("What is the capital of France?")
        assert result.success
        m = result.representation.metadata
        assert m.has_question_mark
        assert m.word_count > 0

    def test_pipeline_linguistic_features(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("How to install Python?")
        assert result.success
        ling = result.representation.linguistic
        assert ling.intent is not None

    def test_pipeline_with_extra_kwargs(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("Hello", source="test", user_id=1)
        assert result.representation is not None
        assert result.representation.extra.get("source") == "test"
        assert result.representation.extra.get("user_id") == 1

    def test_pipeline_to_dict(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("Hello world")
        assert result.success
        d = result.representation.to_dict()
        assert "raw_text" in d
        assert "normalized_text" in d
        assert "language" in d
        assert "tokens" in d
        assert "linguistic" in d
        assert "metadata" in d
        assert "validation" in d
