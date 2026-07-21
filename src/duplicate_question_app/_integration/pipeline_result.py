from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineExecutionMetadata:
    total_latency_ms: float = 0.0
    module_latencies: dict[str, float] = field(default_factory=dict)
    modules_executed: list[str] = field(default_factory=list)
    modules_skipped: list[str] = field(default_factory=list)
    memory_hits: int = 0
    memory_misses: int = 0
    routing_choice: str = ""
    confidence: float = 0.0
    reasoning_depth: str = ""
    debate_participation: int = 0
    error: str | None = None


@dataclass
class PipelineResult:
    success: bool
    context: Any
    prediction: dict[str, Any] = field(default_factory=dict)
    metadata: PipelineExecutionMetadata = field(default_factory=PipelineExecutionMetadata)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "prediction": self.prediction,
            "metadata": {
                "total_latency_ms": self.metadata.total_latency_ms,
                "module_latencies": self.metadata.module_latencies,
                "modules_executed": self.metadata.modules_executed,
                "modules_skipped": self.metadata.modules_skipped,
                "memory_hits": self.metadata.memory_hits,
                "memory_misses": self.metadata.memory_misses,
                "routing_choice": self.metadata.routing_choice,
                "confidence": self.metadata.confidence,
                "reasoning_depth": self.metadata.reasoning_depth,
                "debate_participation": self.metadata.debate_participation,
                "error": self.metadata.error,
            },
            "error": self.error,
        }
