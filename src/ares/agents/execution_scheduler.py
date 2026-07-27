from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ares.agents.agent_communication import MessageRouter
from ares.agents.execution_context import ExecutionContext
from ares.agents.manager import AgentManager
from ares.agents.task_types import AgentTaskResult, AgentTaskSpec, AgentTaskType, TaskDecomposition
from ares.agents.types import AgentExecutionStatus, AgentOutput
from ares.orchestration.retry import RetryManager
from ares.orchestration.types import RunPolicies

logger = logging.getLogger(__name__)


class ExecutionScheduler:
    def __init__(self, agent_manager: AgentManager | None = None, retry_manager: RetryManager | None = None) -> None:
        self._agent_manager = agent_manager
        self._retry_manager = retry_manager or RetryManager()
        self._message_router = MessageRouter()

    @property
    def agent_manager(self) -> AgentManager | None:
        return self._agent_manager

    @agent_manager.setter
    def agent_manager(self, mgr: AgentManager | None) -> None:
        self._agent_manager = mgr

    async def execute_decomposition(self, decomp: TaskDecomposition, context: ExecutionContext) -> TaskDecomposition:
        groups = decomp.parallel_groups
        if not groups:
            groups = self._compute_groups(decomp.tasks)

        for group in groups:
            tasks_in_group = [t for t in decomp.tasks if t.task_id in group]
            if not tasks_in_group:
                continue

            awaitables = []
            for task in tasks_in_group:
                awaitables.append(self._run_task(task, decomp, context))

            if len(awaitables) > 1:
                results = await asyncio.gather(*awaitables, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error("Task '%s' failed: %s", tasks_in_group[i].task_id, result)
                        decomp.add_result(
                            AgentTaskResult(
                                task_id=tasks_in_group[i].task_id,
                                task_type=tasks_in_group[i].task_type,
                                agent_id=tasks_in_group[i].agent_id or "",
                                success=False,
                                error=str(result),
                            )
                        )
                    elif result is not None:
                        decomp.add_result(result)
            else:
                task = tasks_in_group[0]
                result = await self._run_task(task, decomp, context)
                if result is not None:
                    decomp.add_result(result)

        return decomp

    async def _run_task(
        self, task: AgentTaskSpec, decomp: TaskDecomposition, context: ExecutionContext
    ) -> AgentTaskResult | None:
        if task.agent_id is None:
            logger.warning("No agent assigned for task '%s'", task.task_id)
            return AgentTaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                agent_id="",
                success=False,
                error="No agent assigned",
            )

        start = time.perf_counter()
        agent_output: AgentOutput | None = None
        error: str | None = None

        try:
            if self._agent_manager is not None:
                self._agent_manager.get_agent(task.agent_id)
                input_data = self._build_input(task, decomp, context)

                policies = RunPolicies(
                    timeout_seconds=task.timeout_seconds,
                    max_retries=task.max_retries,
                    retry_on_failure=True,
                )

                async def invoke() -> AgentOutput:
                    return await self._agent_manager.invoke_agent(
                        agent_id=task.agent_id,
                        input=input_data,
                    )

                agent_output = await self._retry_manager.execute_with_retry(
                    task_id=task.task_id,
                    func=invoke,
                    policies=policies,
                )
            else:
                agent_output = AgentOutput(
                    agent_id=task.agent_id,
                    status=AgentExecutionStatus.SUCCESS,
                    result={"executed": task.description},
                )

        except Exception as e:
            error = str(e)
            logger.exception("Task '%s' execution failed", task.task_id)

        elapsed_ms = (time.perf_counter() - start) * 1000

        if agent_output and agent_output.status == AgentExecutionStatus.SUCCESS:
            result = AgentTaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                agent_id=task.agent_id,
                success=True,
                output=agent_output.result or {},
                processing_time_ms=elapsed_ms,
                confidence=agent_output.confidence,
                evidence=list(agent_output.evidence),
            )
        else:
            result = AgentTaskResult(
                task_id=task.task_id,
                task_type=task.task_type,
                agent_id=task.agent_id,
                success=False,
                error=error or (agent_output.error if agent_output else "Unknown error"),
                processing_time_ms=elapsed_ms,
            )

        context.add_task_result(result)
        return result

    def _build_input(self, task: AgentTaskSpec, decomp: TaskDecomposition, context: ExecutionContext) -> dict[str, Any]:
        inp: dict[str, Any] = {
            "action": task.description,
            "task_id": task.task_id,
            "task_type": task.task_type.name,
            "trace_id": context.trace_id,
        }

        for target_key, source_key in task.input_mapping.items():
            if source_key.startswith("_"):
                key = source_key[1:]
                if key == "all_task_results":
                    inp[target_key] = {r.task_type.name: r.output for r in decomp.task_results.values()}
                elif key == "prediction_result":
                    r = context.get_task_result(AgentTaskType.PREDICT)
                    if r:
                        inp[target_key] = r.output
                elif key == "adjusted_confidence":
                    r = context.get_task_result(AgentTaskType.SEMANTIC_VALIDATE)
                    inp[target_key] = r.output.get("adjusted_confidence", context.threshold) if r else context.threshold
                elif key == "memory_key":
                    inp[target_key] = f"prediction:{context.trace_id}"
                elif key == "memory_query":
                    inp[target_key] = context.question1[:50]
                elif key == "memory_limit":
                    inp[target_key] = 10
                elif key == "memory_tags":
                    inp[target_key] = ["prediction", "multi-agent"]
                elif key == "prediction_data":
                    r = context.get_task_result(AgentTaskType.PREDICT)
                    inp[target_key] = r.output if r else {}
            elif source_key in context.__dict__:
                inp[target_key] = getattr(context, source_key)
            elif source_key in context.shared_store:
                inp[target_key] = context.shared_store[source_key]

        for t in decomp.tasks:
            if t.task_type == AgentTaskType.PREDICT:
                r = context.get_task_result(AgentTaskType.PREDICT)
                if r and r.success:
                    inp.setdefault("context", {})["prediction"] = r.output
                    inp.setdefault("context", {})["result"] = r.output
            if t.task_type == AgentTaskType.REFLECT:
                r = context.get_task_result(AgentTaskType.REFLECT)
                if r and r.success:
                    inp.setdefault("context", {})["reflection"] = r.output

        inp["question1"] = context.question1
        inp["question2"] = context.question2
        inp["goal_description"] = context.goal_description
        inp["trace_id"] = context.trace_id
        return inp

    @staticmethod
    def _compute_groups(tasks: list[AgentTaskSpec]) -> list[list[str]]:
        remaining = {t.task_id for t in tasks}
        completed: set[str] = set()
        groups: list[list[str]] = []
        deps = {t.task_id: set(t.depends_on) for t in tasks}

        while remaining:
            group = [tid for tid in remaining if deps.get(tid, set()).issubset(completed)]
            if not group:
                group = list(remaining)
            groups.append(group)
            remaining -= set(group)
            completed |= set(group)
        return groups
