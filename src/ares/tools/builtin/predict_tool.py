from __future__ import annotations

import logging
from typing import Any

from ares.orchestration.prediction_service import get_prediction_service
from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType

logger = logging.getLogger(__name__)


class PredictTool(Tool):
    metadata = ToolMetadata(
        tool_id="predict",
        name="Duplicate Question Predictor",
        version="1.0",
        description="Predict whether two questions are duplicates using the ARES inference engine",
        tool_type=ToolType.PYTHON,
        timeout_seconds=60.0,
        requires_permission=False,
    )

    def __init__(self) -> None:
        super().__init__()

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        question1 = input.get("question1", "")
        question2 = input.get("question2", "")
        model = input.get("model")
        threshold = input.get("threshold")
        reflect = input.get("reflect", True)

        if not question1 or not question2:
            return self.create_output(
                error="Both question1 and question2 are required",
                status=ToolStatus.ERROR,
            )

        try:
            result = get_prediction_service().predict(
                question1,
                question2,
                model=model,
                threshold=float(threshold) if threshold is not None else None,
                reflect=bool(reflect) if reflect is not None else None,
            )
            return self.create_output(
                result={
                    "predicted_label": result.predicted_label,
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    "prob_duplicate": result.prob_duplicate,
                    "prob_non_duplicate": result.prob_non_duplicate,
                    "model_name": result.model_name,
                    "latency_ms": result.latency_ms,
                    "trust_score": result.trust_score,
                    "trust_level": result.trust_level,
                    "risk_level": result.risk_level,
                    "human_review_required": result.human_review_required,
                    "recommendations": result.recommendations,
                    "explanations": result.explanations,
                }
            )
        except Exception as e:
            logger.exception("PredictTool execution failed")
            return self.create_output(
                error=f"Prediction failed: {e}",
                status=ToolStatus.ERROR,
            )
