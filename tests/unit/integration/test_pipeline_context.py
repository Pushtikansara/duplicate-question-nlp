from __future__ import annotations

import pytest

from duplicate_question_app._integration.pipeline_context import PipelineContext


class TestPipelineContext:
    def test_creates_with_required_fields(self):
        ctx = PipelineContext(question_a="q1", question_b="q2")
        assert ctx.question_a == "q1"
        assert ctx.question_b == "q2"

    def test_is_frozen(self):
        ctx = PipelineContext(question_a="q1", question_b="q2")
        with pytest.raises(AttributeError):
            ctx.question_a = "changed"

    def test_default_values(self):
        ctx = PipelineContext(question_a="a", question_b="b")
        assert ctx.perception_result is None
        assert ctx.routing_result is None
        assert ctx.retrieved_memories == []
        assert ctx.semantic_assessment is None
        assert ctx.reasoning_result is None
        assert ctx.debate_result is None
        assert ctx.prediction_result == {}
        assert ctx.error is None

    def test_to_dict(self):
        ctx = PipelineContext(question_a="a", question_b="b", error="test error")
        d = ctx.to_dict()
        assert d["question_a"] == "a"
        assert d["question_b"] == "b"
        assert d["error"] == "test error"
        assert "perception_result" in d
        assert "routing_result" in d
        assert "retrieved_memories" in d
