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
        engine = (
            self._engine.with_model(model or "Week 4 Improved DistilBERT")
            .with_threshold(threshold or 0.5)
            .with_reflection(reflect if reflect is not None else True)
        )
        result = engine.predict(question1, question2)
        return result.raw if result.raw else result.to_dict()

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
            "model_label": result.get("model_label", ""),
            "latency_ms": result.get("latency_ms", elapsed),
            "trust_score": result.get("trust_score"),
            "trust_level": result.get("trust_level", "unknown"),
            "risk_level": result.get("risk_level", "unknown"),
            "timestamp": int(time.time()),
            "request_id": "",
        }

    def predict_batch(
        self,
        requests: list[dict[str, Any]],
    ) -> dict[str, Any]:
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

    def version(self) -> dict[str, Any]:
        import platform
        import sys

        return {
            "version": "0.2.0",
            "api_version": "1.0.0",
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        }

    def system_info(self) -> dict[str, Any]:
        import os
        import platform
        import sys

        import psutil
        import torch

        gpu_available = torch.cuda.is_available()
        return {
            "version": "0.2.0",
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu_cores": os.cpu_count() or 0,
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "gpu_available": gpu_available,
            "gpu_name": torch.cuda.get_device_name(0) if gpu_available else "",
            "torch_version": torch.__version__,
        }

    def run_pipeline(
        self,
        question1: str,
        question2: str,
        enable_perception: bool = True,
        enable_routing: bool = True,
        enable_memory: bool = True,
        enable_semantic: bool = True,
        enable_reasoning: bool = True,
        enable_debate: bool = True,
    ) -> dict[str, Any]:
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

    def run_reflection(
        self,
        question1: str,
        question2: str,
        prediction: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        result = self._engine.predict(question1, question2)
        return {
            "trust_score": result.trust_score or 0.0,
            "trust_level": result.trust_level or "unknown",
            "risk_level": result.risk_level or "unknown",
            "confidence": result.confidence,
            "explanation": str(result.explanations) if result.explanations else "",
            "recommendations": result.recommendations,
        }

    def search_memory(
        self,
        query: str,
        limit: int = 10,
        memory_type: str | None = None,
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        try:
            from duplicate_question_app._memory.memory_manager import MemoryManager

            mm = MemoryManager()
            results = mm.search_text(query, limit=limit)
            for e in results.entries:
                entries.append(
                    {
                        "id": str(getattr(e, "id", "")),
                        "type": str(getattr(e, "type", memory_type or "unknown")),
                        "content_json": str(getattr(e, "content", {})),
                        "confidence": float(getattr(e, "confidence", 0.0)),
                        "created_at": int(
                            time.mktime(getattr(e, "created_at", __import__("datetime").datetime.now()).timetuple())
                        ),
                    }
                )
        except Exception as e:
            logger.warning("gRPC memory search failed: %s", e)
        return entries

    def list_plugins(self) -> list[dict[str, Any]]:
        plugins: list[dict[str, Any]] = []
        try:
            from ares.plugins.manager import PluginManager

            pm = PluginManager()
            for p in pm.list():
                plugins.append(
                    {
                        "id": getattr(p, "plugin_id", ""),
                        "name": getattr(p, "name", ""),
                        "version": getattr(p, "version", ""),
                        "status": str(getattr(p, "status", "unknown")),
                    }
                )
        except Exception as e:
            logger.warning("gRPC plugin list failed: %s", e)
        return plugins
