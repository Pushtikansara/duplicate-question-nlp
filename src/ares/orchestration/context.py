from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RequestParams:
    model: str | None = None
    threshold: float | None = None
    reflect: bool | None = None
    skip_cache: bool = False
    timeout_ms: float | None = None


@dataclass(frozen=True)
class PredictionInput:
    question1: str
    question2: str
    request_params: RequestParams = field(default_factory=RequestParams)


@dataclass
class PipelineState:
    query_analysis: Any = None
    engine_config: Any = None
    prediction_result: Any = None
    error: str | None = None
    fallback_used: bool = False
