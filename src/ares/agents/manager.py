from __future__ import annotations

import logging
import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.context import AgentContext
from ares.agents.events import AgentEvent, AgentEventType
from ares.agents.exceptions import AgentExecutionError
from ares.agents.factory import AgentFactory
from ares.agents.lifecycle import AgentLifecycleManager
from ares.agents.registry import AgentRegistry
from ares.agents.types import (
    AgentConfig,
    AgentExecutionStatus,
    AgentInfo,
    AgentMetadata,
    AgentOutput,
    AgentPermissions,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(
        self,
        registry: AgentRegistry | None = None,
        lifecycle: AgentLifecycleManager | None = None,
        factory: AgentFactory | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        self._registry = registry or AgentRegistry()
        self._lifecycle = lifecycle or AgentLifecycleManager(self._registry)
        self._factory = factory or AgentFactory()
        self._config = config or AgentConfig()
        self._event_bus: Any = None
        self._event_handlers: dict[str, list[Any]] = {}

    @property
    def registry(self) -> AgentRegistry:
        return self._registry

    @property
    def lifecycle(self) -> AgentLifecycleManager:
        return self._lifecycle

    @property
    def factory(self) -> AgentFactory:
        return self._factory

    @property
    def config(self) -> AgentConfig:
        return self._config

    def set_event_bus(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    def _emit(self, event: AgentEvent) -> None:
        if self._event_bus and self._config.enable_event_bus:
            try:
                self._event_bus.emit("agent", event)
            except Exception:
                logger.exception("Failed to emit agent event")

    def register_agent(
        self,
        agent_cls: type[Agent],
        metadata: AgentMetadata,
        permissions: AgentPermissions | None = None,
    ) -> str:
        agent_id = metadata.agent_id
        self._factory.register_type(agent_id, agent_cls)
        agent = self._factory.create(agent_id, metadata)
        self._registry.register(agent, permissions)
        logger.info("Registered agent: %s (v%s)", agent_id, metadata.version)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.REGISTERED,
                agent_id=agent_id,
                new_status=AgentStatus.REGISTERED,
                metadata={"version": metadata.version},
            )
        )
        return agent_id

    def register_existing_agent(
        self,
        agent: Agent,
        permissions: AgentPermissions | None = None,
    ) -> str:
        agent_id = agent.metadata.agent_id
        self._registry.register(agent, permissions)
        logger.info("Registered existing agent: %s", agent_id)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.REGISTERED,
                agent_id=agent_id,
                new_status=AgentStatus.REGISTERED,
            )
        )
        return agent_id

    async def load_agent(self, agent_id: str) -> None:
        await self._lifecycle.load(agent_id)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.LOADED,
                agent_id=agent_id,
                new_status=AgentStatus.LOADED,
            )
        )

    async def activate_agent(self, agent_id: str) -> None:
        await self._lifecycle.activate(agent_id)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.ACTIVATED,
                agent_id=agent_id,
                new_status=AgentStatus.ACTIVE,
            )
        )

    async def pause_agent(self, agent_id: str) -> None:
        await self._lifecycle.pause(agent_id)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.PAUSED,
                agent_id=agent_id,
                new_status=AgentStatus.PAUSED,
            )
        )

    async def resume_agent(self, agent_id: str) -> None:
        await self._lifecycle.resume(agent_id)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.RESUMED,
                agent_id=agent_id,
                new_status=AgentStatus.ACTIVE,
            )
        )

    async def disable_agent(self, agent_id: str) -> None:
        await self._lifecycle.disable(agent_id)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.DISABLED,
                agent_id=agent_id,
                new_status=AgentStatus.DISABLED,
            )
        )

    async def enable_agent(self, agent_id: str) -> None:
        await self._lifecycle.enable(agent_id)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.REGISTERED,
                agent_id=agent_id,
                new_status=AgentStatus.REGISTERED,
            )
        )

    def get_agent(self, agent_id: str) -> Agent:
        return self._registry.get(agent_id)

    def get_agent_info(self, agent_id: str) -> AgentInfo:
        return self._registry.get_info(agent_id)

    def list_agents(self, status: AgentStatus | None = None) -> list[AgentInfo]:
        return self._registry.list_by_status(status)

    def has_agent(self, agent_id: str) -> bool:
        return self._registry.has(agent_id)

    async def invoke_agent(
        self,
        agent_id: str,
        input: dict[str, Any],
        context: AgentContext | None = None,
    ) -> AgentOutput:
        agent = self._registry.get(agent_id)
        info = self._registry.get_info(agent_id)
        if info.status != AgentStatus.ACTIVE:
            raise AgentExecutionError(detail=f"Agent '{agent_id}' is not active (status: {info.status.name})")
        if context is None:
            import logging as _logging

            context = AgentContext(
                agent_id=agent_id,
                logger=_logging.getLogger(f"ares.agents.runtime.{agent_id}"),
                config=None,
                event_bus=self._event_bus,
            )
        agent.set_context(context)
        self._emit(
            AgentEvent(
                event_type=AgentEventType.INVOKED,
                agent_id=agent_id,
                execution_status=AgentExecutionStatus.RUNNING,
                trace_id=context.trace_id,
            )
        )
        timeout = info.metadata.timeout_seconds or self._config.default_timeout_seconds
        start = time.time()
        try:
            import asyncio

            output = await asyncio.wait_for(
                agent.execute(input),
                timeout=timeout,
            )
            elapsed = (time.time() - start) * 1000
            self._registry.record_invocation(agent_id, elapsed, error=False)
            self._emit(
                AgentEvent(
                    event_type=AgentEventType.COMPLETED,
                    agent_id=agent_id,
                    execution_status=output.status,
                    processing_time_ms=elapsed,
                    error=output.error,
                    trace_id=context.trace_id,
                )
            )
            return output
        except asyncio.TimeoutError:
            elapsed = (time.time() - start) * 1000
            self._registry.record_invocation(agent_id, elapsed, error=True)
            await self._lifecycle.handle_error(agent_id, TimeoutError(f"Agent '{agent_id}' timed out after {timeout}s"))
            self._emit(
                AgentEvent(
                    event_type=AgentEventType.TIMEOUT,
                    agent_id=agent_id,
                    execution_status=AgentExecutionStatus.TIMEOUT,
                    processing_time_ms=elapsed,
                    error=f"Timed out after {timeout}s",
                    trace_id=context.trace_id,
                )
            )
            return AgentOutput(
                agent_id=agent_id,
                status=AgentExecutionStatus.TIMEOUT,
                error=f"Timed out after {timeout}s",
                processing_time_ms=elapsed,
                trace_id=context.trace_id,
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            self._registry.record_invocation(agent_id, elapsed, error=True)
            await self._lifecycle.handle_error(agent_id, e)
            self._emit(
                AgentEvent(
                    event_type=AgentEventType.FAILED,
                    agent_id=agent_id,
                    execution_status=AgentExecutionStatus.FAILURE,
                    processing_time_ms=elapsed,
                    error=str(e),
                    trace_id=context.trace_id,
                )
            )
            return AgentOutput(
                agent_id=agent_id,
                status=AgentExecutionStatus.FAILURE,
                error=str(e),
                processing_time_ms=elapsed,
                trace_id=context.trace_id,
            )

    def unregister_agent(self, agent_id: str) -> None:
        self._registry.unregister(agent_id)
        self._factory.unregister_type(agent_id)

    def shutdown(self) -> None:
        for info in self._registry.list_by_status():
            import asyncio

            try:
                asyncio.run(self._lifecycle.disable(info.metadata.agent_id))
            except Exception:
                logger.exception("Error disabling agent '%s' during shutdown", info.metadata.agent_id)
