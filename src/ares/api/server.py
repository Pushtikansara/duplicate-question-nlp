from __future__ import annotations

import logging
import signal
import sys

import uvicorn

from ares.api.config import APIConfig

logger = logging.getLogger(__name__)


def run_server(
    host: str | None = None,
    port: int | None = None,
    workers: int | None = None,
    reload: bool | None = None,
    log_level: str | None = None,
) -> None:
    """Launch the ARES API server via Uvicorn.

    Args:
        host: Bind address. Falls back to ``APIConfig.host`` when ``None``.
        port: Bind port. Falls back to ``APIConfig.port`` when ``None``.
        workers: Number of worker processes. Falls back to ``APIConfig.workers``
            when ``None``.
        reload: Enable hot-reload. Falls back to ``APIConfig.reload`` when
            ``None``.
        log_level: Uvicorn log level. Falls back to ``APIConfig.log_level``
            when ``None``.
    """
    config = APIConfig.get()
    host = host or config.host
    port = port or config.port
    workers = workers or config.workers
    reload = reload if reload is not None else config.reload
    log_level = log_level or config.log_level
    logger.info(
        "Starting ARES API server on %s:%s (workers=%s, reload=%s)",
        host,
        port,
        workers,
        reload,
    )
    uvicorn.run(
        "ares.api.app:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        log_level=log_level,
        access_log=True,
        timeout_keep_alive=30,
    )


def run_production() -> None:
    """Start the server in production mode using configured defaults."""
    config = APIConfig.get()
    run_server(
        host=config.host,
        port=config.port,
        workers=config.workers,
        log_level="info",
    )


def handle_signal(sig: int, frame: object) -> None:
    """Gracefully shut down on receipt of a termination signal.

    Args:
        sig: Signal number.
        frame: Current stack frame (unused).
    """
    logger.info("Received signal %s, shutting down...", sig)
    sys.exit(0)


def main() -> None:
    """Entry point for the ARES API server.

    Registers signal handlers for SIGINT and SIGTERM, then starts Uvicorn
    with configuration sourced from :class:`ares.api.config.APIConfig`.
    """
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    run_server()
