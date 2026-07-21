from __future__ import annotations

from collections.abc import Callable
from typing import Any

from duplicate_question_app._evaluation.benchmark_result import AblationResult, BenchmarkResult
from duplicate_question_app._evaluation.configuration import AblationConfig
from duplicate_question_app._evaluation.evaluator import Evaluator


class AblationEngine:
    ABLATION_MODULES = {
        "no_routing": {
            "modules_enabled": ["cross_encoder", "semantic", "reasoning", "made", "memory"],
            "skipped": ["routing"],
        },
        "no_semantic": {
            "modules_enabled": ["cross_encoder", "routing", "reasoning", "made", "memory"],
            "skipped": ["semantic"],
        },
        "no_reasoning": {
            "modules_enabled": ["cross_encoder", "routing", "semantic", "made", "memory"],
            "skipped": ["reasoning"],
        },
        "no_made": {
            "modules_enabled": ["cross_encoder", "routing", "semantic", "reasoning", "memory"],
            "skipped": ["made"],
        },
        "no_memory": {
            "modules_enabled": ["cross_encoder", "routing", "semantic", "reasoning", "made"],
            "skipped": ["memory"],
        },
    }

    def __init__(self, config: AblationConfig | None = None) -> None:
        self.config = config or AblationConfig()
        self.evaluator = Evaluator()

    def run_ablation(
        self,
        full_pipeline_fn: Callable[[str, str], dict[str, Any]],
        ablated_fns: dict[str, Callable[[str, str], dict[str, Any]]],
        test_pairs: list[tuple[str, str, int]],
    ) -> AblationResult:
        y_true = [t[2] for t in test_pairs]

        def _eval(name: str, fn: Callable, modules: list[str]) -> BenchmarkResult:
            y_pred, y_prob = [], []
            for q1, q2, _ in test_pairs:
                pred = fn(q1, q2)
                y_pred.append(int(pred.get("predicted_label", 0)))
                y_prob.append(float(pred.get("prob_duplicate", 0.5)))
            import numpy as np

            return self.evaluator.evaluate_predictions(
                y_true=np.array(y_true),
                y_pred=np.array(y_pred),
                y_prob=np.array(y_prob),
                config_name=name,
                modules_enabled=modules,
            )

        full_result = _eval(
            "full_ares", full_pipeline_fn, ["cross_encoder", "routing", "semantic", "reasoning", "made", "memory"]
        )

        ablated_results: dict[str, BenchmarkResult] = {}
        for name, fn in ablated_fns.items():
            info = self.ABLATION_MODULES.get(name, {"modules_enabled": [], "skipped": []})
            ablated_results[name] = _eval(name, fn, info["modules_enabled"])

        contribution_ranking = self._compute_contribution_ranking(full_result, ablated_results)
        return AblationResult(
            full_config=full_result,
            ablated_results=ablated_results,
            contribution_ranking=contribution_ranking,
        )

    def _compute_contribution_ranking(
        self,
        full: BenchmarkResult,
        ablated: dict[str, BenchmarkResult],
    ) -> list[dict[str, Any]]:
        baseline_f1 = full.classification.f1
        contributions = []
        for name, result in ablated.items():
            delta_f1 = baseline_f1 - result.classification.f1
            contributions.append(
                {
                    "module": name,
                    "f1_without": result.classification.f1,
                    "f1_delta": delta_f1,
                    "accuracy_without": result.classification.accuracy,
                    "accuracy_delta": full.classification.accuracy - result.classification.accuracy,
                }
            )
        contributions.sort(key=lambda x: x["f1_delta"], reverse=True)
        return contributions
