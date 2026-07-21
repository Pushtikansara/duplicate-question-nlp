from __future__ import annotations

from duplicate_question_app._integration.pipeline_events import PipelineEvent
from duplicate_question_app._integration.pipeline_hooks import PipelineHook


class TestPipelineHook:
    def test_subscribe_and_publish(self):
        hook = PipelineHook()
        received: list[tuple] = []

        def handler(event, ctx):
            received.append((event, ctx))

        hook.subscribe(PipelineEvent.PIPELINE_STARTED, handler)
        hook.publish(PipelineEvent.PIPELINE_STARTED, {"key": "value"})
        assert len(received) == 1
        assert received[0][0] == PipelineEvent.PIPELINE_STARTED
        assert received[0][1]["key"] == "value"

    def test_unsubscribe(self):
        hook = PipelineHook()
        received: list[tuple] = []

        def handler(event, ctx):
            received.append((event, ctx))

        hook.subscribe(PipelineEvent.PIPELINE_STARTED, handler)
        hook.unsubscribe(PipelineEvent.PIPELINE_STARTED, handler)
        hook.publish(PipelineEvent.PIPELINE_STARTED, {})
        assert len(received) == 0

    def test_multiple_handlers(self):
        hook = PipelineHook()
        results: list[int] = []

        def h1(event, ctx):
            results.append(1)

        def h2(event, ctx):
            results.append(2)

        hook.subscribe(PipelineEvent.AFTER_DECISION, h1)
        hook.subscribe(PipelineEvent.AFTER_DECISION, h2)
        hook.publish(PipelineEvent.AFTER_DECISION, {})
        assert results == [1, 2]

    def test_clear(self):
        hook = PipelineHook()
        received: list[tuple] = []

        def handler(event, ctx):
            received.append((event, ctx))

        hook.subscribe(PipelineEvent.PIPELINE_STARTED, handler)
        hook.clear()
        hook.publish(PipelineEvent.PIPELINE_STARTED, {})
        assert len(received) == 0

    def test_publish_no_handlers(self):
        hook = PipelineHook()
        hook.publish(PipelineEvent.BEFORE_PERCEPTION, {})
