from __future__ import annotations

from typing import Any

from ares.api.models import ErrorResponse, PaginatedResponse


def success_response(
    data: Any,
    request_id: str = "",
    status_code: int = 200,
) -> dict[str, Any]:
    """Build a standard success response envelope.

    Args:
        data: The response payload.
        request_id: Unique identifier for the request.
        status_code: HTTP status code for the response.

    Returns:
        Dictionary with ``success``, ``data``, ``request_id``, and
        ``status_code`` keys.
    """
    return {
        "success": True,
        "data": data,
        "request_id": request_id,
        "status_code": status_code,
    }


def error_response(
    detail: str,
    error_code: str = "INTERNAL_ERROR",
    status_code: int = 500,
    request_id: str = "",
    errors: list[dict[str, Any]] | None = None,
) -> ErrorResponse:
    """Build a standard error response.

    Args:
        detail: Human-readable error description.
        error_code: Machine-readable error identifier.
        status_code: HTTP status code.
        request_id: Unique identifier for the request.
        errors: Optional list of per-field error details.

    Returns:
        An ``ErrorResponse`` instance.
    """
    return ErrorResponse(
        detail=detail,
        error_code=error_code,
        status_code=status_code,
        request_id=request_id,
        errors=errors,
    )


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    request_id: str = "",
) -> PaginatedResponse:
    """Build a paginated response envelope.

    Args:
        items: The items for the current page.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        request_id: Unique identifier for the request.

    Returns:
        A ``PaginatedResponse`` instance with computed pagination metadata.
    """
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
        request_id=request_id,
    )
