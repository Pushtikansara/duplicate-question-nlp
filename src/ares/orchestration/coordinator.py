from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.manager import AgentManager
from ares.agents.registry import AgentRegistry
from ares.orchestration.cancellation import CancellationManager, CancellationToken
from ares.orchestration.events import OrchestrationEvent, OrchestrationEventType
from ares.orchestration.exceptions import (
    RunCancelledError,
    RunTimeoutError,
    StrategyNotFoundError,
)
from ares.orchestration.metrics import OrchestrationMetrics
from ares.orchestration.retry import RetryManager
from ares.orchestration.strategies.base import OrchestrationStrategy
from ares.orchestration.strategies.debate import DebateStrategy
from ares.orchestration.strategies.hierarchical import HierarchicalStrategy
from ares.orchestration.strategies.parallel import ParallelStrategy
from ares.orchestration.strategies.pipeline import PipelineStrategy
from ares.orchestration.strategies.sequential import SequentialStrategy
from ares.orchestration.strategies.supervisor import SupervisorStrategy
from ares.orchestration.strategies.voting import VotingStrategy
from ares.orchestration.timeout import TimeoutManager
from ares.orchestration.types import (
    AgentMessage,
    OrchestrationResult,
    OrchestrationStatus,
    OrchestrationStrategyType,
    RunPolicies,
    SharedAgentContext,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class AgentCoordinator:
    def __init__(
        self,
        agent_manager: AgentManager | None = None,
        registry: AgentRegistry | None = None,
        event_bus: Any = None,
    ) -> None:
        self._agent_manager = agent_manager or AgentManager(registry=registry or AgentRegistry())
        self._event_bus = event_bus
        self._retry_manager = RetryManager()
        self._timeout_manager = TimeoutManager()
        self._cancellation_manager = CancellationManager()
        self._metrics = OrchestrationMetrics()
        self._strategies: dict[OrchestrationStrategyType, OrchestrationStrategy] = {
            OrchestrationStrategyType.SEQUENTIAL: SequentialStrategy(),
            OrchestrationStrategyType.PARALLEL: ParallelStrategy(),
            OrchestrationStrategyType.HIERARCHICAL: HierarchicalStrategy(),
            OrchestrationStrategyType.DEBATE: DebateStrategy(),
            OrchestrationStrategyType.VOTING: VotingStrategy(),
            OrchestrationStrategyType.PIPELINE: PipelineStrategy(),
            OrchestrationStrategyType.SUPERVISOR: SupervisorStrategy(),
        }

    @property
    def agent_manager(self) -> AgentManager:
        return self._agent_manager

    @property
    def metrics(self) -> OrchestrationMetrics:
        return self._metrics

    @property
    def cancellation_manager(self) -> CancellationManager:
        return self._cancellation_manager

    @property
    def retry_manager(self) -> RetryManager:
        return self._retry_manager

    @property
    def timeout_manager(self) -> TimeoutManager:
        return self._timeout_manager

    def register_strategy(
        self,
        strategy_type: OrchestrationStrategyType,
        strategy: OrchestrationStrategy,
    ) -> None:
        self._strategies[strategy_type] = strategy

    def get_strategy(
        self,
        strategy_type: OrchestrationStrategyType,
    ) -> OrchestrationStrategy:
        strategy = self._strategies.get(strategy_type)
        if strategy is None:
            raise StrategyNotFoundError(detail=f"Strategy '{strategy_type.name}' is not registered")
        return strategy

    async def run_agents(
        self,
        agent_ids: list[str],
        input: dict[str, Any],
        strategy_type: OrchestrationStrategyType = OrchestrationStrategyType.SEQUENTIAL,
        policies: RunPolicies | None = None,
        shared_context: SharedAgentContext | None = None,
    ) -> OrchestrationResult:
        p = policies or RunPolicies()
        generated_id = f"run_{'_'.join(agent_ids)}_{int(time.time())}"
        if shared_context is not None and shared_context.workflow_id:
            workflow_id = shared_context.workflow_id
            trace_id = shared_context.trace_id or workflow_id
        else:
            workflow_id = generated_id
            trace_id = workflow_id

        if shared_context is None:
            shared_context = SharedAgentContext(
                workflow_id=workflow_id,
                trace_id=trace_id,
            )
        else:
            shared_context.workflow_id = workflow_id
            shared_context.trace_id = trace_id

        cancellation_token = self._cancellation_manager.create_token(workflow_id)

        await self._emit_event(
            OrchestrationEventType.ORCHESTRATION_STARTED,
            workflow_id=workflow_id,
            trace_id=trace_id,
            metadata={"agent_ids": agent_ids, "strategy": strategy_type.name},
        )

        agents = self._resolve_agents(agent_ids)
        strategy = self.get_strategy(strategy_type)

        await self._emit_event(
            OrchestrationEventType.STRATEGY_SELECTED,
            workflow_id=workflow_id,
            trace_id=trace_id,
            metadata={"strategy": strategy_type.name},
        )

        try:
            cancellation_token.check()

            async def execute_strategy() -> OrchestrationResult:
                return await strategy.execute(
                    agents=agents,
                    input=input,
                    shared_context=shared_context,
                    policies=p,
                )

            if p.enable_cancellation:
                result = await self._run_with_cancellation(
                    execute_strategy,
                    cancellation_token,
                    workflow_id,
                    trace_id,
                    p,
                )
            else:
                result = await self._timeout_manager.run_with_timeout(
                    workflow_id,
                    execute_strategy,
                    p.timeout_seconds,
                    p,
                )

            self._record_metrics(result, strategy_type)
            await self._emit_event(
                OrchestrationEventType.ORCHESTRATION_COMPLETED
                if result.status == OrchestrationStatus.COMPLETED
                else OrchestrationEventType.ORCHESTRATION_FAILED,
                workflow_id=workflow_id,
                trace_id=trace_id,
                new_status=result.status,
                error=result.error,
                processing_time_ms=result.processing_time_ms,
                metadata={"strategy": strategy_type.name},
            )
            return result

        except RunCancelledError as e:
            self._metrics.record_cancelled()
            await self._emit_event(
                OrchestrationEventType.ORCHESTRATION_CANCELLED,
                workflow_id=workflow_id,
                trace_id=trace_id,
                error=str(e),
            )
            return OrchestrationResult(
                workflow_id=workflow_id,
                status=OrchestrationStatus.CANCELLED,
                agent_results=[],
                task_nodes={},
                shared_context=shared_context,
                error=str(e),
                trace_id=trace_id,
                strategy=strategy_type,
            )

        except RunTimeoutError as e:
            self._metrics.record_timeout()
            await self._emit_event(
                OrchestrationEventType.ORCHESTRATION_TIMEOUT,
                workflow_id=workflow_id,
                trace_id=trace_id,
                error=str(e),
            )
            return OrchestrationResult(
                workflow_id=workflow_id,
                status=OrchestrationStatus.TIMEOUT,
                agent_results=[],
                task_nodes={},
                shared_context=shared_context,
                error=str(e),
                trace_id=trace_id,
                strategy=strategy_type,
            )

        except Exception as e:
            logger.exception("Orchestration run '%s' failed", workflow_id)
            self._metrics.record_run(False, 0.0, strategy_type.name)
            await self._emit_event(
                OrchestrationEventType.ORCHESTRATION_FAILED,
                workflow_id=workflow_id,
                trace_id=trace_id,
                error=str(e),
            )
            return OrchestrationResult(
                workflow_id=workflow_id,
                status=OrchestrationStatus.FAILED,
                agent_results=[],
                task_nodes={},
                shared_context=shared_context,
                error=str(e),
                trace_id=trace_id,
                strategy=strategy_type,
            )

        finally:
            self._cancellation_manager.remove_token(workflow_id)

    def _resolve_agents(self, agent_ids: list[str]) -> list[Agent]:
        agents: list[Agent] = []
        for agent_id in agent_ids:
            agent = self._agent_manager.get_agent(agent_id)
            agents.append(agent)
        return agents

    async def _run_with_cancellation(
        self,
        func: Any,
        token: CancellationToken,
        workflow_id: str,
        trace_id: str,
        policies: RunPolicies,
    ) -> OrchestrationResult:
        async def run_with_check() -> OrchestrationResult:
            check_task = asyncio.create_task(self._cancellation_checker(token))
            main_task = asyncio.create_task(func())
            done, pending = await asyncio.wait(
                [check_task, main_task],
                return_when=asyncio.FIRST_COMPLETED,
                timeout=policies.timeout_seconds,
            )

            for task in pending:
                task.cancel()

            if check_task in done and check_task.result():
                raise RunCancelledError(detail="Run was cancelled")

            if main_task in done:
                result: OrchestrationResult = await main_task
                return result

            raise RunTimeoutError(detail=f"Run timed out after {policies.timeout_seconds}s")

        return await self._timeout_manager.run_with_timeout(
            workflow_id,
            run_with_check,
            policies.timeout_seconds,
            policies,
        )

    async def _cancellation_checker(
        self,
        token: CancellationToken,
        interval: float = 0.1,
    ) -> bool:
        while True:
            if token.is_cancelled:
                return True
            await asyncio.sleep(interval)

    def _record_metrics(
        self,
        result: OrchestrationResult,
        strategy_type: OrchestrationStrategyType,
    ) -> None:
        success = result.status == OrchestrationStatus.COMPLETED
        self._metrics.record_run(
            success=success,
            processing_time_ms=result.processing_time_ms,
            strategy=strategy_type.name,
        )

        for node in result.task_nodes.values():
            self._metrics.record_task(
                task_id=node.id,
                success=node.status == TaskStatus.COMPLETED,
                processing_time_ms=node.processing_time_ms,
                retried=node.retry_count > 0,
            )

    async def _emit_event(
        self,
        event_type: OrchestrationEventType,
        workflow_id: str = "",
        trace_id: str = "",
        error: str | None = None,
        processing_time_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
        new_status: OrchestrationStatus | None = None,
    ) -> None:
        if self._event_bus is None:
            return
        try:
            event = OrchestrationEvent(
                event_type=event_type,
                workflow_id=workflow_id,
                error=error,
                processing_time_ms=processing_time_ms,
                metadata=metadata or {},
                trace_id=trace_id,
                new_status=new_status,
            )
            await self._event_bus.emit("orchestration", orchestration_event=event)
        except Exception:
            logger.exception("Failed to emit orchestration event")

    def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        content: dict[str, Any],
        shared_context: SharedAgentContext,
        message_type: str = "generic",
    ) -> None:
        shared_context.add_message(
            AgentMessage(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                message_type=message_type,
                trace_id=shared_context.trace_id,
            )
        )
