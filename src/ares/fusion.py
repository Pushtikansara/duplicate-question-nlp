from __future__ import annotations

from typing import Any

from ares._config import get_config
from ares._result import PredictionResult
from ares.inference.dispatcher import InferenceDispatcher
from ares.model_registry import ModelBackend, build_registry


class FusionEngine:
    def __init__(self, weights: dict[str, float] | None = None):
        self._weights = weights or {}

    def get_available_models(self) -> list[str]:
        return [
            e.display_name for e in build_registry() if e.backend != ModelBackend.ENSEMBLE and e.status.value == "ready"
        ]

    def fuse(
        self,
        question1: str,
        question2: str,
        model_names: list[str] | None = None,
        threshold: float | None = None,
    ) -> PredictionResult:
        models = model_names or self.get_available_models()
        if not models:
            raise RuntimeError("No models available for fusion")

        results: list[dict[str, Any]] = []
        errors: list[str] = []

        for name in models:
            try:
                pred = InferenceDispatcher.predict(name, question1, question2, threshold)
                results.append(
                    {
                        "model_name": name,
                        "predicted_label": pred.predicted_label,
                        "confidence": pred.confidence,
                        "prob_duplicate": pred.prob_duplicate,
                        "latency_ms": pred.latency_ms,
                    }
                )
            except Exception as e:
                errors.append(f"{name}: {e}")
                results.append(
                    {
                        "model_name": name,
                        "error": str(e),
                        "predicted_label": 0,
                        "confidence": 0.0,
                        "prob_duplicate": 0.0,
                        "latency_ms": 0.0,
                    }
                )

        if not results:
            raise RuntimeError(f"All models failed: {'; '.join(errors)}")

        return self._weighted_fusion(results, question1, question2)

    def _weighted_fusion(
        self,
        results: list[dict[str, Any]],
        q1: str,
        q2: str,
    ) -> PredictionResult:
        inf_cfg = get_config("inference") or {}
        default_th = float(inf_cfg.get("default_threshold", 0.5))

        total_weight = 0.0
        weighted_prob = 0.0
        model_contributions: dict[str, dict[str, float]] = {}
        total_latency = 0.0
        error_count = 0

        for r in results:
            name = r["model_name"]
            w = self._weights.get(name, 1.0 / len(results))
            total_weight += w
            weighted_prob += r["prob_duplicate"] * w
            total_latency += r.get("latency_ms", 0)
            model_contributions[name] = {
                "weight": w,
                "prob_duplicate": r["prob_duplicate"],
                "predicted_label": r["predicted_label"],
                "confidence": r["confidence"],
                "latency_ms": r.get("latency_ms", 0),
            }
            if r.get("error"):
                error_count += 1

        fused_prob = weighted_prob / total_weight if total_weight > 0 else 0.5

        predicted_label = int(fused_prob >= default_th)
        prediction = "Duplicate" if predicted_label == 1 else "Non-Duplicate"
        confidence = max(fused_prob, 1.0 - fused_prob)

        agreement = self._compute_agreement(results)
        uncertainty = self._compute_uncertainty(results)

        return PredictionResult(
            predicted_label=predicted_label,
            prediction=prediction,
            confidence=confidence,
            prob_duplicate=fused_prob,
            prob_non_duplicate=1.0 - fused_prob,
            model_name="Semantic Ensemble",
            latency_ms=total_latency,
            selected_model="Semantic Ensemble",
            executed_model=" + ".join(r["model_name"] for r in results),
            backend="FusionEngine",
            inference_function="weighted_voting",
            threshold=default_th,
            explanations={
                "fusion_method": "weighted_voting",
                "model_count": len(results),
                "model_contributions": model_contributions,
                "agreement": agreement,
                "uncertainty": uncertainty,
                "error_count": error_count,
                "fused_probability": fused_prob,
            },
        )

    def _compute_agreement(self, results: list[dict[str, Any]]) -> float:
        if len(results) < 2:
            return 1.0
        labels = [r["predicted_label"] for r in results]
        majority = max(set(labels), key=labels.count)
        return labels.count(majority) / len(labels)

    def _compute_uncertainty(self, results: list[dict[str, Any]]) -> float:
        if len(results) < 2:
            return 0.0
        probs = [r["prob_duplicate"] for r in results]
        return float(np.std(probs)) if len(probs) > 1 else 0.0

    def get_contribution_report(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "models": [
                {
                    "name": r["model_name"],
                    "weight": self._weights.get(r["model_name"], 1.0 / len(results)),
                    "prob_duplicate": r["prob_duplicate"],
                    "predicted_label": r["predicted_label"],
                    "latency_ms": r.get("latency_ms", 0),
                }
                for r in results
            ],
            "agreement": self._compute_agreement(results),
            "uncertainty": self._compute_uncertainty(results),
        }


import numpy as np
