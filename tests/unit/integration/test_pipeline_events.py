from __future__ import annotations

from duplicate_question_app._integration.pipeline_events import PipelineEvent


class TestPipelineEvents:
    def test_all_events_present(self):
        expected = [
            "PIPELINE_STARTED",
            "BEFORE_PERCEPTION",
            "AFTER_PERCEPTION",
            "BEFORE_ROUTING",
            "AFTER_ROUTING",
            "BEFORE_MEMORY_READ",
            "AFTER_MEMORY_READ",
            "BEFORE_SEMANTIC",
            "AFTER_SEMANTIC",
            "BEFORE_REASONING",
            "AFTER_REASONING",
            "BEFORE_DEBATE",
            "AFTER_DEBATE",
            "BEFORE_DECISION",
            "AFTER_DECISION",
            "BEFORE_MEMORY_WRITE",
            "AFTER_MEMORY_WRITE",
            "PIPELINE_COMPLETED",
            "PIPELINE_FAILED",
        ]
        for name in expected:
            assert hasattr(PipelineEvent, name), f"Missing event: {name}"

    def test_events_are_unique(self):
        values = [e.value for e in PipelineEvent]
        assert len(values) == len(set(values))
