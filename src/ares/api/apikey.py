from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from ares.api.models import UserRole

logger = logging.getLogger(__name__)


class StoredKey:
    def __init__(
        self,
        key_hash: str,
        prefix: str,
        client_id: str,
        role: str,
        permissions: list[str],
        created_at: datetime,
        expires_at: datetime | None = None,
        revoked: bool = False,
    ) -> None:
        self.key_hash = key_hash
        self.prefix = prefix
        self.client_id = client_id
        self.role = role
        self.permissions = permissions
        self.created_at = created_at
        self.expires_at = expires_at
        self.revoked = revoked


class APIKeyManager:
    def __init__(self) -> None:
        self._keys: dict[str, StoredKey] = {}

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    def _generate_key(self) -> tuple[str, str, str]:
        prefix = "ares_" + secrets.token_hex(4)
        secret = secrets.token_hex(32)
        full_key = f"{prefix}.{secret}"
        return full_key, prefix, self._hash_key(full_key)

    def create_key(
        self,
        client_id: str,
        role: UserRole = UserRole.USER,
        permissions: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> str:
        full_key, prefix, key_hash = self._generate_key()
        now = datetime.now(timezone.utc)
        self._keys[prefix] = StoredKey(
            key_hash=key_hash,
            prefix=prefix,
            client_id=client_id,
            role=role.value,
            permissions=permissions or [],
            created_at=now,
            expires_at=expires_at,
        )
        return full_key

    def verify_key(self, api_key: str) -> dict[str, Any] | None:
        try:
            prefix = api_key.split(".")[0]
        except (IndexError, AttributeError):
            return None
        stored = self._keys.get(prefix)
        if stored is None:
            return None
        if stored.revoked:
            return None
        if stored.expires_at and stored.expires_at < datetime.now(timezone.utc):
            return None
        if stored.key_hash != self._hash_key(api_key):
            return None
        return {
            "client_id": stored.client_id,
            "role": stored.role,
            "permissions": stored.permissions,
        }

    def revoke_key(self, key_prefix: str) -> bool:
        stored = self._keys.get(key_prefix)
        if stored is None:
            return False
        stored.revoked = True
        return True

    def list_keys(self) -> list[dict[str, Any]]:
        return [
            {
                "prefix": k.prefix,
                "client_id": k.client_id,
                "role": k.role,
                "created_at": k.created_at.isoformat(),
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "revoked": k.revoked,
            }
            for k in self._keys.values()
        ]
