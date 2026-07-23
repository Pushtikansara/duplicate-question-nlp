from __future__ import annotations

from ares.memory import MemoryContext


class TestMemoryContext:
    def test_create_context(self, memory_context: MemoryContext) -> None:
        assert memory_context.agent_id == "agent-1"
        assert memory_context.workflow_id == "workflow-1"
        assert memory_context.trace_id == "trace-1"
        assert memory_context.session_id == "session-1"

    def test_set_and_get(self, memory_context: MemoryContext) -> None:
        memory_context.set("custom_key", "custom_value")
        assert memory_context.get("custom_key") == "custom_value"

    def test_get_default(self, memory_context: MemoryContext) -> None:
        assert memory_context.get("nonexistent") is None
        assert memory_context.get("nonexistent", 42) == 42

    def test_default_context(self) -> None:
        ctx = MemoryContext()
        assert ctx.agent_id == ""
        assert ctx.metadata == {}
