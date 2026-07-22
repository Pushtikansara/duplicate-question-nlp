from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ares.api.config import APIConfig
from ares.api.exceptions import ARESAPIError

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that attaches a unique request ID to every request and response.

    Reads the ``X-Request-ID`` header from the incoming request if present,
    otherwise generates a new UUID. The ID is stored on ``request.state`` and
    echoed back in the response headers.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware that records the processing time for each request.

    Adds an ``X-Processing-Time-Ms`` response header containing the elapsed
    time in milliseconds with two decimal places.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.time()
        response = await call_next(request)
        elapsed_ms = (time.time() - start) * 1000
        response.headers["X-Processing-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that applies security-related HTTP response headers.

    Sets ``X-Content-Type-Options``, ``X-Frame-Options``,
    ``X-XSS-Protection``, ``Strict-Transport-Security``, and
    ``Cache-Control`` to recommended safe defaults.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        return response


def setup_middleware(app: FastAPI) -> None:
    """Register all API middleware on the given FastAPI application.

    Middleware is applied in order: CORS, GZip, request ID, timing, and
    security headers. CORS origins are read from the active
    :class:`ares.api.config.APIConfig`.

    Args:
        app: The FastAPI application instance.
    """
    config = APIConfig.get()

    @app.exception_handler(ARESAPIError)
    async def aresapi_error_handler(request: Request, exc: ARESAPIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": exc.error_code,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR",
            },
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
