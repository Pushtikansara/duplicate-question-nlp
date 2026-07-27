from __future__ import annotations

from ares.agents.task_types import TASK_TO_CAPABILITIES, AgentTaskSpec, AgentTaskType
from ares.agents.types import AgentCapability


class CapabilityResolver:
    def required_capabilities(self, task_type: AgentTaskType) -> set[AgentCapability]:
        return TASK_TO_CAPABILITIES.get(task_type, set())

    def can_execute(self, task: AgentTaskSpec, agent_capabilities: set[AgentCapability]) -> bool:
        required = self.required_capabilities(task.task_type)
        if not required:
            return True
        return required.issubset(agent_capabilities)

    def rank_agents(self, task: AgentTaskSpec, agents_capabilities: dict[str, set[AgentCapability]]) -> list[str]:
        required = self.required_capabilities(task.task_type)
        scored: list[tuple[int, str]] = []
        for agent_id, caps in agents_capabilities.items():
            match_count = len(required & caps)
            if match_count > 0:
                scored.append((match_count, agent_id))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [aid for _, aid in scored]

    def best_match(self, task: AgentTaskSpec, agents_capabilities: dict[str, set[AgentCapability]]) -> str | None:
        ranked = self.rank_agents(task, agents_capabilities)
        return ranked[0] if ranked else None

    def list_uncovered(
        self, tasks: list[AgentTaskSpec], agents_capabilities: dict[str, set[AgentCapability]]
    ) -> list[AgentTaskType]:
        uncovered: list[AgentTaskType] = []
        all_caps: set[AgentCapability] = set()
        for caps in agents_capabilities.values():
            all_caps |= caps
        for task in tasks:
            required = self.required_capabilities(task.task_type)
            if required and not required.issubset(all_caps):
                uncovered.append(task.task_type)
        return uncovered
