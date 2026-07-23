from __future__ import annotations

from ares.tools.events import ToolEvent, ToolEventType


class TestToolEventType:
    def test_values(self):
        types = list(ToolEventType)
        assert ToolEventType.REGISTERED in types
        assert ToolEventType.UNREGISTERED in types
        assert ToolEventType.INVOKED in types
        assert ToolEventType.COMPLETED in types
        assert ToolEventType.FAILED in types
        assert ToolEventType.TIMEOUT in types
        assert ToolEventType.ERROR in types
        assert ToolEventType.PERMISSION_DENIED in types


class TestToolEvent:
    def test_create(self):
        event = ToolEvent(
            event_type=ToolEventType.INVOKED,
            tool_id="file",
            agent_id="agent_1",
            trace_id="trace_1",
        )
        assert event.event_type == ToolEventType.INVOKED
        assert event.tool_id == "file"
        assert event.agent_id == "agent_1"
        assert event.trace_id == "trace_1"

    def test_with_error(self):
        event = ToolEvent(
            event_type=ToolEventType.FAILED,
            tool_id="test",
            error="Something broke",
            processing_time_ms=150.0,
        )
        assert event.error == "Something broke"
        assert event.processing_time_ms == 150.0
