from __future__ import annotations

import logging

from ares.agents.context import AgentContext


class TestAgentContext:
    def test_defaults(self) -> None:
        ctx = AgentContext(agent_id="test-agent", logger=logging.getLogger("test"))
        assert ctx.agent_id == "test-agent"
        assert ctx.workflow_id == ""
        assert ctx.trace_id == ""
        assert ctx.in_memory_store == {}
        assert ctx.metadata == {}
        assert ctx.config is None
        assert ctx.event_bus is None

    def test_with_values(self) -> None:
        ctx = AgentContext(
            agent_id="agent-1",
            logger=logging.getLogger("test"),
            workflow_id="wf-1",
            trace_id="trace-1",
            in_memory_store={"key": "value"},
            metadata={"env": "test"},
        )
        assert ctx.workflow_id == "wf-1"
        assert ctx.trace_id == "trace-1"
        assert ctx.in_memory_store["key"] == "value"
        assert ctx.metadata["env"] == "test"

    def test_in_memory_store_is_mutable(self) -> None:
        ctx = AgentContext(agent_id="a1", logger=logging.getLogger("test"))
        ctx.in_memory_store["result"] = 42
        assert ctx.in_memory_store["result"] == 42
