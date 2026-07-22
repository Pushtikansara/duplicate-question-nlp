from __future__ import annotations


class ARESClientError(Exception):
    pass


class AuthenticationError(ARESClientError):
    pass


class APIError(ARESClientError):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class ConnectionError(ARESClientError):
    pass


class TimeoutError(ARESClientError):
    pass


class RateLimitError(ARESClientError):
    pass


class NotFoundError(ARESClientError):
    pass


class ValidationError(ARESClientError):
    pass
