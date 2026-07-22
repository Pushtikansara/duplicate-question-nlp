from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_grpc_reflection() -> dict[str, Any]:
    return {
        "service_name": "ares.AresService",
        "methods": [
            "Predict",
            "PredictBatch",
            "PredictStream",
            "Health",
            "Version",
            "SystemInfo",
            "RunPipeline",
            "RunReflection",
            "SearchMemory",
            "ListPlugins",
        ],
    }
