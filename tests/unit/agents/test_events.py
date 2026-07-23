from __future__ import annotations

from ares.agents.events import AgentEvent, AgentEventType
from ares.agents.types import AgentExecutionStatus, AgentStatus


class TestAgentEventType:
    def test_has_expected_types(self) -> None:
        types = {t.name for t in AgentEventType}
        expected = {
            "DISCOVERED",
            "REGISTERED",
            "LOADED",
            "ACTIVATED",
            "PAUSED",
            "RESUMED",
            "DISABLED",
            "ERROR",
            "INVOKED",
            "COMPLETED",
            "FAILED",
            "TIMEOUT",
        }
        assert types == expected


class TestAgentEvent:
    def test_defaults(self) -> None:
        event = AgentEvent(
            event_type=AgentEventType.REGISTERED,
            agent_id="test_agent",
        )
        assert event.agent_id == "test_agent"
        assert event.error is None

    def test_with_all_fields(self) -> None:
        event = AgentEvent(
            event_type=AgentEventType.FAILED,
            agent_id="test_agent",
            previous_status=AgentStatus.ACTIVE,
            new_status=AgentStatus.ERROR,
            execution_status=AgentExecutionStatus.FAILURE,
            processing_time_ms=100.0,
            error="Something broke",
            metadata={"reason": "test"},
            trace_id="trace-123",
        )
        assert event.previous_status == AgentStatus.ACTIVE
        assert event.new_status == AgentStatus.ERROR
        assert event.processing_time_ms == 100.0
        assert event.error == "Something broke"

    def test_timestamp_is_set(self) -> None:
        event = AgentEvent(
            event_type=AgentEventType.REGISTERED,
            agent_id="test_agent",
        )
        assert event.timestamp is not None
