from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class AresGrpcService:
    def __init__(self) -> None:
        from ares._engine import ARES

        self._engine = ARES()
        self._start_time = time.time()

    def _run_prediction(
        self,
        question1: str,
        question2: str,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
    ) -> dict[str, Any]:
        engine = self._engine.with_model(model or "").with_threshold(threshold or 0.5)
        if reflect is not None:
            engine = engine.with_reflection(reflect)
        result = engine.predict(question1, question2)
        d = result.to_dict()
        d.pop("explanations", None)
        return d

    def predict(
        self,
        question1: str,
        question2: str,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
    ) -> dict[str, Any]:
        start = time.time()
        result = self._run_prediction(question1, question2, model, threshold, reflect)
        elapsed = (time.time() - start) * 1000
        return {
            "question1": question1,
            "question2": question2,
            "predicted_label": result.get("predicted_label", 0),
            "prediction": result.get("prediction", "unknown"),
            "prob_duplicate": result.get("prob_duplicate", 0.0),
            "prob_non_duplicate": result.get("prob_non_duplicate", 0.0),
            "confidence": result.get("confidence", 0.0),
            "threshold": result.get("threshold", 0.5),
            "model_label": result.get("model_name", ""),
            "latency_ms": result.get("latency_ms", elapsed),
            "trust_score": result.get("trust_score"),
            "trust_level": result.get("trust_level", "unknown"),
            "risk_level": result.get("risk_level", "unknown"),
            "timestamp": int(time.time()),
            "request_id": "",
        }

    def predict_batch(self, requests: list[dict[str, Any]]) -> dict[str, Any]:
        start = time.time()
        results = []
        successes = 0
        failures = 0
        for req in requests:
            try:
                result = self.predict(
                    req.get("question1", ""),
                    req.get("question2", ""),
                    req.get("model"),
                    req.get("threshold"),
                    req.get("reflect"),
                )
                results.append(result)
                successes += 1
            except Exception as e:
                failures += 1
                logger.warning("gRPC batch item failed: %s", e)
        total = (time.time() - start) * 1000
        return {
            "results": results,
            "total_latency_ms": total,
            "success_count": successes,
            "failure_count": failures,
        }

    def version(self) -> dict[str, Any]:
        import platform
        import sys

        from ares.api.version import API_VERSION

        return {
            "version": "0.2.0",
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "api_version": API_VERSION,
        }

    def health(self) -> dict[str, Any]:
        import torch

        components: dict[str, str] = {
            "app": "healthy",
            "torch": "healthy" if torch is not None else "unavailable",
        }
        if torch.cuda.is_available():
            components["cuda"] = "available"
            components["gpu"] = torch.cuda.get_device_name(0)
        else:
            components["cuda"] = "unavailable"
            components["gpu"] = "none"
        return {
            "status": "healthy" if all(v in ("healthy", "available") for v in components.values()) else "degraded",
            "version": "0.2.0",
            "uptime_seconds": time.time() - self._start_time,
            "components": components,
        }

    def run_pipeline(self, question1: str, question2: str, **kwargs: Any) -> dict[str, Any]:
        start = time.time()
        prediction = self._engine.predict(question1, question2)
        elapsed = (time.time() - start) * 1000
        return {
            "success": True,
            "modules_executed": ["inference"],
            "total_latency_ms": elapsed,
            "module_latencies": {"inference": prediction.latency_ms},
            "confidence": prediction.confidence,
            "error": "",
        }

    def run_reflection(self, question1: str, question2: str, prediction: dict | None = None) -> dict[str, Any]:
        result = self._engine.predict(question1, question2)
        return {
            "trust_score": result.trust_score or 0.0,
            "trust_level": result.trust_level or "unknown",
            "risk_level": result.risk_level or "unknown",
            "confidence": result.confidence,
        }
