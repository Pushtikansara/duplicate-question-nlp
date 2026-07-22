from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> dict[str, Any]:
    if app.openapi_schema:
        return cast("dict[str, Any]", app.openapi_schema)
    openapi_schema = get_openapi(
        title="ARES API",
        version="1.0.0",
        summary="ARES - Advanced Reasoning Engine for Semantic Understanding",
        description=(
            "Enterprise-grade REST API for semantic duplicate question detection. "
            "Supports single/batch/streaming inference, cognitive pipeline execution, "
            "memory management, plugin orchestration, and comprehensive observability."
        ),
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://ares.ai/logo.png",
        "altText": "ARES Logo",
    }
    app.openapi_schema = openapi_schema
    return cast("dict[str, Any]", app.openapi_schema)


tags_metadata = [
    {"name": "Version", "description": "API version information"},
    {"name": "Health", "description": "Health check endpoints"},
    {"name": "Predict", "description": "Inference endpoints for duplicate question detection"},
    {"name": "Pipeline", "description": "Cognitive pipeline execution"},
    {"name": "Reason", "description": "Reasoning engine with trace and evidence"},
    {"name": "Memory", "description": "Memory management and retrieval"},
    {"name": "Plugins", "description": "Plugin lifecycle management"},
    {"name": "Reflection", "description": "Trust scoring and confidence auditing"},
    {"name": "Benchmark", "description": "Benchmark execution and comparison"},
    {"name": "Config", "description": "Configuration management"},
    {"name": "Metrics", "description": "Prometheus metrics and observability"},
    {"name": "Trace", "description": "Decision tracing"},
    {"name": "Profile", "description": "Performance profiling"},
    {"name": "System", "description": "System information and diagnostics"},
    {"name": "Auth", "description": "Authentication and authorization"},
]
