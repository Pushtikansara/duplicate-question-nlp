from __future__ import annotations

import logging
from typing import Any

from ares.agents.capability_resolver import CapabilityResolver
from ares.agents.registry import AgentRegistry
from ares.agents.task_types import AgentCapability, AgentTaskSpec, TaskDecomposition
from ares.agents.types import AgentStatus

logger = logging.getLogger(__name__)


class DynamicAgentSelector:
    def __init__(self, registry: AgentRegistry | None = None, resolver: CapabilityResolver | None = None) -> None:
        self._registry = registry
        self._resolver = resolver or CapabilityResolver()
        self._selection_cache: dict[str, str] = {}

    @property
    def registry(self) -> AgentRegistry | None:
        return self._registry

    @registry.setter
    def registry(self, r: AgentRegistry | None) -> None:
        self._registry = r

    def _get_agent_capabilities(self) -> dict[str, set[AgentCapability]]:
        caps: dict[str, set[AgentCapability]] = {}
        if self._registry is None:
            return caps
        for info in self._registry.list_by_status():
            caps[info.metadata.agent_id] = set(info.metadata.capabilities)
        return caps

    def _get_active_agents(self) -> dict[str, set[AgentCapability]]:
        caps: dict[str, set[AgentCapability]] = {}
        if self._registry is None:
            return caps
        for info in self._registry.list_by_status(AgentStatus.ACTIVE):
            caps[info.metadata.agent_id] = set(info.metadata.capabilities)
        return caps

    def select_agent(self, task: AgentTaskSpec) -> str | None:
        cache_key = f"{task.task_type.name}:{hash(frozenset(task.required_capabilities))}"
        if cache_key in self._selection_cache:
            return self._selection_cache[cache_key]

        active = self._get_active_agents()
        if not active:
            all_agents = self._get_agent_capabilities()
            if not all_agents:
                return None
            active = all_agents

        agent_id = self._resolver.best_match(task, active)
        if agent_id:
            self._selection_cache[cache_key] = agent_id
        return agent_id

    def select_for_decomposition(self, decomp: TaskDecomposition) -> TaskDecomposition:
        for task in decomp.tasks:
            if task.agent_id is not None:
                continue
            agent_id = self.select_agent(task)
            if agent_id is None:
                logger.warning("No agent found for task '%s' (%s)", task.task_id, task.task_type.name)
            else:
                task.agent_id = agent_id
                logger.debug("Selected agent '%s' for task '%s'", agent_id, task.task_type.name)
        return decomp

    def available_agents_summary(self) -> dict[str, Any]:
        active = self._get_active_agents()
        return {
            "total_active": len(active),
            "agents": [{"agent_id": aid, "capabilities": [c.name for c in caps]} for aid, caps in active.items()],
            "uncovered_capabilities": self._find_uncovered(active),
        }

    def _find_uncovered(self, agents_capabilities: dict[str, set[AgentCapability]]) -> list[str]:
        all_caps: set[AgentCapability] = set()
        for caps in agents_capabilities.values():
            all_caps |= caps
        return [c.name for c in AgentCapability if c not in all_caps]

    def clear_cache(self) -> None:
        self._selection_cache.clear()
