from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from ares.orchestration.types import StageStatus


@dataclass
class StageResult:
    name: str
    status: StageStatus
    duration_ms: float
    detail: dict[str, Any] | None = None


@dataclass
class OrchestrationMetadata:
    start_time: float = 0.0
    stages: list[StageResult] = field(default_factory=list)
    cache_hit: bool = False

    def add_stage(
        self,
        name: str,
        duration_ms: float,
        status: StageStatus,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.stages.append(StageResult(name=name, status=status, duration_ms=duration_ms, detail=detail))

    def elapsed_ms(self) -> float:
        if self.start_time == 0.0:
            return 0.0
        return (time.time() - self.start_time) * 1000.0

    def to_trace_dict(self) -> dict[str, Any]:
        return {
            "start_time": self.start_time,
            "total_duration_ms": self.elapsed_ms(),
            "cache_hit": self.cache_hit,
            "stages": [
                {
                    "name": s.name,
                    "status": s.status.name,
                    "duration_ms": s.duration_ms,
                    "detail": s.detail,
                }
                for s in self.stages
            ],
        }


@dataclass
class ExecutionMetadata:
    request_id: str = ""
    model_name: str = ""
    strategy: str = ""
    cache_hit: bool = False
    retry_count: int = 0
    fallback_used: bool = False
    error: str | None = None
    stages: list[StageResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    stage_timings: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineResult:
    prediction_result: Any
    metadata: OrchestrationMetadata
    status: StageStatus
