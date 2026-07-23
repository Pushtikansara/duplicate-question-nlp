from __future__ import annotations

from ares.orchestration.events import OrchestrationEvent, OrchestrationEventType
from ares.orchestration.types import OrchestrationStatus


class TestOrchestrationEventType:
    def test_values(self):
        types = list(OrchestrationEventType)
        assert len(types) == 14
        assert OrchestrationEventType.ORCHESTRATION_STARTED in types
        assert OrchestrationEventType.ORCHESTRATION_COMPLETED in types
        assert OrchestrationEventType.ORCHESTRATION_FAILED in types
        assert OrchestrationEventType.ORCHESTRATION_CANCELLED in types
        assert OrchestrationEventType.ORCHESTRATION_TIMEOUT in types
        assert OrchestrationEventType.TASK_STARTED in types
        assert OrchestrationEventType.TASK_COMPLETED in types
        assert OrchestrationEventType.TASK_FAILED in types
        assert OrchestrationEventType.TASK_SKIPPED in types
        assert OrchestrationEventType.TASK_RETRYING in types
        assert OrchestrationEventType.STRATEGY_SELECTED in types
        assert OrchestrationEventType.STRATEGY_COMPLETED in types
        assert OrchestrationEventType.AGENT_MESSAGE_SENT in types
        assert OrchestrationEventType.RUN_POLICY_APPLIED in types


class TestOrchestrationEvent:
    def test_create(self):
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.ORCHESTRATION_STARTED,
            workflow_id="wf_1",
            trace_id="trace_1",
        )
        assert event.event_type == OrchestrationEventType.ORCHESTRATION_STARTED
        assert event.workflow_id == "wf_1"
        assert event.trace_id == "trace_1"
        assert event.error is None

    def test_with_error(self):
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.TASK_FAILED,
            workflow_id="wf_1",
            task_id="task_1",
            error="Something failed",
            processing_time_ms=150.0,
            metadata={"retry_count": 2},
        )
        assert event.event_type == OrchestrationEventType.TASK_FAILED
        assert event.task_id == "task_1"
        assert event.error == "Something failed"
        assert event.processing_time_ms == 150.0
        assert event.metadata == {"retry_count": 2}

    def test_with_status_transition(self):
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.ORCHESTRATION_COMPLETED,
            previous_status=OrchestrationStatus.RUNNING,
            new_status=OrchestrationStatus.COMPLETED,
        )
        assert event.previous_status == OrchestrationStatus.RUNNING
        assert event.new_status == OrchestrationStatus.COMPLETED
