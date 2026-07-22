from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from duplicate_question_app._evaluation.benchmark_result import (
    BenchmarkResult,
    ClassificationMetrics,
    ModuleSpecificMetrics,
    PerModuleMetrics,
)
from duplicate_question_app._evaluation.configuration import EvaluationConfig
from duplicate_question_app._evaluation.debate_metrics import compute_debate_metrics
from duplicate_question_app._evaluation.error_analyzer import ErrorAnalyzer
from duplicate_question_app._evaluation.explainability_metrics import compute_explainability_score
from duplicate_question_app._evaluation.latency_profiler import LatencyProfiler
from duplicate_question_app._evaluation.memory_metrics import compute_memory_metrics
from duplicate_question_app._evaluation.memory_profiler import MemoryProfiler
from duplicate_question_app._evaluation.metrics import (
    EvaluationMetrics,
    evaluate_model,
)
from duplicate_question_app._evaluation.reasoning_metrics import compute_reasoning_metrics
from duplicate_question_app._evaluation.routing_metrics import compute_routing_metrics


class Evaluator:
    def __init__(self, config: EvaluationConfig | None = None) -> None:
        self.config = config or EvaluationConfig()
        self.latency_profiler = LatencyProfiler()
        self.memory_profiler = MemoryProfiler()
        self.error_analyzer = ErrorAnalyzer()
        self._results: list[BenchmarkResult] = []

    def evaluate_predictions(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: np.ndarray,
        config_name: str = "baseline",
        modules_enabled: list[str] | None = None,
        per_module_latencies: dict[str, float] | None = None,
        routing_results: list[Any] | None = None,
        reasoning_results: list[Any] | None = None,
        debate_results: list[Any] | None = None,
        memory_manager: Any = None,
        prediction_df: pd.DataFrame | None = None,
    ) -> BenchmarkResult:
        modules = modules_enabled or []
        em: EvaluationMetrics = evaluate_model(y_true, y_pred, y_prob, config_name)

        cm = ClassificationMetrics(
            accuracy=em.accuracy,
            precision=em.precision,
            recall=em.recall,
            f1=em.f1,
            roc_auc=em.roc_auc,
            pr_auc=em.pr_auc,
            brier_score=em.brier_score,
            log_loss=em.log_loss,
            ece=em.ece,
            mce=em.mce,
        )

        per_module = []
        if per_module_latencies:
            for mod_name, lat in per_module_latencies.items():
                per_module.append(PerModuleMetrics(module_name=mod_name, latency_ms=lat))

        module_specific: dict[str, Any] = {
            "routing": compute_routing_metrics(routing_results or []),
            "reasoning": compute_reasoning_metrics(reasoning_results or []),
            "debate": compute_debate_metrics(debate_results or []),
            "memory": compute_memory_metrics(memory_manager),
            "explainability": compute_explainability_score(
                reasoning_result=reasoning_results[-1] if reasoning_results else None,
                debate_result=debate_results[-1] if debate_results else None,
                memory_manager=memory_manager,
            ),
        }

        result = BenchmarkResult(
            config_name=config_name,
            modules_enabled=modules,
            classification=cm,
            per_module=per_module,
            module_specific=ModuleSpecificMetrics(
                routing=module_specific.get("routing", {}),
                reasoning=module_specific.get("reasoning", {}),
                debate=module_specific.get("debate", {}),
                memory=module_specific.get("memory", {}),
                explainability=module_specific.get("explainability", {}),
            ),
            num_samples=len(y_true),
        )
        self._results.append(result)
        return result

    def compare_configs(self, results: list[BenchmarkResult] | None = None) -> pd.DataFrame:
        targets = results or self._results
        rows = []
        for r in targets:
            row = {"Config": r.config_name, "Modules": ", ".join(r.modules_enabled), "Samples": r.num_samples}
            row.update(r.classification.to_dict())
            rows.append(row)
        return pd.DataFrame(rows)

    def get_results(self) -> list[BenchmarkResult]:
        return list(self._results)

    def clear(self) -> None:
        self._results.clear()
        self.latency_profiler.clear()
        self.memory_profiler.clear()
