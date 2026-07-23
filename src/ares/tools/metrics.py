from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolMetrics:
    total_invocations: int = 0
    completed_invocations: int = 0
    failed_invocations: int = 0
    timed_out_invocations: int = 0
    permission_denied_count: int = 0
    total_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    min_processing_time_ms: float = float("inf")
    tool_counts: dict[str, int] = field(default_factory=dict)
    tool_times: dict[str, list[float]] = field(default_factory=dict)

    def record_invocation(
        self,
        tool_id: str,
        success: bool,
        processing_time_ms: float,
        timed_out: bool = False,
    ) -> None:
        self.total_invocations += 1
        if timed_out:
            self.timed_out_invocations += 1
        elif success:
            self.completed_invocations += 1
        else:
            self.failed_invocations += 1
        self.total_processing_time_ms += processing_time_ms
        self.max_processing_time_ms = max(self.max_processing_time_ms, processing_time_ms)
        self.min_processing_time_ms = min(self.min_processing_time_ms, processing_time_ms)
        self.tool_counts[tool_id] = self.tool_counts.get(tool_id, 0) + 1
        if tool_id not in self.tool_times:
            self.tool_times[tool_id] = []
        self.tool_times[tool_id].append(processing_time_ms)

    def record_permission_denied(self) -> None:
        self.permission_denied_count += 1

    def average_processing_time_ms(self) -> float:
        if self.total_invocations == 0:
            return 0.0
        return self.total_processing_time_ms / self.total_invocations

    def success_rate(self) -> float:
        if self.total_invocations == 0:
            return 1.0
        return self.completed_invocations / self.total_invocations

    def reset(self) -> None:
        self.total_invocations = 0
        self.completed_invocations = 0
        self.failed_invocations = 0
        self.timed_out_invocations = 0
        self.permission_denied_count = 0
        self.total_processing_time_ms = 0.0
        self.max_processing_time_ms = 0.0
        self.min_processing_time_ms = float("inf")
        self.tool_counts.clear()
        self.tool_times.clear()
