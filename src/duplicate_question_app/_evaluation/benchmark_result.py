from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PerModuleMetrics:
    module_name: str
    latency_ms: float = 0.0
    memory_bytes: int = 0
    cpu_percent: float = 0.0
    throughput: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "latency_ms": self.latency_ms,
            "memory_bytes": self.memory_bytes,
            "cpu_percent": self.cpu_percent,
            "throughput": self.throughput,
            **self.extra,
        }


@dataclass
class ClassificationMetrics:
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    roc_auc: float = 0.0
    pr_auc: float = 0.0
    brier_score: float = 0.0
    log_loss: float = 0.0
    ece: float = 0.0
    mce: float = 0.0
    mcc: float = 0.0
    balanced_accuracy: float = 0.0
    cohen_kappa: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "roc_auc": self.roc_auc,
            "pr_auc": self.pr_auc,
            "brier_score": self.brier_score,
            "log_loss": self.log_loss,
            "ece": self.ece,
            "mce": self.mce,
            "mcc": self.mcc,
            "balanced_accuracy": self.balanced_accuracy,
            "cohen_kappa": self.cohen_kappa,
        }


@dataclass
class ModuleSpecificMetrics:
    routing: dict[str, Any] = field(default_factory=dict)
    reasoning: dict[str, Any] = field(default_factory=dict)
    debate: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    explainability: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "routing": self.routing,
            "reasoning": self.reasoning,
            "debate": self.debate,
            "memory": self.memory,
            "explainability": self.explainability,
        }


@dataclass
class BenchmarkResult:
    config_name: str
    modules_enabled: list[str]
    classification: ClassificationMetrics = field(default_factory=ClassificationMetrics)
    per_module: list[PerModuleMetrics] = field(default_factory=list)
    module_specific: ModuleSpecificMetrics = field(default_factory=ModuleSpecificMetrics)
    total_latency_ms: float = 0.0
    total_memory_bytes: int = 0
    throughput: float = 0.0
    num_samples: int = 0
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_name": self.config_name,
            "modules_enabled": self.modules_enabled,
            "classification": self.classification.to_dict(),
            "per_module": [m.to_dict() for m in self.per_module],
            "module_specific": self.module_specific.to_dict(),
            "total_latency_ms": self.total_latency_ms,
            "total_memory_bytes": self.total_memory_bytes,
            "throughput": self.throughput,
            "num_samples": self.num_samples,
            "timestamp": self.timestamp,
        }


@dataclass
class AblationResult:
    full_config: BenchmarkResult
    ablated_results: dict[str, BenchmarkResult]
    contribution_ranking: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "full": self.full_config.to_dict(),
            "ablated": {k: v.to_dict() for k, v in self.ablated_results.items()},
            "contribution_ranking": self.contribution_ranking,
        }
