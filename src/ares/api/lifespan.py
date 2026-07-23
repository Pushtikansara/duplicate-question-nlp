from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ares.api.config import APIConfig
from ares.api.logging import setup_api_logging
from ares.api.telemetry import get_telemetry

logger = logging.getLogger(__name__)


def _validate_config() -> None:
    config = APIConfig.get()

    if not config.secret_key:
        raise RuntimeError(
            "ARES_SECRET_KEY is not set. "
            "Generate a strong secret key (e.g. 'openssl rand -hex 32') "
            "and set it via the ARES_SECRET_KEY environment variable."
        )
    if len(config.secret_key) < 16:
        logger.warning("ARES_SECRET_KEY is too short (minimum 16 characters recommended)")

    if config.cors_origins == ["*"]:
        logger.info("CORS configured with wildcard origin — credentials disabled")

    if config.data_dir:
        os.makedirs(config.data_dir, exist_ok=True)
        logger.info("Data directory ensured: %s", config.data_dir)

    if config.upload_dir:
        os.makedirs(config.upload_dir, exist_ok=True)
        logger.info("Upload directory ensured: %s", config.upload_dir)

    if config.log_level not in ("debug", "info", "warning", "error", "critical"):
        logger.warning("Unrecognized log level: %s", config.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info("ARES API starting up...")
    setup_api_logging()
    _validate_config()

    telemetry = get_telemetry()
    if telemetry.enabled:
        logger.info("OpenTelemetry enabled")
    logger.info("ARES API startup complete")
    yield
    logger.info("ARES API shutting down...")
    logger.info("ARES API shutdown complete")
