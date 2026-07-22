from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from duplicate_question_app._evaluation.benchmark_result import BenchmarkResult
from duplicate_question_app._evaluation.configuration import EvaluationConfig
from duplicate_question_app._evaluation.evaluator import Evaluator
from duplicate_question_app._evaluation.latency_profiler import LatencyProfiler
from duplicate_question_app._evaluation.memory_profiler import MemoryProfiler


class BenchmarkRunner:
    CONFIGURATIONS = {
        "baseline": {
            "modules_enabled": ["cross_encoder"],
            "enable_perception": False,
            "enable_routing": False,
            "enable_memory_read": False,
            "enable_semantic": False,
            "enable_reasoning": False,
            "enable_debate": False,
            "enable_memory_write": False,
        },
        "config_a": {
            "modules_enabled": ["cross_encoder", "semantic"],
            "enable_perception": True,
            "enable_routing": False,
            "enable_memory_read": False,
            "enable_semantic": True,
            "enable_reasoning": False,
            "enable_debate": False,
            "enable_memory_write": False,
        },
        "config_b": {
            "modules_enabled": ["cross_encoder", "semantic", "reasoning"],
            "enable_perception": True,
            "enable_routing": False,
            "enable_memory_read": False,
            "enable_semantic": True,
            "enable_reasoning": True,
            "enable_debate": False,
            "enable_memory_write": False,
        },
        "config_c": {
            "modules_enabled": ["cross_encoder", "semantic", "reasoning", "made"],
            "enable_perception": True,
            "enable_routing": False,
            "enable_memory_read": False,
            "enable_semantic": True,
            "enable_reasoning": True,
            "enable_debate": True,
            "enable_memory_write": False,
        },
        "config_d_full": {
            "modules_enabled": ["cross_encoder", "routing", "semantic", "reasoning", "made", "memory"],
            "enable_perception": True,
            "enable_routing": True,
            "enable_memory_read": True,
            "enable_semantic": True,
            "enable_reasoning": True,
            "enable_debate": True,
            "enable_memory_write": True,
        },
    }

    def __init__(
        self,
        config: EvaluationConfig | None = None,
        pipeline_fn: Callable | None = None,
    ) -> None:
        self.config = config or EvaluationConfig()
        self.pipeline_fn = pipeline_fn
        self.evaluator = Evaluator(self.config)
        self.latency_profiler = LatencyProfiler()
        self.memory_profiler = MemoryProfiler()
        self._results: dict[str, BenchmarkResult] = {}

    def run_configuration(
        self,
        config_name: str,
        prediction_fn: Callable[[str, str], dict[str, Any]] | None = None,
        test_pairs: list[tuple[str, str, int]] | None = None,
    ) -> BenchmarkResult:
        cfg = self.CONFIGURATIONS.get(config_name)
        if cfg is None:
            raise ValueError(f"Unknown configuration: {config_name}. Choose from {list(self.CONFIGURATIONS.keys())}")

        if test_pairs is None:
            test_pairs = []

        y_true_list: list[int] = []
        y_pred_list: list[int] = []
        y_prob_list: list[float] = []
        per_module_latencies: dict[str, float] = {}

        for q1, q2, true_label in test_pairs:
            self.latency_profiler.start()
            if prediction_fn is not None:
                pred = prediction_fn(q1, q2)
                y_pred_list.append(int(pred.get("predicted_label", 0)))
                y_prob_list.append(float(pred.get("prob_duplicate", 0.5)))
            else:
                y_pred_list.append(0)
                y_prob_list.append(0.5)
            y_true_list.append(true_label)

        modules_val: Any = cfg.get("modules_enabled", [])
        modules_enabled_val: list[str] = list(modules_val) if modules_val else []
        result = self.evaluator.evaluate_predictions(
            y_true=np.array(y_true_list),
            y_pred=np.array(y_pred_list),
            y_prob=np.array(y_prob_list),
            config_name=config_name,
            modules_enabled=modules_enabled_val,
            per_module_latencies=per_module_latencies,
        )
        self._results[config_name] = result
        return result

    def run_all_configurations(
        self,
        prediction_fn: Callable[[str, str], dict[str, Any]] | None = None,
        test_pairs: list[tuple[str, str, int]] | None = None,
    ) -> dict[str, BenchmarkResult]:
        for config_name in self.CONFIGURATIONS:
            self.run_configuration(config_name, prediction_fn, test_pairs)
        return dict(self._results)

    def get_comparison(self) -> pd.DataFrame:
        return self.evaluator.compare_configs(list(self._results.values()))

    def get_results(self) -> dict[str, BenchmarkResult]:
        return dict(self._results)

    def clear(self) -> None:
        self._results.clear()
        self.evaluator.clear()
        self.latency_profiler.clear()
        self.memory_profiler.clear()
