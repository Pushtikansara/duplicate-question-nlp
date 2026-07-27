from __future__ import annotations

import uuid
from typing import Any

from ares.agents.task_types import AgentTaskSpec, AgentTaskType, TaskDecomposition


class TaskDecomposer:
    def decompose(
        self, goal_description: str, include_reflection: bool = True, include_memory: bool = True
    ) -> TaskDecomposition:
        decomp = TaskDecomposition(goal_description=goal_description)
        tasks: list[AgentTaskSpec] = []
        prev_id: str | None = None

        validate = AgentTaskSpec(
            task_id=str(uuid.uuid4()),
            task_type=AgentTaskType.VALIDATE_INPUT,
            input_mapping={"question1": "question1", "question2": "question2"},
            timeout_seconds=10.0,
        )
        tasks.append(validate)
        prev_id = validate.task_id

        select_model = AgentTaskSpec(
            task_id=str(uuid.uuid4()),
            task_type=AgentTaskType.SELECT_MODEL,
            depends_on=[prev_id],
            input_mapping={"model_name": "model_name", "goal": "goal_description"},
            timeout_seconds=10.0,
        )
        tasks.append(select_model)
        prev_id = select_model.task_id

        predict = AgentTaskSpec(
            task_id=str(uuid.uuid4()),
            task_type=AgentTaskType.PREDICT,
            depends_on=[prev_id],
            input_mapping={
                "question1": "question1",
                "question2": "question2",
                "model": "model_name",
                "threshold": "threshold",
            },
            timeout_seconds=60.0,
            max_retries=2,
        )
        tasks.append(predict)
        prev_id = predict.task_id

        semantic = AgentTaskSpec(
            task_id=str(uuid.uuid4()),
            task_type=AgentTaskType.SEMANTIC_VALIDATE,
            depends_on=[prev_id],
            input_mapping={"question1": "question1", "question2": "question2", "prediction": "_prediction_result"},
            timeout_seconds=15.0,
        )
        tasks.append(semantic)
        prev_id = semantic.task_id

        calibrate = AgentTaskSpec(
            task_id=str(uuid.uuid4()),
            task_type=AgentTaskType.CALIBRATE,
            depends_on=[prev_id],
            input_mapping={"confidence": "_adjusted_confidence", "model": "model_name"},
            timeout_seconds=10.0,
        )
        tasks.append(calibrate)

        memory_ids: list[str] = []
        if include_memory:
            mem_store = AgentTaskSpec(
                task_id=str(uuid.uuid4()),
                task_type=AgentTaskType.MEMORY_STORE,
                depends_on=[calibrate.task_id],
                input_mapping={"key": "_memory_key", "value": "_prediction_data", "tags": "_memory_tags"},
                timeout_seconds=15.0,
            )
            tasks.append(mem_store)
            memory_ids.append(mem_store.task_id)

            mem_retrieve = AgentTaskSpec(
                task_id=str(uuid.uuid4()),
                task_type=AgentTaskType.MEMORY_RETRIEVE,
                depends_on=[calibrate.task_id],
                input_mapping={"query": "_memory_query", "limit": "_memory_limit"},
                timeout_seconds=15.0,
            )
            tasks.append(mem_retrieve)
            memory_ids.append(mem_retrieve.task_id)

        reflect_deps = [calibrate.task_id] + memory_ids if memory_ids else [calibrate.task_id]

        if include_reflection:
            reflect = AgentTaskSpec(
                task_id=str(uuid.uuid4()),
                task_type=AgentTaskType.REFLECT,
                depends_on=reflect_deps,
                input_mapping={
                    "prediction": "_prediction_result",
                    "confidence": "_adjusted_confidence",
                    "question1": "question1",
                    "question2": "question2",
                },
                timeout_seconds=30.0,
            )
            tasks.append(reflect)
            decide_deps = [reflect.task_id]
        else:
            decide_deps = reflect_deps

        decide = AgentTaskSpec(
            task_id=str(uuid.uuid4()),
            task_type=AgentTaskType.DECIDE,
            depends_on=decide_deps,
            input_mapping={"_all": "_all_task_results"},
            timeout_seconds=15.0,
        )
        tasks.append(decide)

        for task in tasks:
            decomp.add_task(task)

        decomp.parallel_groups = self._compute_parallel_groups(tasks)
        return decomp

    def _compute_parallel_groups(self, tasks: list[AgentTaskSpec]) -> list[list[str]]:
        remaining = {t.task_id for t in tasks}
        completed: set[str] = set()
        groups: list[list[str]] = []

        while remaining:
            group = [tid for tid in remaining if all(dep in completed for dep in self._get_deps(tid, tasks))]
            if not group:
                group = list(remaining)
            groups.append(group)
            remaining -= set(group)
            completed |= set(group)
        return groups

    @staticmethod
    def _get_deps(task_id: str, tasks: list[AgentTaskSpec]) -> list[str]:
        for t in tasks:
            if t.task_id == task_id:
                return t.depends_on
        return []

    def create_default_decomposition(self) -> TaskDecomposition:
        return self.decompose("Analyze semantic similarity between two questions")

    def to_dict(self, decomp: TaskDecomposition) -> dict[str, Any]:
        return {
            "goal": decomp.goal_description,
            "task_count": len(decomp.tasks),
            "parallel_groups": decomp.parallel_groups,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "task_type": t.task_type.name,
                    "description": t.description,
                    "depends_on": t.depends_on,
                    "agent_id": t.agent_id,
                    "timeout": t.timeout_seconds,
                }
                for t in decomp.tasks
            ],
        }
