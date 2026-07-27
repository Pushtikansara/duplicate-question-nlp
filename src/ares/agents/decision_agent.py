from __future__ import annotations

import logging
import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.task_types import AgentTaskResult, AgentTaskType
from ares.agents.types import (
    AgentCapability,
    AgentExecutionStatus,
    AgentMetadata,
    AgentOutput,
)

logger = logging.getLogger(__name__)


class DecisionAgent(Agent):
    metadata = AgentMetadata(
        agent_id="decision",
        name="Decision Agent",
        version="2.0",
        description="Aggregates all pipeline results into a final consolidated decision. NEVER silently flips prediction.",
        capabilities=frozenset({AgentCapability.REASONING, AgentCapability.CONSENSUS_BUILDING}),
        timeout_seconds=30.0,
        max_retries=2,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()

        prediction_output = input.get("prediction", {})
        if not prediction_output or "error" in prediction_output:
            elapsed = (time.perf_counter() - start) * 1000
            return self.create_output(
                status=AgentExecutionStatus.FAILURE,
                result={
                    "predicted_label": 0,
                    "prediction": "unknown",
                    "raw_confidence": 0.0,
                    "adjusted_confidence": 0.0,
                    "trust_score": 0.0,
                    "final_confidence": 0.0,
                    "model_name": prediction_output.get("model_name", ""),
                    "recommendations": ["manual_review_required"],
                    "signals": [],
                    "conflicts": [],
                },
                confidence=0.0,
                evidence=[{"type": "error", "detail": prediction_output.get("error", "Prediction unavailable")}],
                processing_time_ms=elapsed,
            )

        task_results_raw = input.get("task_results", input.get("_all", {}))
        reflection_output = input.get("reflection", {})
        semantic_output = input.get("semantic_validation", {})

        task_results: dict[str, AgentTaskResult] = {}
        for key, val in task_results_raw.items():
            if isinstance(val, dict):
                task_results[key] = AgentTaskResult(
                    task_id=val.get("task_id", key),
                    task_type=AgentTaskType[key] if key in AgentTaskType.__members__ else AgentTaskType.DECIDE,
                    agent_id=val.get("agent_id", ""),
                    success=val.get("success", False),
                    output=val.get("output", val),
                    error=val.get("error"),
                    processing_time_ms=val.get("processing_time_ms", 0.0),
                    confidence=val.get("confidence", 0.0),
                )

        prediction = prediction_output or self._extract_prediction(task_results)
        reflection = reflection_output or self._extract_reflection(task_results)
        semantic = semantic_output or self._extract_semantic(task_results)

        predicted_label = prediction.get("predicted_label", 0)
        prediction_str = prediction.get("prediction", "unknown")
        confidence = prediction.get("confidence", 0.0)
        adjusted_confidence = semantic.get("adjusted_confidence", confidence)
        trust_score = reflection.get("trust_score", confidence)

        final_confidence = self._compute_final_confidence(
            raw_confidence=confidence,
            adjusted_confidence=adjusted_confidence,
            trust_score=trust_score,
        )

        flip_record = None
        final_prediction_str = prediction_str
        if abs(final_confidence - 0.5) <= 0.05 and abs(confidence - final_confidence) > 0.1:
            final_prediction_str = "duplicate" if final_confidence >= 0.5 else "not_duplicate"
            if final_prediction_str != prediction_str.lower().replace("-", "_"):
                flip_record = {
                    "before": prediction_str,
                    "after": final_prediction_str,
                    "reason": "confidence_crossed_threshold_due_to_adjustment",
                    "rule": "final_confidence >= 0.5 -> duplicate, else not_duplicate",
                    "confidence_delta": round(final_confidence - confidence, 4),
                }

        if flip_record:
            logger.warning(
                "DecisionAgent prediction flip: %s -> %s (reason: %s, delta: %s)",
                flip_record["before"],
                flip_record["after"],
                flip_record["reason"],
                flip_record["confidence_delta"],
            )

        signals: list[dict[str, Any]] = []
        if abs(confidence - adjusted_confidence) > 0.05:
            signals.append(
                {
                    "source": "semantic_validation",
                    "type": "confidence_adjustment",
                    "from": confidence,
                    "to": adjusted_confidence,
                }
            )
        if trust_score < 0.5:
            signals.append(
                {
                    "source": "reflection",
                    "type": "low_trust",
                    "trust_score": trust_score,
                }
            )

        conflicts: list[str] = []
        if confidence > 0.8 and trust_score < 0.4:
            conflicts.append("high_prediction_confidence_vs_low_trust_score")
        if prediction_str == "duplicate" and adjusted_confidence < 0.3:
            conflicts.append("prediction_label_mismatch_with_confidence")

        predictions = self._get_recent_predictions(input)
        consistency = self._check_temporal_consistency(prediction_str, predictions)

        decision = {
            "predicted_label": predicted_label,
            "prediction": prediction_str,
            "raw_confidence": confidence,
            "adjusted_confidence": adjusted_confidence,
            "trust_score": trust_score,
            "final_confidence": final_confidence,
            "final_verdict": "duplicate" if final_confidence >= 0.5 else "not_duplicate",
            "final_prediction": final_prediction_str,
            "signals": signals,
            "conflicts": conflicts,
            "temporal_consistency": consistency,
            "model_name": prediction.get("model_name", ""),
            "flip_record": flip_record,
            "prediction_changed": flip_record is not None,
        }

        if trust_score >= 0.8:
            decision["recommendations"] = ["automatic_accept"]
        elif trust_score >= 0.5:
            decision["recommendations"] = ["review_recommended"]
        else:
            decision["recommendations"] = ["manual_review_required"]

        evidence = [
            {"type": "prediction", "confidence": confidence, "label": prediction_str},
            {"type": "semantic_validation", "adjusted_confidence": adjusted_confidence},
            {"type": "reflection", "trust_score": trust_score},
        ]

        if flip_record:
            evidence.append(
                {
                    "type": "prediction_flip",
                    "before": flip_record["before"],
                    "after": flip_record["after"],
                    "reason": flip_record["reason"],
                }
            )

        elapsed = (time.perf_counter() - start) * 1000
        return self.create_output(
            status=AgentExecutionStatus.SUCCESS,
            result=decision,
            confidence=final_confidence,
            evidence=evidence,
            processing_time_ms=elapsed,
        )

    def _compute_final_confidence(self, raw_confidence: float, adjusted_confidence: float, trust_score: float) -> float:
        from ares._config import get_config

        config = get_config("inference")
        raw_cfg = (config or {}).get("confidence", {}).get("single_model", {})
        w = {
            "raw": float(raw_cfg.get("raw", 0.50)),
            "adjusted": float(raw_cfg.get("adjusted", 0.30)),
            "trust": float(raw_cfg.get("trust", 0.20)),
        }
        weighted = w["raw"] * raw_confidence + w["adjusted"] * adjusted_confidence + w["trust"] * trust_score
        return max(0.0, min(1.0, weighted))

    def _extract_prediction(self, results: dict[str, AgentTaskResult]) -> dict[str, Any]:
        r = results.get(AgentTaskType.PREDICT.name)
        if r and r.success:
            return r.output
        for res in results.values():
            if res.task_type == AgentTaskType.PREDICT and res.success:
                return res.output
        return {}

    def _extract_reflection(self, results: dict[str, AgentTaskResult]) -> dict[str, Any]:
        r = results.get(AgentTaskType.REFLECT.name)
        if r and r.success:
            return r.output
        for res in results.values():
            if res.task_type == AgentTaskType.REFLECT and res.success:
                return res.output
        return {}

    def _extract_semantic(self, results: dict[str, AgentTaskResult]) -> dict[str, Any]:
        r = results.get(AgentTaskType.SEMANTIC_VALIDATE.name)
        if r and r.success:
            return r.output
        for res in results.values():
            if res.task_type == AgentTaskType.SEMANTIC_VALIDATE and res.success:
                return res.output
        return {}

    def _get_recent_predictions(self, input: dict[str, Any]) -> list[dict[str, Any]]:
        return input.get("recent_predictions", [])

    def _check_temporal_consistency(self, current_prediction: str, predictions: list[dict[str, Any]]) -> dict[str, Any]:
        if not predictions:
            return {"consistent": True, "reason": "no_prior_predictions"}
        same = sum(1 for p in predictions if p.get("prediction") == current_prediction)
        total = len(predictions)
        ratio = same / total if total > 0 else 1.0
        return {
            "consistent": ratio >= 0.6,
            "consistency_ratio": ratio,
            "total_prior": total,
            "matching_prior": same,
        }
