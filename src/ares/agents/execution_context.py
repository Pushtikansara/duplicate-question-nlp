from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ares.agents.task_types import AgentTaskResult, AgentTaskType, TaskDecomposition
from ares.agents.types import AgentOutput


@dataclass
class ExecutionContext:
    trace_id: str = ""
    workflow_id: str = ""
    scenario_id: str = ""
    question1: str = ""
    question2: str = ""
    goal_description: str = ""
    model_name: str = ""
    strategy: str = "LINEAR"
    threshold: float = 0.5

    decomposition: TaskDecomposition | None = None

    task_results: dict[str, AgentTaskResult] = field(default_factory=dict)
    agent_outputs: dict[str, AgentOutput] = field(default_factory=dict)
    phase_results: dict[str, Any] = field(default_factory=dict)

    shared_store: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    started_at: float = 0.0
    completed_at: float = 0.0
    phase_timings: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
        if not self.workflow_id:
            self.workflow_id = self.trace_id
        self.started_at = time.time()

    @property
    def total_time_ms(self) -> float:
        end = self.completed_at or time.time()
        return (end - self.started_at) * 1000

    def start_phase(self, phase: str) -> None:
        self.phase_timings[f"{phase}_start"] = time.time()

    def end_phase(self, phase: str) -> float:
        elapsed = (time.time() - self.phase_timings.get(f"{phase}_start", time.time())) * 1000
        self.phase_timings[f"{phase}_ms"] = elapsed
        return elapsed

    def add_task_result(self, result: AgentTaskResult) -> None:
        self.task_results[result.task_id] = result
        if self.decomposition:
            self.decomposition.add_result(result)

    def get_task_result(self, task_type: AgentTaskType) -> AgentTaskResult | None:
        if self.decomposition:
            return self.decomposition.get_result(task_type)
        for r in self.task_results.values():
            if r.task_type == task_type:
                return r
        return None

    def add_agent_output(self, agent_id: str, output: AgentOutput) -> None:
        self.agent_outputs[agent_id] = output

    def set(self, key: str, value: Any) -> None:
        self.shared_store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.shared_store.get(key, default)

    def mark_completed(self) -> None:
        self.completed_at = time.time()

    def summary(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "scenario_id": self.scenario_id,
            "question1": self.question1,
            "question2": self.question2,
            "goal": self.goal_description,
            "model": self.model_name,
            "strategy": self.strategy,
            "total_time_ms": self.total_time_ms,
            "phase_timings": {k: v for k, v in self.phase_timings.items() if k.endswith("_ms")},
            "task_count": len(self.task_results),
            "success_count": sum(1 for r in self.task_results.values() if r.success),
            "success_rate": (
                sum(1 for r in self.task_results.values() if r.success) / len(self.task_results)
                if self.task_results
                else 0.0
            ),
        }
