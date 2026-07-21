"""Integration tests: PerceptionPipeline with Linguistic Intelligence Layer."""

from __future__ import annotations

from duplicate_question_app._perception.pipeline import PerceptionPipeline


class TestPipelineIntegration:
    def test_pipeline_embeds_linguistic_profile(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("How to install Python on Ubuntu?")
        assert result.success
        assert result.representation is not None
        assert result.representation.linguistic_profile is not None

    def test_linguistic_profile_has_language(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("What is machine learning?")
        lp = result.representation.linguistic_profile
        assert lp.language == "en"

    def test_linguistic_profile_has_intent(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("How to install Python?")
        lp = result.representation.linguistic_profile
        assert lp.intent is not None

    def test_linguistic_profile_has_keywords(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("How to install Python on Ubuntu?")
        lp = result.representation.linguistic_profile
        assert len(lp.keywords) > 0

    def test_linguistic_profile_has_complexity(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("The implementation of convolutional neural networks is complex.")
        lp = result.representation.linguistic_profile
        assert lp.complexity.overall > 0.0

    def test_linguistic_profile_has_quality_metrics(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("What is the capital of France?")
        lp = result.representation.linguistic_profile
        assert lp.quality_metrics.quality_score > 0.0

    def test_pipeline_to_dict_includes_linguistic_profile(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("Hello world")
        d = result.representation.to_dict()
        assert "linguistic_profile" in d
        assert d["linguistic_profile"]["language"] == "en"

    def test_pipeline_stages_include_linguistic_intelligence(self):
        pipeline = PerceptionPipeline()
        result = pipeline.run("Hello world")
        assert "linguistic_intelligence" in result.stages
        assert result.stages["linguistic_intelligence"] > 0.0
