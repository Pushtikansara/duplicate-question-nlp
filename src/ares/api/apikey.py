from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
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
    def __init__(self, storage_path: str = "") -> None:
        self._keys: dict[str, StoredKey] = {}
        self._storage_path = storage_path
        if storage_path:
            self._load()

    def _storage_file(self) -> str:
        return os.path.join(self._storage_path, "api_keys.json")

    def _load(self) -> None:
        path = self._storage_file()
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = json.load(f)
            for item in data:
                created = datetime.fromisoformat(item["created_at"])
                expires = datetime.fromisoformat(item["expires_at"]) if item.get("expires_at") else None
                self._keys[item["prefix"]] = StoredKey(
                    key_hash=item["key_hash"],
                    prefix=item["prefix"],
                    client_id=item["client_id"],
                    role=item["role"],
                    permissions=item.get("permissions", []),
                    created_at=created,
                    expires_at=expires,
                    revoked=item.get("revoked", False),
                )
            logger.info("Loaded %d API keys from %s", len(self._keys), path)
        except Exception:
            logger.exception("Failed to load API keys from %s", path)

    def _save(self) -> None:
        if not self._storage_path:
            return
        path = self._storage_file()
        try:
            Path(self._storage_path).mkdir(parents=True, exist_ok=True)
            data = [
                {
                    "key_hash": k.key_hash,
                    "prefix": k.prefix,
                    "client_id": k.client_id,
                    "role": k.role,
                    "permissions": k.permissions,
                    "created_at": k.created_at.isoformat(),
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                    "revoked": k.revoked,
                }
                for k in self._keys.values()
            ]
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            logger.exception("Failed to save API keys to %s", path)

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
        self._save()
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
        self._save()
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
