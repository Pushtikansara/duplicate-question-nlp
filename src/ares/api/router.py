from __future__ import annotations

from fastapi import APIRouter

from ares.api.routers.ares_demo import router as ares_demo_router
from ares.api.routers.benchmark import router as benchmark_router
from ares.api.routers.config import router as config_router
from ares.api.routers.health import router as health_router
from ares.api.routers.memory import router as memory_router
from ares.api.routers.metrics import router as metrics_router
from ares.api.routers.pipeline import router as pipeline_router
from ares.api.routers.plugins import router as plugins_router
from ares.api.routers.predict import router as predict_router
from ares.api.routers.profile import router as profile_router
from ares.api.routers.reason import router as reason_router
from ares.api.routers.reflection import router as reflection_router
from ares.api.routers.system import router as system_router
from ares.api.routers.trace import router as trace_router
from ares.api.routers.version import router as version_router

api_router = APIRouter()
"""Top-level API router that aggregates all domain-specific sub-routers."""

api_router.include_router(version_router, tags=["Version"])
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(predict_router, tags=["Predict"])
api_router.include_router(pipeline_router, tags=["Pipeline"])
api_router.include_router(reason_router, tags=["Reason"])
api_router.include_router(memory_router, tags=["Memory"])
api_router.include_router(plugins_router, tags=["Plugins"])
api_router.include_router(reflection_router, tags=["Reflection"])
api_router.include_router(benchmark_router, tags=["Benchmark"])
api_router.include_router(config_router, tags=["Config"])
api_router.include_router(metrics_router, tags=["Metrics"])
api_router.include_router(trace_router, tags=["Trace"])
api_router.include_router(profile_router, tags=["Profile"])
api_router.include_router(system_router, tags=["System"])
api_router.include_router(ares_demo_router, tags=["ARES Demo"])

from ares.api.routers.auth import router as auth_router

auth_router = auth_router
"""Standalone router for authentication and authorisation endpoints."""
