from __future__ import annotations

from typing import Any

from ares.agents.task_types import AgentTaskType
from ares.tools.manager import ToolManager
from ares.tools.registry import ToolRegistry
from ares.tools.types import ToolStatus

TASK_TO_REQUIRED_TOOLS: dict[AgentTaskType, list[str]] = {
    AgentTaskType.PREDICT: ["predict"],
    AgentTaskType.MEMORY_STORE: ["memory"],
    AgentTaskType.MEMORY_RETRIEVE: ["memory"],
    AgentTaskType.REFLECT: ["memory"],
}

TASK_TO_OPTIONAL_TOOLS: dict[AgentTaskType, list[str]] = {
    AgentTaskType.VALIDATE_INPUT: ["file"],
    AgentTaskType.CALIBRATE: ["file"],
    AgentTaskType.DECIDE: ["memory"],
}


class ToolDiscovery:
    def __init__(self, registry: ToolRegistry | None = None, manager: ToolManager | None = None) -> None:
        self._registry = registry or (manager.registry if manager else ToolRegistry())
        self._manager = manager

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    def required_tools(self, task_type: AgentTaskType) -> list[str]:
        return TASK_TO_REQUIRED_TOOLS.get(task_type, [])

    def optional_tools(self, task_type: AgentTaskType) -> list[str]:
        return TASK_TO_OPTIONAL_TOOLS.get(task_type, [])

    def all_relevant_tools(self, task_type: AgentTaskType) -> list[str]:
        return self.required_tools(task_type) + self.optional_tools(task_type)

    def tools_available(self, task_type: AgentTaskType) -> list[dict[str, Any]]:
        relevant = self.all_relevant_tools(task_type)
        result: list[dict[str, Any]] = []
        for tool_id in relevant:
            if self._registry.has(tool_id):
                status = self._registry.get_status(tool_id)
                tool = self._registry.get(tool_id)
                result.append(
                    {
                        "tool_id": tool_id,
                        "name": tool.metadata.name,
                        "status": status.name,
                        "available": status == ToolStatus.AVAILABLE,
                    }
                )
        return result

    def check_prerequisites(self, task_type: AgentTaskType) -> list[str]:
        missing: list[str] = []
        for tool_id in self.required_tools(task_type):
            if not self._registry.has(tool_id):
                missing.append(tool_id)
            elif self._registry.get_status(tool_id) != ToolStatus.AVAILABLE:
                missing.append(f"{tool_id}(unavailable)")
        return missing

    def list_discoverable_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "tool_id": tid,
                "name": self._registry.get(tid).metadata.name,
                "type": self._registry.get(tid).metadata.tool_type.name,
                "status": self._registry.get_status(tid).name,
            }
            for tid in self._registry.list_all()
        ]

    def find_tools_by_capability(self, capability_keyword: str) -> list[str]:
        matching: list[str] = []
        for tid in self._registry.list_all():
            tool = self._registry.get(tid)
            desc = tool.metadata.description.lower()
            name = tool.metadata.name.lower()
            if capability_keyword.lower() in desc or capability_keyword.lower() in name:
                matching.append(tid)
        return matching
