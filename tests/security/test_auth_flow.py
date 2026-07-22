from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ares.api.apikey import APIKeyManager
from ares.api.config import APIConfig
from ares.api.exceptions import AuthenticationError, AuthorizationError
from ares.api.jwt import JWTManager
from ares.api.models import UserRole
from ares.api.security import SecurityManager


@pytest.mark.security
class TestAPIKeyCreation:
    def test_create_api_key_returns_string(self):
        manager = SecurityManager()
        key = manager.create_api_key("test-client", UserRole.USER)
        assert isinstance(key, str)
        assert key.startswith("ares_")

    def test_create_api_key_starts_with_prefix(self):
        manager = APIKeyManager()
        key = manager.create_key("client-1", UserRole.ADMIN)
        assert key.startswith("ares_")

    def test_create_api_key_contains_dot(self):
        manager = APIKeyManager()
        key = manager.create_key("client-1")
        assert "." in key

    def test_create_api_key_with_expiry(self):
        manager = APIKeyManager()
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        key = manager.create_key("client-1", expires_at=expires)
        assert key is not None

    def test_create_api_key_with_permissions(self):
        manager = APIKeyManager()
        key = manager.create_key("client-1", permissions=["read", "write"])
        assert key is not None

    def test_create_api_key_admin_role(self):
        manager = APIKeyManager()
        key = manager.create_key("admin-client", role=UserRole.ADMIN)
        assert key is not None

    def test_create_multiple_keys_unique(self):
        manager = APIKeyManager()
        key1 = manager.create_key("client-1")
        key2 = manager.create_key("client-2")
        assert key1 != key2


@pytest.mark.security
class TestAPIKeyVerification:
    def test_verify_valid_api_key_returns_data(self):
        manager = SecurityManager()
        api_key = manager.create_api_key("test-client", UserRole.USER)
        result = manager.authenticate_request(api_key=api_key)
        assert result is not None
        assert "sub" in result
        assert "role" in result

    def test_verify_api_key_returns_correct_role(self):
        manager = SecurityManager()
        api_key = manager.create_api_key("admin-client", UserRole.ADMIN)
        result = manager.authenticate_request(api_key=api_key)
        assert result["role"] == UserRole.ADMIN.value

    def test_verify_api_key_returns_client_id(self):
        manager = APIKeyManager()
        api_key = manager.create_key("my-client")
        result = manager.verify_key(api_key)
        assert result["client_id"] == "my-client"

    def test_verify_invalid_api_key_returns_none(self):
        manager = APIKeyManager()
        result = manager.verify_key("ares_invalid.1234567890abcdef1234567890abcdef")
        assert result is None

    def test_verify_empty_api_key_returns_none(self):
        manager = APIKeyManager()
        result = manager.verify_key("")
        assert result is None

    def test_verify_malformed_api_key_returns_none(self):
        manager = APIKeyManager()
        result = manager.verify_key("no-dot-format")
        assert result is None


@pytest.mark.security
class TestAPIKeyRevocation:
    def test_revoke_api_key_returns_true(self):
        manager = APIKeyManager()
        key = manager.create_key("client-1")
        prefix = key.split(".")[0]
        assert manager.revoke_key(prefix) is True

    def test_revoked_key_fails_verification(self):
        manager = APIKeyManager()
        key = manager.create_key("client-1")
        prefix = key.split(".")[0]
        manager.revoke_key(prefix)
        result = manager.verify_key(key)
        assert result is None

    def test_revoke_nonexistent_key_returns_false(self):
        manager = APIKeyManager()
        assert manager.revoke_key("nonexistent") is False

    def test_revoked_key_listed_as_revoked(self):
        manager = APIKeyManager()
        key = manager.create_key("client-1")
        prefix = key.split(".")[0]
        manager.revoke_key(prefix)
        keys = manager.list_keys()
        assert any(k["prefix"] == prefix and k["revoked"] for k in keys)


@pytest.mark.security
class TestJWTTokenCreation:
    def test_create_access_token_returns_string(self):
        manager = SecurityManager()
        token = manager.create_access_token("user1", UserRole.USER)
        assert isinstance(token, str)

    def test_create_access_token_with_admin_role(self):
        manager = SecurityManager()
        token = manager.create_access_token("admin1", UserRole.ADMIN)
        assert isinstance(token, str)

    def test_create_refresh_token_returns_string(self):
        manager = SecurityManager()
        token = manager.create_refresh_token("user1")
        assert isinstance(token, str)

    def test_access_and_refresh_tokens_differ(self):
        manager = SecurityManager()
        access = manager.create_access_token("user1", UserRole.USER)
        refresh = manager.create_refresh_token("user1")
        assert access != refresh


@pytest.mark.security
class TestJWTTokenVerification:
    def test_verify_valid_token_returns_payload(self):
        manager = SecurityManager()
        token = manager.create_access_token("user1", UserRole.USER)
        result = manager.authenticate_request(authorization=token)
        assert result is not None
        assert result["sub"] == "user1"
        assert result["role"] == UserRole.USER.value

    def test_verify_token_with_admin_role(self):
        manager = SecurityManager()
        token = manager.create_access_token("admin1", UserRole.ADMIN)
        result = manager.authenticate_request(authorization=token)
        assert result["role"] == UserRole.ADMIN.value

    def test_verify_token_with_permissions(self):
        manager = SecurityManager()
        token = manager.create_access_token("user1", UserRole.USER, permissions=["read"])
        result = manager.authenticate_request(authorization=token)
        assert "permissions" in result

    def test_verify_expired_token_raises_error(self):
        from ares.api.jwt import JWTManager

        config = APIConfig.get()
        jwt_manager = JWTManager(config)
        token = jwt_manager.create_access_token("user1", expires_delta=timedelta(seconds=-1))
        with pytest.raises(AuthenticationError):
            jwt_manager.verify_token(token)

    def test_verify_malformed_token_raises_error(self):
        manager = SecurityManager()
        with pytest.raises(AuthenticationError):
            manager.authenticate_request(authorization="this-is-not-a-valid-token")

    def test_refresh_token_creates_new_access(self):
        jwt_manager = JWTManager(APIConfig.get())
        refresh = jwt_manager.create_refresh_token("user1")
        new_access = jwt_manager.refresh_access_token(refresh)
        assert isinstance(new_access, str)
        assert len(new_access) > 0

    def test_verify_refresh_token_type(self):
        jwt_manager = JWTManager(APIConfig.get())
        refresh = jwt_manager.create_refresh_token("user1")
        payload = jwt_manager.verify_token(refresh)
        assert payload["type"] == "refresh"


@pytest.mark.security
class TestRoleBasedAccessControl:
    def test_admin_role_hierarchy(self):
        manager = SecurityManager()
        token_data = {"sub": "admin", "role": UserRole.ADMIN.value}
        manager.check_role(token_data, UserRole.ADMIN)
        manager.check_role(token_data, UserRole.USER)
        manager.check_role(token_data, UserRole.READER)

    def test_user_role_cannot_access_admin(self):
        manager = SecurityManager()
        token_data = {"sub": "user", "role": UserRole.USER.value}
        with pytest.raises(AuthorizationError):
            manager.check_role(token_data, UserRole.ADMIN)

    def test_user_role_can_access_user(self):
        manager = SecurityManager()
        token_data = {"sub": "user", "role": UserRole.USER.value}
        manager.check_role(token_data, UserRole.USER)

    def test_reader_role_cannot_access_user(self):
        manager = SecurityManager()
        token_data = {"sub": "reader", "role": UserRole.READER.value}
        with pytest.raises(AuthorizationError):
            manager.check_role(token_data, UserRole.USER)

    def test_reader_role_cannot_access_admin(self):
        manager = SecurityManager()
        token_data = {"sub": "reader", "role": UserRole.READER.value}
        with pytest.raises(AuthorizationError):
            manager.check_role(token_data, UserRole.ADMIN)

    def test_reader_role_can_access_reader(self):
        manager = SecurityManager()
        token_data = {"sub": "reader", "role": UserRole.READER.value}
        manager.check_role(token_data, UserRole.READER)

    def test_invalid_role_raises_error(self):
        manager = SecurityManager()
        token_data = {"sub": "unknown", "role": "superuser"}
        with pytest.raises(AuthorizationError):
            manager.check_role(token_data, UserRole.USER)


@pytest.mark.security
class TestAPIKeyListing:
    def test_list_keys_returns_list(self):
        manager = APIKeyManager()
        keys = manager.list_keys()
        assert isinstance(keys, list)

    def test_list_keys_includes_created_keys(self):
        manager = APIKeyManager()
        manager.create_key("client-1")
        keys = manager.list_keys()
        assert len(keys) >= 1
        assert any(k["client_id"] == "client-1" for k in keys)

    def test_list_keys_contains_expected_fields(self):
        manager = APIKeyManager()
        manager.create_key("client-1", UserRole.ADMIN)
        keys = manager.list_keys()
        key = keys[0]
        assert "prefix" in key
        assert "client_id" in key
        assert "role" in key
        assert "created_at" in key
        assert "revoked" in key
