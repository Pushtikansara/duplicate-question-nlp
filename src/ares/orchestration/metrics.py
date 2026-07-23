from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationMetrics:
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    cancelled_runs: int = 0
    timed_out_runs: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    retried_tasks: int = 0
    total_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    min_processing_time_ms: float = float("inf")
    run_times: list[float] = field(default_factory=list)
    task_times: dict[str, list[float]] = field(default_factory=dict)
    strategy_counts: dict[str, int] = field(default_factory=dict)

    def record_run(
        self,
        success: bool,
        processing_time_ms: float,
        strategy: str | None = None,
    ) -> None:
        self.total_runs += 1
        if success:
            self.completed_runs += 1
        else:
            self.failed_runs += 1
        self.total_processing_time_ms += processing_time_ms
        self.max_processing_time_ms = max(self.max_processing_time_ms, processing_time_ms)
        self.min_processing_time_ms = min(self.min_processing_time_ms, processing_time_ms)
        self.run_times.append(processing_time_ms)
        if strategy:
            self.strategy_counts[strategy] = self.strategy_counts.get(strategy, 0) + 1

    def record_cancelled(self) -> None:
        self.total_runs += 1
        self.cancelled_runs += 1

    def record_timeout(self, processing_time_ms: float = 0.0) -> None:
        self.total_runs += 1
        self.timed_out_runs += 1
        self.total_processing_time_ms += processing_time_ms

    def record_task(
        self,
        task_id: str,
        success: bool,
        processing_time_ms: float,
        retried: bool = False,
    ) -> None:
        self.total_tasks += 1
        if success:
            self.completed_tasks += 1
        else:
            self.failed_tasks += 1
        if retried:
            self.retried_tasks += 1
        if task_id not in self.task_times:
            self.task_times[task_id] = []
        self.task_times[task_id].append(processing_time_ms)

    def average_processing_time_ms(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.total_processing_time_ms / self.total_runs

    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 1.0
        return self.completed_runs / self.total_runs

    def reset(self) -> None:
        self.total_runs = 0
        self.completed_runs = 0
        self.failed_runs = 0
        self.cancelled_runs = 0
        self.timed_out_runs = 0
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.retried_tasks = 0
        self.total_processing_time_ms = 0.0
        self.max_processing_time_ms = 0.0
        self.min_processing_time_ms = float("inf")
        self.run_times.clear()
        self.task_times.clear()
        self.strategy_counts.clear()
