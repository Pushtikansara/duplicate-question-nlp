from __future__ import annotations

import logging

from ares.agents.exceptions import AgentStateError
from ares.agents.registry import AgentRegistry
from ares.agents.types import AgentStatus

logger = logging.getLogger(__name__)

_VALID_TRANSITIONS: dict[AgentStatus, set[AgentStatus]] = {
    AgentStatus.DISCOVERED: {AgentStatus.PENDING},
    AgentStatus.PENDING: {AgentStatus.REGISTERED},
    AgentStatus.REGISTERED: {AgentStatus.LOADED, AgentStatus.DISABLED},
    AgentStatus.LOADED: {AgentStatus.ACTIVE, AgentStatus.ERROR, AgentStatus.DISABLED},
    AgentStatus.ACTIVE: {AgentStatus.PAUSED, AgentStatus.ERROR, AgentStatus.DISABLED},
    AgentStatus.PAUSED: {AgentStatus.ACTIVE, AgentStatus.DISABLED},
    AgentStatus.ERROR: {AgentStatus.ACTIVE, AgentStatus.DISABLED},
    AgentStatus.DISABLED: {AgentStatus.REGISTERED},
}


class AgentLifecycleManager:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def _transition(self, agent_id: str, target: AgentStatus) -> None:
        info = self._registry.get_info(agent_id)
        current = info.status
        allowed = _VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise AgentStateError(detail=f"Cannot transition agent '{agent_id}' from {current.name} to {target.name}")
        self._registry.update_status(agent_id, target)

    def discover(self, agent_id: str) -> None:
        info = self._registry.get_info(agent_id)
        if info.status != AgentStatus.DISCOVERED:
            self._transition(agent_id, AgentStatus.PENDING)

    def register(self, agent_id: str) -> None:
        self._transition(agent_id, AgentStatus.REGISTERED)

    async def load(self, agent_id: str) -> None:
        self._transition(agent_id, AgentStatus.LOADED)
        agent = self._registry.get(agent_id)
        try:
            await agent.on_load()
        except Exception:
            self._registry.update_status(agent_id, AgentStatus.ERROR)
            raise

    async def activate(self, agent_id: str) -> None:
        self._transition(agent_id, AgentStatus.ACTIVE)
        agent = self._registry.get(agent_id)
        try:
            await agent.on_activate()
        except Exception:
            self._registry.update_status(agent_id, AgentStatus.ERROR)
            raise

    async def pause(self, agent_id: str) -> None:
        agent = self._registry.get(agent_id)
        await agent.on_pause()
        self._transition(agent_id, AgentStatus.PAUSED)

    async def resume(self, agent_id: str) -> None:
        self._transition(agent_id, AgentStatus.ACTIVE)
        agent = self._registry.get(agent_id)
        try:
            await agent.on_resume()
        except Exception:
            self._registry.update_status(agent_id, AgentStatus.ERROR)
            raise

    async def disable(self, agent_id: str) -> None:
        agent = self._registry.get(agent_id)
        await agent.on_disable()
        self._transition(agent_id, AgentStatus.DISABLED)

    async def enable(self, agent_id: str) -> None:
        self._transition(agent_id, AgentStatus.REGISTERED)

    async def handle_error(self, agent_id: str, exc: Exception) -> None:
        agent = self._registry.get(agent_id)
        await agent.on_error(exc)
        self._registry.update_status(agent_id, AgentStatus.ERROR)
        self._registry.record_invocation(agent_id, 0.0, error=True)

    async def retry(self, agent_id: str) -> None:
        info = self._registry.get_info(agent_id)
        if info.status != AgentStatus.ERROR:
            raise AgentStateError(
                detail=f"Cannot retry agent '{agent_id}': status is {info.status.name}, expected ERROR"
            )
        max_retries = info.metadata.max_retries
        if info.error_count > max_retries:
            raise AgentStateError(detail=f"Agent '{agent_id}' has exceeded max retries ({max_retries})")
        self._transition(agent_id, AgentStatus.ACTIVE)
        agent = self._registry.get(agent_id)
        try:
            await agent.on_resume()
        except Exception:
            self._registry.update_status(agent_id, AgentStatus.ERROR)
            raise
