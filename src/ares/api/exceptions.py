from __future__ import annotations


class ARESAPIError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        detail: str | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        super().__init__(self.detail)


class AuthenticationError(ARESAPIError):
    status_code = 401
    detail = "Not authenticated"
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(ARESAPIError):
    status_code = 403
    detail = "Permission denied"
    error_code = "AUTHORIZATION_ERROR"


class RateLimitError(ARESAPIError):
    status_code = 429
    detail = "Rate limit exceeded"
    error_code = "RATE_LIMIT_ERROR"


class ModelNotFoundError(ARESAPIError):
    status_code = 404
    detail = "Model not found"
    error_code = "MODEL_NOT_FOUND"


class ValidationError(ARESAPIError):
    status_code = 422
    detail = "Validation error"
    error_code = "VALIDATION_ERROR"


class ResourceNotFoundError(ARESAPIError):
    status_code = 404
    detail = "Resource not found"
    error_code = "RESOURCE_NOT_FOUND"


class ConflictError(ARESAPIError):
    status_code = 409
    detail = "Resource conflict"
    error_code = "CONFLICT_ERROR"


class ServiceUnavailableError(ARESAPIError):
    status_code = 503
    detail = "Service temporarily unavailable"
    error_code = "SERVICE_UNAVAILABLE"
