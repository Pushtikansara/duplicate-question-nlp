from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from ares.api.apikey import APIKeyManager as _APIKeyManager
from ares.api.config import APIConfig
from ares.api.exceptions import AuthenticationError, AuthorizationError
from ares.api.jwt import JWTManager as _JWTManager
from ares.api.models import UserRole

logger = logging.getLogger(__name__)

APIKeyManager = _APIKeyManager
JWTManager = _JWTManager


class SecurityManager:
    def __init__(self) -> None:
        self.config = APIConfig.get()
        self.jwt = _JWTManager(self.config)
        self.apikey = _APIKeyManager(storage_path=self.config.data_dir)

    def authenticate_request(
        self,
        authorization: str | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        token_data: dict[str, Any] | None = None
        if authorization:
            token_data = self.jwt.verify_token(authorization)
        elif api_key:
            key_data = self.apikey.verify_key(api_key)
            if key_data:
                token_data = {
                    "sub": key_data.get("client_id", "api-key-user"),
                    "role": key_data.get("role", UserRole.USER.value),
                    "permissions": key_data.get("permissions", []),
                }
        if token_data is None:
            raise AuthenticationError("No valid authentication credentials provided")
        return token_data

    def check_role(self, token_data: dict[str, Any], required_role: UserRole) -> None:
        user_role_str = token_data.get("role", UserRole.READER.value)
        try:
            user_role = UserRole(user_role_str)
        except ValueError as e:
            raise AuthorizationError(f"Invalid user role: {user_role_str}") from e
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.USER: 2,
            UserRole.READER: 1,
        }
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise AuthorizationError(f"Role '{user_role.value}' insufficient for required role '{required_role.value}'")

    def create_access_token(
        self,
        subject: str,
        role: UserRole = UserRole.USER,
        permissions: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        return self.jwt.create_access_token(subject, role, permissions, expires_delta)

    def create_refresh_token(
        self,
        subject: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        return self.jwt.create_refresh_token(subject, expires_delta)

    def create_api_key(
        self,
        client_id: str,
        role: UserRole = UserRole.USER,
        permissions: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> str:
        return self.apikey.create_key(client_id, role, permissions, expires_at)

    def revoke_api_key(self, key_prefix: str) -> bool:
        return self.apikey.revoke_key(key_prefix)

    def list_api_keys(self) -> list[dict[str, Any]]:
        return self.apikey.list_keys()
