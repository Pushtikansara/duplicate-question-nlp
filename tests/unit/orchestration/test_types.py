from __future__ import annotations

from ares.orchestration.types import (
    AgentMessage,
    OrchestrationResult,
    OrchestrationStatus,
    OrchestrationStrategyType,
    RunPolicies,
    SharedAgentContext,
    StageStatus,
    TaskEdge,
    TaskNode,
    TaskStatus,
)


class TestAgentMessage:
    def test_create(self):
        msg = AgentMessage(
            sender_id="agent_a",
            recipient_id="agent_b",
            content={"key": "value"},
        )
        assert msg.sender_id == "agent_a"
        assert msg.recipient_id == "agent_b"
        assert msg.content == {"key": "value"}
        assert msg.message_type == "generic"
        assert msg.trace_id == ""

    def test_custom_type(self):
        msg = AgentMessage(
            sender_id="a",
            recipient_id="b",
            content={"data": 1},
            message_type="vote",
            trace_id="trace_1",
            metadata={"round": 1},
        )
        assert msg.message_type == "vote"
        assert msg.trace_id == "trace_1"
        assert msg.metadata == {"round": 1}


class TestSharedAgentContext:
    def test_create(self):
        ctx = SharedAgentContext(workflow_id="wf_1", trace_id="trace_1")
        assert ctx.workflow_id == "wf_1"
        assert ctx.trace_id == "trace_1"
        assert ctx.messages == []
        assert ctx.shared_store == {}

    def test_add_and_get_messages(self):
        ctx = SharedAgentContext()
        msg1 = AgentMessage(sender_id="a", recipient_id="b", content={"k": "v1"})
        msg2 = AgentMessage(sender_id="b", recipient_id="a", content={"k": "v2"})
        ctx.add_message(msg1)
        ctx.add_message(msg2)
        assert len(ctx.messages) == 2
        assert len(ctx.get_messages(sender_id="a")) == 1
        assert len(ctx.get_messages(recipient_id="a")) == 1

    def test_shared_store(self):
        ctx = SharedAgentContext()
        ctx.set("key1", "value1")
        assert ctx.get("key1") == "value1"
        assert ctx.get("nonexistent") is None
        assert ctx.get("nonexistent", "default") == "default"


class TestTaskNode:
    def test_create(self):
        node = TaskNode(id="task_1", agent_id="agent_1")
        assert node.id == "task_1"
        assert node.agent_id == "agent_1"
        assert node.status == TaskStatus.PENDING
        assert node.depends_on == []
        assert node.input == {}
        assert node.output is None

    def test_with_dependencies(self):
        node = TaskNode(
            id="task_2",
            agent_id="agent_2",
            depends_on=["task_1"],
            input={"data": "test"},
            metadata={"priority": "high"},
        )
        assert node.depends_on == ["task_1"]
        assert node.input == {"data": "test"}
        assert node.metadata == {"priority": "high"}


class TestTaskEdge:
    def test_create(self):
        edge = TaskEdge(source_id="a", target_id="b")
        assert edge.source_id == "a"
        assert edge.target_id == "b"
        assert edge.condition is None

    def test_with_condition(self):
        edge = TaskEdge(source_id="a", target_id="b", condition="${result.confidence} > 0.5")
        assert edge.condition is not None


class TestOrchestrationResult:
    def test_create(self):
        result = OrchestrationResult(
            workflow_id="wf_1",
            status=OrchestrationStatus.COMPLETED,
            agent_results=[],
            task_nodes={},
            shared_context=SharedAgentContext(),
        )
        assert result.workflow_id == "wf_1"
        assert result.status == OrchestrationStatus.COMPLETED

    def test_with_error(self):
        result = OrchestrationResult(
            workflow_id="wf_1",
            status=OrchestrationStatus.FAILED,
            agent_results=[],
            task_nodes={},
            shared_context=SharedAgentContext(),
            error="Something went wrong",
            strategy=OrchestrationStrategyType.SEQUENTIAL,
        )
        assert result.error == "Something went wrong"
        assert result.strategy == OrchestrationStrategyType.SEQUENTIAL


class TestRunPolicies:
    def test_defaults(self):
        p = RunPolicies()
        assert p.timeout_seconds == 60.0
        assert p.max_concurrency == 10
        assert p.retry_on_failure is True
        assert p.max_retries == 3
        assert p.retry_backoff_base == 1.0
        assert p.partial_results_on_timeout is True
        assert p.stop_on_first_error is False
        assert p.enable_cancellation is True

    def test_custom(self):
        p = RunPolicies(
            timeout_seconds=30.0,
            max_concurrency=5,
            retry_on_failure=False,
            stop_on_first_error=True,
        )
        assert p.timeout_seconds == 30.0
        assert p.max_concurrency == 5
        assert p.retry_on_failure is False
        assert p.stop_on_first_error is True


class TestOrchestrationStrategyType:
    def test_values(self):
        types = list(OrchestrationStrategyType)
        assert len(types) == 7
        assert OrchestrationStrategyType.SEQUENTIAL in types
        assert OrchestrationStrategyType.PARALLEL in types
        assert OrchestrationStrategyType.HIERARCHICAL in types
        assert OrchestrationStrategyType.DEBATE in types
        assert OrchestrationStrategyType.VOTING in types
        assert OrchestrationStrategyType.PIPELINE in types
        assert OrchestrationStrategyType.SUPERVISOR in types


class TestOrchestrationStatus:
    def test_values(self):
        statuses = list(OrchestrationStatus)
        assert OrchestrationStatus.PENDING in statuses
        assert OrchestrationStatus.RUNNING in statuses
        assert OrchestrationStatus.COMPLETED in statuses
        assert OrchestrationStatus.FAILED in statuses
        assert OrchestrationStatus.PARTIAL in statuses
        assert OrchestrationStatus.CANCELLED in statuses
        assert OrchestrationStatus.TIMEOUT in statuses


class TestStageStatus:
    def test_values(self):
        statuses = list(StageStatus)
        assert StageStatus.SUCCESS in statuses
        assert StageStatus.FAILED in statuses
        assert StageStatus.SKIPPED in statuses

    def test_enum_values(self):
        assert StageStatus.SUCCESS.name == "SUCCESS"
        assert StageStatus.FAILED.name == "FAILED"
        assert StageStatus.SKIPPED.name == "SKIPPED"
