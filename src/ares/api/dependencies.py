from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Request, status

from ares.api.config import APIConfig, Settings
from ares.api.exceptions import AuthenticationError, AuthorizationError
from ares.api.models import UserRole
from ares.api.rate_limit import RateLimiter
from ares.api.security import SecurityManager

logger = logging.getLogger(__name__)


_security_manager: SecurityManager | None = None
_rate_limiter: RateLimiter | None = None


def get_config() -> Settings:
    """Return the current API configuration settings singleton.

    Returns:
        The active :class:`ares.api.config.Settings` instance.
    """
    return APIConfig.get()


def get_security_manager() -> SecurityManager:
    """Return a singleton :class:`SecurityManager` instance.

    The security manager is lazily initialised on first access and reused
    for the lifetime of the process.

    Returns:
        The shared SecurityManager instance.
    """
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def get_rate_limiter() -> RateLimiter:
    """Return a singleton :class:`RateLimiter` instance.

    The rate limiter is lazily initialised on first access and reused
    for the lifetime of the process.

    Returns:
        The shared RateLimiter instance.
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def get_token_data(
    request: Request,
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None),
) -> dict[str, Any]:
    """Extract and validate authentication token data from the request.

    Supports Bearer token (via the ``Authorization`` header) and API key
    (via the ``X-API-Key`` header). At least one credential must be
    provided.

    Args:
        request: The incoming HTTP request.
        authorization: The ``Authorization`` header value.
        x_api_key: The ``X-API-Key`` header value.

    Returns:
        A dictionary of token claims extracted from the valid credential.

    Raises:
        HTTPException: 401 if authentication fails.
    """
    sm = get_security_manager()
    try:
        if authorization:
            scheme, _, token = authorization.partition(" ")
            if scheme.lower() != "bearer":
                raise AuthenticationError("Invalid authorization scheme")
            return sm.authenticate_request(authorization=token)
        if x_api_key:
            return sm.authenticate_request(api_key=x_api_key)
        raise AuthenticationError("No authentication credentials provided")
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


async def require_admin(
    token: Annotated[dict[str, Any], Depends(get_token_data)],
) -> dict[str, Any]:
    """Dependency that ensures the authenticated user has the admin role.

    Args:
        token: The token data obtained from :func:`get_token_data`.

    Returns:
        The validated token data.

    Raises:
        HTTPException: 403 if the user is not an admin.
    """
    sm = get_security_manager()
    try:
        sm.check_role(token, UserRole.ADMIN)
        return token
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


async def require_user(
    token: Annotated[dict[str, Any], Depends(get_token_data)],
) -> dict[str, Any]:
    """Dependency that ensures the authenticated user has at least the user role.

    Args:
        token: The token data obtained from :func:`get_token_data`.

    Returns:
        The validated token data.

    Raises:
        HTTPException: 403 if the user lacks the required role.
    """
    sm = get_security_manager()
    try:
        sm.check_role(token, UserRole.USER)
        return token
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


async def apply_rate_limit(
    request: Request,
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Dependency that enforces rate limiting based on the client IP.

    Args:
        request: The incoming HTTP request.
        rate_limiter: The RateLimiter instance.

    Raises:
        HTTPException: 429 if the rate limit is exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(client_ip)


async def get_request_id(request: Request) -> str:
    """Extract the request ID from the request state.

    Args:
        request: The incoming HTTP request.

    Returns:
        The request ID string, or ``"unknown"`` if not set.
    """
    return request.state.request_id if hasattr(request.state, "request_id") else "unknown"
