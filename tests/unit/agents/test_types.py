from __future__ import annotations

from ares.agents.types import (
    AgentCapability,
    AgentConfig,
    AgentExecutionStatus,
    AgentInfo,
    AgentMetadata,
    AgentOutput,
    AgentPermissions,
    AgentStatus,
)


class TestAgentStatus:
    def test_has_all_states(self) -> None:
        states = {s.name for s in AgentStatus}
        expected = {"DISCOVERED", "PENDING", "REGISTERED", "LOADED", "ACTIVE", "PAUSED", "ERROR", "DISABLED"}
        assert states == expected

    def test_values_are_unique(self) -> None:
        values = [s.value for s in AgentStatus]
        assert len(values) == len(set(values))


class TestAgentCapability:
    def test_has_expected_capabilities(self) -> None:
        caps = {c.name for c in AgentCapability}
        assert "PREDICTION" in caps
        assert "MEMORY" in caps
        assert "REASONING" in caps
        assert "PLANNING" in caps


class TestAgentExecutionStatus:
    def test_has_all_statuses(self) -> None:
        statuses = {s.name for s in AgentExecutionStatus}
        assert "SUCCESS" in statuses
        assert "FAILURE" in statuses
        assert "TIMEOUT" in statuses


class TestAgentMetadata:
    def test_defaults(self) -> None:
        m = AgentMetadata(agent_id="a1", name="Test", version="1.0")
        assert m.description == ""
        assert isinstance(m.capabilities, frozenset)
        assert m.tools_required == ()
        assert m.timeout_seconds == 30.0

    def test_frozen(self) -> None:
        m = AgentMetadata(agent_id="a1", name="Test", version="1.0")
        import dataclasses

        assert dataclasses.is_dataclass(m)
        assert m.agent_id == "a1"


class TestAgentPermissions:
    def test_defaults(self) -> None:
        p = AgentPermissions(agent_id="a1")
        assert p.allowed_tools == ()
        assert p.max_invocations_per_minute == 1000

    def test_frozen(self) -> None:
        p = AgentPermissions(agent_id="a1")
        import dataclasses

        assert dataclasses.is_dataclass(p)


class TestAgentConfig:
    def test_defaults(self) -> None:
        c = AgentConfig()
        assert c.max_concurrency == 10
        assert c.default_timeout_seconds == 30.0
        assert c.audit_log_enabled is True


class TestAgentOutput:
    def test_defaults(self) -> None:
        o = AgentOutput(agent_id="a1", status=AgentExecutionStatus.SUCCESS)
        assert o.result == {}
        assert o.confidence == 0.0
        assert o.warnings == []
        assert o.error is None

    def test_with_values(self) -> None:
        o = AgentOutput(
            agent_id="a1",
            status=AgentExecutionStatus.SUCCESS,
            result={"key": "value"},
            confidence=0.9,
            processing_time_ms=15.0,
        )
        assert o.result["key"] == "value"
        assert o.confidence == 0.9


class TestAgentInfo:
    def test_defaults(self) -> None:
        m = AgentMetadata(agent_id="a1", name="Test", version="1.0")
        p = AgentPermissions(agent_id="a1")
        info = AgentInfo(metadata=m, status=AgentStatus.ACTIVE, permissions=p)
        assert info.error_count == 0
        assert info.total_invocations == 0

    def test_with_counts(self) -> None:
        m = AgentMetadata(agent_id="a1", name="Test", version="1.0")
        p = AgentPermissions(agent_id="a1")
        info = AgentInfo(
            metadata=m,
            status=AgentStatus.ACTIVE,
            permissions=p,
            error_count=3,
            total_invocations=50,
        )
        assert info.error_count == 3
        assert info.total_invocations == 50
