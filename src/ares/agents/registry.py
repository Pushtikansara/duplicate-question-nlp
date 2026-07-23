from __future__ import annotations

import logging
from threading import Lock

from ares.agents.base import Agent
from ares.agents.exceptions import AgentNotFoundError, AgentRegistrationError
from ares.agents.types import AgentInfo, AgentPermissions, AgentStatus

logger = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}
        self._infos: dict[str, AgentInfo] = {}
        self._lock = Lock()

    def register(
        self,
        agent: Agent,
        permissions: AgentPermissions | None = None,
    ) -> str:
        agent_id = agent.metadata.agent_id
        with self._lock:
            if agent_id in self._agents:
                raise AgentRegistrationError(detail=f"Agent '{agent_id}' is already registered")
            self._agents[agent_id] = agent
            self._infos[agent_id] = AgentInfo(
                metadata=agent.metadata,
                status=AgentStatus.REGISTERED,
                permissions=permissions or AgentPermissions(agent_id=agent_id),
            )
        logger.info("Registered agent: %s (v%s)", agent_id, agent.metadata.version)
        return agent_id

    def unregister(self, agent_id: str) -> None:
        with self._lock:
            if agent_id not in self._agents:
                raise AgentNotFoundError(detail=f"Agent '{agent_id}' not found")
            del self._agents[agent_id]
            del self._infos[agent_id]
        logger.info("Unregistered agent: %s", agent_id)

    def get(self, agent_id: str) -> Agent:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise AgentNotFoundError(detail=f"Agent '{agent_id}' not found")
        return agent

    def get_info(self, agent_id: str) -> AgentInfo:
        info = self._infos.get(agent_id)
        if info is None:
            raise AgentNotFoundError(detail=f"Agent '{agent_id}' not found")
        return info

    def list_by_status(self, status: AgentStatus | None = None) -> list[AgentInfo]:
        with self._lock:
            if status is None:
                return list(self._infos.values())
            return [info for info in self._infos.values() if info.status == status]

    def list_all(self) -> list[Agent]:
        with self._lock:
            return list(self._agents.values())

    def has(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def count(self) -> int:
        return len(self._agents)

    def update_status(self, agent_id: str, status: AgentStatus) -> None:
        with self._lock:
            info = self._infos.get(agent_id)
            if info is None:
                raise AgentNotFoundError(detail=f"Agent '{agent_id}' not found")
            self._infos[agent_id] = AgentInfo(
                metadata=info.metadata,
                status=status,
                permissions=info.permissions,
                error_count=info.error_count,
                total_invocations=info.total_invocations,
                last_invocation_time=info.last_invocation_time,
                total_processing_time_ms=info.total_processing_time_ms,
            )

    def record_invocation(
        self,
        agent_id: str,
        processing_time_ms: float,
        error: bool = False,
    ) -> None:
        with self._lock:
            info = self._infos.get(agent_id)
            if info is None:
                return
            import time as _time

            self._infos[agent_id] = AgentInfo(
                metadata=info.metadata,
                status=info.status,
                permissions=info.permissions,
                error_count=info.error_count + (1 if error else 0),
                total_invocations=info.total_invocations + 1,
                last_invocation_time=_time.time(),
                total_processing_time_ms=info.total_processing_time_ms + processing_time_ms,
            )

    def get_permissions(self, agent_id: str) -> AgentPermissions:
        info = self.get_info(agent_id)
        return info.permissions

    def clear(self) -> None:
        with self._lock:
            self._agents.clear()
            self._infos.clear()
