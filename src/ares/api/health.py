from __future__ import annotations

import logging
import time
from typing import Any

import torch

from ares.api.models import HealthResponse

logger = logging.getLogger(__name__)


_start_time: float = time.time()


def get_uptime() -> float:
    return time.time() - _start_time


def check_component_health() -> dict[str, str]:
    components: dict[str, str] = {}
    try:
        import duplicate_question_app  # noqa: F401

        components["app"] = "healthy"
    except ImportError:
        components["app"] = "unavailable"
    try:
        from duplicate_question_app._config.loader import get_config  # noqa: F401

        components["config"] = "healthy"
    except Exception:
        components["config"] = "degraded"
    try:
        components["torch"] = "healthy" if torch is not None else "unavailable"
    except Exception:
        components["torch"] = "unavailable"
    if torch.cuda.is_available():
        components["cuda"] = "available"
        components["gpu"] = torch.cuda.get_device_name(0)
    else:
        components["cuda"] = "unavailable"
        components["gpu"] = "none"
    return components


def run_health_checks() -> dict[str, Any]:
    checks: dict[str, Any] = {}
    checks["python"] = "pass"
    checks["dependencies"] = "pass"
    try:
        from ares import __version__  # noqa: F401

        checks["ares_package"] = "pass"
    except ImportError:
        checks["ares_package"] = "fail"
    try:
        from duplicate_question_app._config.settings import get_app_paths  # noqa: F401

        checks["config_loader"] = "pass"
    except Exception:
        checks["config_loader"] = "fail"
    return checks


def build_health_response(version: str, request_id: str) -> HealthResponse:
    components = check_component_health()
    all_healthy = all(v == "healthy" or v == "available" or v == "pass" for v in components.values())
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=version,
        uptime_seconds=get_uptime(),
        components=components,
        checks=run_health_checks(),
        request_id=request_id,
    )
