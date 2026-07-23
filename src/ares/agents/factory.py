from __future__ import annotations

import logging

from ares.agents.base import Agent
from ares.agents.exceptions import AgentRegistrationError
from ares.agents.types import AgentMetadata

logger = logging.getLogger(__name__)

_agent_creators: dict[str, type[Agent]] = {}


def register_agent_type(agent_id: str, cls: type[Agent]) -> None:
    if agent_id in _agent_creators:
        raise AgentRegistrationError(detail=f"Agent type '{agent_id}' is already registered")
    _agent_creators[agent_id] = cls


def unregister_agent_type(agent_id: str) -> None:
    _agent_creators.pop(agent_id, None)


def get_agent_types() -> dict[str, type[Agent]]:
    return dict(_agent_creators)


class AgentFactory:
    def __init__(self) -> None:
        self._creators: dict[str, type[Agent]] = {}

    def register_type(self, agent_id: str, cls: type[Agent]) -> None:
        if agent_id in self._creators:
            raise AgentRegistrationError(detail=f"Agent type '{agent_id}' is already registered in factory")
        self._creators[agent_id] = cls

    def unregister_type(self, agent_id: str) -> None:
        self._creators.pop(agent_id, None)

    def create(self, agent_id: str, metadata: AgentMetadata | None = None) -> Agent:
        cls = self._creators.get(agent_id)
        if cls is None:
            raise AgentRegistrationError(detail=f"Agent type '{agent_id}' is not registered in factory")
        agent = cls()
        if metadata is not None:
            object.__setattr__(agent, "metadata", metadata)
        return agent

    def has_type(self, agent_id: str) -> bool:
        return agent_id in self._creators

    def list_types(self) -> list[str]:
        return list(self._creators.keys())

    def clear(self) -> None:
        self._creators.clear()
