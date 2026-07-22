from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from ares.api.config import Settings
from ares.api.exceptions import AuthenticationError
from ares.api.models import UserRole

logger = logging.getLogger(__name__)


class JWTManager:
    def __init__(self, config: Settings) -> None:
        self._config = config
        self._secret_key = config.secret_key
        self._algorithm = config.jwt_algorithm
        self._access_expire = config.jwt_access_token_expire_minutes
        self._refresh_expire = config.jwt_refresh_token_expire_days

    def create_access_token(
        self,
        subject: str,
        role: UserRole = UserRole.USER,
        permissions: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=self._access_expire)
        now = datetime.now(timezone.utc)
        claims = {
            "sub": subject,
            "role": role.value,
            "permissions": permissions or [],
            "iat": now,
            "exp": now + expires_delta,
            "type": "access",
        }
        return str(jwt.encode(claims, self._secret_key, algorithm=self._algorithm))

    def create_refresh_token(
        self,
        subject: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(days=self._refresh_expire)
        now = datetime.now(timezone.utc)
        claims = {
            "sub": subject,
            "iat": now,
            "exp": now + expires_delta,
            "type": "refresh",
        }
        return str(jwt.encode(claims, self._secret_key, algorithm=self._algorithm))

    def verify_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            return dict(payload)
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {e}") from e

    def decode_token(self, token: str) -> dict[str, Any]:
        return self.verify_token(token)

    def refresh_access_token(self, refresh_token: str) -> str:
        payload = self.verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type: expected refresh token")
        subject = payload.get("sub", "")
        return self.create_access_token(subject)
