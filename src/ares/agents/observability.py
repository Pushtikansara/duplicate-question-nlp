from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ares.agents.execution_context import ExecutionContext
from ares.agents.task_types import AgentTaskResult, AgentTaskSpec


@dataclass
class AgentTimelineEntry:
    agent_id: str
    task_type: str
    action: str
    status: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    error: str | None = None
    dependencies: list[str] = field(default_factory=list)


@dataclass
class ExecutionDAGEntry:
    task_id: str
    task_type: str
    agent_id: str
    status: str
    depends_on: list[str]
    level: int = 0
    duration_ms: float = 0.0


class MultiAgentObservability:
    def __init__(self) -> None:
        self._timeline: list[AgentTimelineEntry] = []
        self._dag: list[ExecutionDAGEntry] = []
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._start_time: float = 0.0

    def start_tracking(self) -> None:
        self._timeline.clear()
        self._dag.clear()
        self._snapshots.clear()
        self._start_time = time.time()

    def record_task_start(self, task: AgentTaskSpec) -> None:
        self._timeline.append(
            AgentTimelineEntry(
                agent_id=task.agent_id or "",
                task_type=task.task_type.name,
                action=task.description,
                status="RUNNING",
                start_time=time.time(),
                dependencies=list(task.depends_on),
            )
        )

    def record_task_end(self, task: AgentTaskSpec, result: AgentTaskResult) -> None:
        for entry in reversed(self._timeline):
            if entry.agent_id == (task.agent_id or "") and entry.status == "RUNNING":
                entry.end_time = time.time()
                entry.duration_ms = (entry.end_time - entry.start_time) * 1000
                entry.status = "SUCCESS" if result.success else "FAILED"
                entry.error = result.error
                break

        level = self._compute_level(task.task_id, self._timeline)
        self._dag.append(
            ExecutionDAGEntry(
                task_id=task.task_id,
                task_type=task.task_type.name,
                agent_id=task.agent_id or "",
                status="SUCCESS" if result.success else "FAILED",
                depends_on=list(task.depends_on),
                level=level,
                duration_ms=result.processing_time_ms,
            )
        )

    def snapshot(self, context: ExecutionContext) -> dict[str, Any]:
        snap = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": context.trace_id,
            "elapsed_ms": (time.time() - self._start_time) * 1000 if self._start_time else 0,
            "tasks_completed": len([e for e in self._timeline if e.status in ("SUCCESS", "FAILED")]),
            "tasks_pending": len([e for e in self._timeline if e.status == "RUNNING"]),
            "tasks_failed": len([e for e in self._timeline if e.status == "FAILED"]),
        }
        self._snapshots[snap["timestamp"]] = snap
        return snap

    def _compute_level(self, task_id: str, timeline: list[AgentTimelineEntry]) -> int:
        current = 0
        for entry in timeline:
            if task_id in entry.dependencies:
                current += 1
        return current

    def execution_dag(self) -> list[dict[str, Any]]:
        return [
            {
                "task_id": e.task_id,
                "task_type": e.task_type,
                "agent_id": e.agent_id,
                "status": e.status,
                "depends_on": e.depends_on,
                "level": e.level,
                "duration_ms": e.duration_ms,
            }
            for e in self._dag
        ]

    def agent_timeline(self) -> list[dict[str, Any]]:
        return [
            {
                "agent_id": e.agent_id,
                "task_type": e.task_type,
                "action": e.action,
                "status": e.status,
                "duration_ms": e.duration_ms,
                "error": e.error,
                "dependencies": e.dependencies,
            }
            for e in self._timeline
        ]

    def summary(self) -> dict[str, Any]:
        total = len(self._timeline)
        succeeded = sum(1 for e in self._timeline if e.status == "SUCCESS")
        failed = sum(1 for e in self._timeline if e.status == "FAILED")
        total_duration = sum(e.duration_ms for e in self._timeline)
        return {
            "total_tasks": total,
            "succeeded": succeeded,
            "failed": failed,
            "success_rate": succeeded / total if total > 0 else 0.0,
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / total if total > 0 else 0.0,
            "agents_used": list({e.agent_id for e in self._timeline}),
            "task_types": list({e.task_type for e in self._timeline}),
        }
