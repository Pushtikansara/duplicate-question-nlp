from __future__ import annotations

import logging
from enum import Enum, auto

from ares.agents.execution_context import ExecutionContext
from ares.agents.task_types import AgentTaskResult, AgentTaskSpec, AgentTaskType, TaskDecomposition

logger = logging.getLogger(__name__)


class FailureAction(Enum):
    RETRY = auto()
    FALLBACK = auto()
    SKIP = auto()
    ABORT = auto()


class FailureHandler:
    def __init__(self, max_global_retries: int = 3) -> None:
        self._max_global_retries = max_global_retries
        self._global_retries: dict[str, int] = {}
        self._fallback_agents: dict[AgentTaskType, str] = {}

    def register_fallback(self, task_type: AgentTaskType, agent_id: str) -> None:
        self._fallback_agents[task_type] = agent_id

    def handle_failure(
        self, task: AgentTaskSpec, result: AgentTaskResult, decomp: TaskDecomposition, context: ExecutionContext
    ) -> FailureAction:
        global_key = f"{task.task_type.name}:{context.trace_id}"
        retry_count = self._global_retries.get(global_key, 0)

        if retry_count < self._max_global_retries and task.max_retries > 0:
            self._global_retries[global_key] = retry_count + 1
            return FailureAction.RETRY

        fallback = self._fallback_agents.get(task.task_type)
        if fallback is not None and fallback != task.agent_id:
            task.agent_id = fallback
            logger.info("Falling back to agent '%s' for task '%s'", fallback, task.task_type.name)
            return FailureAction.FALLBACK

        dependents = self._find_dependents(task.task_id, decomp.tasks)
        if not dependents:
            return FailureAction.SKIP

        return FailureAction.ABORT

    def is_critical(self, task_type: AgentTaskType) -> bool:
        return task_type in (AgentTaskType.PREDICT, AgentTaskType.DECIDE)

    @staticmethod
    def _find_dependents(task_id: str, tasks: list[AgentTaskSpec]) -> list[str]:
        return [t.task_id for t in tasks if task_id in t.depends_on]

    def skip_failed_dependencies(self, decomp: TaskDecomposition) -> TaskDecomposition:
        failed_ids = {tid for tid, r in decomp.task_results.items() if not r.success}
        for task in decomp.tasks:
            if any(dep in failed_ids for dep in task.depends_on) and task.task_id not in decomp.task_results:
                decomp.add_result(
                    AgentTaskResult(
                        task_id=task.task_id,
                        task_type=task.task_type,
                        agent_id=task.agent_id or "",
                        success=False,
                        error="Skipped due to failed dependency",
                    )
                )
        return decomp

    def determine_strategy(self, task_type: AgentTaskType, error: str) -> FailureAction:
        if self.is_critical(task_type):
            return FailureAction.RETRY
        if "timeout" in error.lower():
            return FailureAction.RETRY
        if "not found" in error.lower() or "unavailable" in error.lower():
            return FailureAction.SKIP
        return FailureAction.RETRY

    def reset(self) -> None:
        self._global_retries.clear()
