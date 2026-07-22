from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ares.api.logging import setup_api_logging
from ares.api.telemetry import get_telemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info("ARES API starting up...")
    setup_api_logging()
    telemetry = get_telemetry()
    if telemetry.enabled:
        logger.info("OpenTelemetry enabled")
    logger.info("ARES API startup complete")
    yield
    logger.info("ARES API shutting down...")
    logger.info("ARES API shutdown complete")
