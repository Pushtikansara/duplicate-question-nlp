from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from ares.api.lifespan import lifespan
from ares.api.middleware import setup_middleware
from ares.api.openapi import custom_openapi, tags_metadata
from ares.api.router import api_router, auth_router
from ares.api.telemetry import get_telemetry

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the ARES FastAPI application.

    Builds the application with OpenAPI metadata, custom OpenAPI schema,
    middleware stack, and registered route groups. Telemetry initialisation
    is logged but does not block startup.

    Returns:
        Fully configured FastAPI application instance.
    """
    app = FastAPI(
        title="ARES API",
        version="1.0.0",
        summary="ARES - Advanced Reasoning Engine for Semantic Understanding",
        description="Enterprise-grade REST API for semantic duplicate question detection.",
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        openapi_tags=tags_metadata,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.openapi = custom_openapi(app)
    setup_middleware(app)
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    telemetry = get_telemetry()
    if telemetry.enabled:
        logger.info("Telemetry enabled for ARES API")
    else:
        logger.info("Telemetry disabled for ARES API")
    return app


app = create_app()
