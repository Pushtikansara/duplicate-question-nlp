from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ares.api.config import APIConfig
from ares.api.exceptions import RateLimitError
from ares.api.rate_limit import RateLimiter


@pytest.mark.security
class TestRateLimiter:
    def test_rate_limiter_initializes(self):
        limiter = RateLimiter()
        assert limiter is not None

    def test_check_within_limit_returns_allowed(self):
        with patch.object(APIConfig, "get") as mock_get:
            settings = MagicMock()
            settings.rate_limit_enabled = True
            settings.rate_limit_requests = 100
            settings.rate_limit_window_seconds = 60
            settings.rate_limit_burst = 100
            mock_get.return_value = settings
            limiter = RateLimiter()
            result = limiter.check("test-key")
            assert result["allowed"] is True

    def test_check_returns_remaining_count(self):
        with patch.object(APIConfig, "get") as mock_get:
            settings = MagicMock()
            settings.rate_limit_enabled = True
            settings.rate_limit_requests = 100
            settings.rate_limit_window_seconds = 60
            settings.rate_limit_burst = 100
            mock_get.return_value = settings
            limiter = RateLimiter()
            result = limiter.check("test-key")
            assert "remaining" in result
            assert isinstance(result["remaining"], int)

    def test_check_returns_reset_time(self):
        with patch.object(APIConfig, "get") as mock_get:
            settings = MagicMock()
            settings.rate_limit_enabled = True
            settings.rate_limit_burst = 100
            settings.rate_limit_window_seconds = 60
            settings.rate_limit_requests = 100
            mock_get.return_value = settings
            limiter = RateLimiter()
            result = limiter.check("test-key")
            assert "reset" in result
            assert isinstance(result["reset"], int)

    def test_multiple_requests_decrease_remaining(self):
        with patch.object(APIConfig, "get") as mock_get:
            settings = MagicMock()
            settings.rate_limit_enabled = True
            settings.rate_limit_requests = 100
            settings.rate_limit_window_seconds = 60
            settings.rate_limit_burst = 100
            mock_get.return_value = settings
            limiter = RateLimiter()
            r1 = limiter.check("key-1")
            r2 = limiter.check("key-1")
            assert r2["remaining"] < r1["remaining"]

    def test_different_keys_have_independent_counts(self):
        with patch.object(APIConfig, "get") as mock_get:
            settings = MagicMock()
            settings.rate_limit_enabled = True
            settings.rate_limit_requests = 100
            settings.rate_limit_window_seconds = 60
            settings.rate_limit_burst = 100
            mock_get.return_value = settings
            limiter = RateLimiter()
            r1 = limiter.check("key-a")
            r2 = limiter.check("key-b")
            assert r1["remaining"] == r2["remaining"]

    @patch.object(APIConfig, "get")
    def test_check_exceeding_burst_raises_error(self, mock_get):
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.rate_limit_requests = 100
        mock_settings.rate_limit_window_seconds = 60
        mock_settings.rate_limit_burst = 2
        mock_get.return_value = mock_settings

        limiter = RateLimiter()
        limiter.check("burst-key")
        limiter.check("burst-key")
        with pytest.raises(RateLimitError):
            limiter.check("burst-key")

    def test_rate_limit_disabled_allows_all(self):
        with patch.object(APIConfig, "get") as mock_get:
            mock_settings = MagicMock()
            mock_settings.rate_limit_enabled = False
            mock_settings.rate_limit_requests = 100
            mock_settings.rate_limit_window_seconds = 60
            mock_settings.rate_limit_burst = 5
            mock_get.return_value = mock_settings

            limiter = RateLimiter()
            for _ in range(100):
                result = limiter.check("unlimited-key")
                assert result["allowed"] is True

    def test_get_remaining_returns_count(self):
        with patch.object(APIConfig, "get") as mock_get:
            settings = MagicMock()
            settings.rate_limit_enabled = True
            settings.rate_limit_requests = 100
            settings.rate_limit_window_seconds = 60
            settings.rate_limit_burst = 100
            mock_get.return_value = settings
            limiter = RateLimiter()
            remaining = limiter.get_remaining("some-key")
            assert isinstance(remaining, int)
            assert remaining >= 0

    def test_get_remaining_decreases_after_requests(self):
        with patch.object(APIConfig, "get") as mock_get:
            settings = MagicMock()
            settings.rate_limit_enabled = True
            settings.rate_limit_requests = 100
            settings.rate_limit_window_seconds = 60
            settings.rate_limit_burst = 100
            mock_get.return_value = settings
            limiter = RateLimiter()
            before = limiter.get_remaining("count-key")
            limiter.check("count-key")
            after = limiter.get_remaining("count-key")
            assert after == before - 1

    def test_rate_limit_error_has_detail(self):
        with patch.object(APIConfig, "get") as mock_get:
            mock_settings = MagicMock()
            mock_settings.rate_limit_enabled = True
            mock_settings.rate_limit_requests = 100
            mock_settings.rate_limit_window_seconds = 60
            mock_settings.rate_limit_burst = 1
            mock_get.return_value = mock_settings

            limiter = RateLimiter()
            limiter.check("error-key")
            with pytest.raises(RateLimitError) as exc_info:
                limiter.check("error-key")
            assert "Rate limit exceeded" in str(exc_info.value)


@pytest.mark.security
class TestRateLimitAPI:
    def test_rate_limited_endpoint_returns_200_within_limit(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_predict_response_has_request_id(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=auth_headers,
        )
        data = response.json()
        assert "request_id" in data
        assert isinstance(data["request_id"], str)
