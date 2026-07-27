from __future__ import annotations

import tempfile
from typing import Any

import pytest

from ares.agents.base import Agent
from ares.agents.types import (
    AgentCapability,
    AgentExecutionStatus,
    AgentMetadata,
    AgentOutput,
)
from ares.orchestration.coordinator import AgentCoordinator
from ares.orchestration.types import (
    OrchestrationStatus,
    OrchestrationStrategyType,
)
from ares.tools.builtin.file_tool import FileTool
from ares.tools.builtin.memory_tool import MemoryTool
from ares.tools.manager import ToolManager


class ToolUsingAgent(Agent):
    def __init__(self, tool_manager: ToolManager, agent_id: str = "tool_user") -> None:
        super().__init__()
        self._tool_manager = tool_manager
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"ToolUser-{agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        tool_id = input.get("tool_id", "file")
        tool_input = {k: v for k, v in input.items() if k != "tool_id"}

        result = await self._tool_manager.invoke_tool(
            tool_id=tool_id,
            input=tool_input,
            agent_id=self.metadata.agent_id,
        )

        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={
                "tool_result": result.result,
                "tool_status": result.status.name,
                "tool_error": result.error,
            },
            confidence=1.0,
        )


class TestToolOrchestrationIntegration:
    @pytest.fixture
    def tool_manager(self):
        tm = ToolManager()
        tm.registry.register(FileTool(allowed_paths=[tempfile.gettempdir()]))
        tm.registry.register(MemoryTool())
        return tm

    @pytest.fixture
    def coordinator(self, tool_manager):
        c = AgentCoordinator()
        # Register the ToolUsingAgent
        agent = ToolUsingAgent(tool_manager, agent_id="tool_user")
        c.agent_manager.register_existing_agent(agent)
        return c

    async def test_agent_uses_file_tool(self, coordinator):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("integration test")
            tmp_path = f.name

        result = await coordinator.run_agents(
            agent_ids=["tool_user"],
            input={
                "tool_id": "file",
                "operation": "read",
                "path": tmp_path,
            },
            strategy_type=OrchestrationStrategyType.SEQUENTIAL,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        agent_result = result.agent_results[0]
        assert agent_result.result["tool_result"]["content"] == "integration test"

    async def test_agent_uses_memory_tool(self, tool_manager, coordinator):
        # First store data via tool manager
        await tool_manager.invoke_tool(
            "memory",
            {"operation": "set", "key": "greeting", "value": "hello world", "namespace": "test"},
        )

        result = await coordinator.run_agents(
            agent_ids=["tool_user"],
            input={
                "tool_id": "memory",
                "operation": "get",
                "key": "greeting",
                "namespace": "test",
            },
            strategy_type=OrchestrationStrategyType.SEQUENTIAL,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        agent_result = result.agent_results[0]
        assert agent_result.result["tool_result"]["entries"][0]["value"] == "hello world"

    async def test_parallel_tool_usage(self, tool_manager, coordinator):
        agent_a = ToolUsingAgent(tool_manager, agent_id="tool_user_a")
        agent_b = ToolUsingAgent(tool_manager, agent_id="tool_user_b")
        coordinator.agent_manager.register_existing_agent(agent_a)
        coordinator.agent_manager.register_existing_agent(agent_b)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("parallel test")
            tmp_path = f.name

        result = await coordinator.run_agents(
            agent_ids=["tool_user_a", "tool_user_b"],
            input={
                "tool_id": "file",
                "operation": "read",
                "path": tmp_path,
            },
            strategy_type=OrchestrationStrategyType.PARALLEL,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 2

    async def test_tool_metrics_collected(self, tool_manager):
        await tool_manager.invoke_tool("file", {"operation": "exists", "path": "/tmp"})
        await tool_manager.invoke_tool("memory", {"operation": "set", "key": "k", "value": "v"})

        assert tool_manager.metrics.total_invocations == 2
        assert tool_manager.metrics.completed_invocations == 2
        assert "file" in tool_manager.metrics.tool_counts
        assert "memory" in tool_manager.metrics.tool_counts
