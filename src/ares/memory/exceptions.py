from __future__ import annotations

from ares.api.exceptions import ARESAPIError


class MemoryError(ARESAPIError):
    status_code = 500
    detail = "Memory error"
    error_code = "MEMORY_ERROR"


class MemoryStoreError(MemoryError):
    status_code = 500
    detail = "Memory store operation failed"
    error_code = "MEMORY_STORE_ERROR"


class MemoryRetrievalError(MemoryError):
    status_code = 500
    detail = "Memory retrieval failed"
    error_code = "MEMORY_RETRIEVAL_ERROR"


class MemoryPermissionError(MemoryError):
    status_code = 403
    detail = "Memory permission denied"
    error_code = "MEMORY_PERMISSION_DENIED"


class MemoryNotFoundError(MemoryError):
    status_code = 404
    detail = "Memory entry not found"
    error_code = "MEMORY_NOT_FOUND"


class MemorySessionError(MemoryError):
    status_code = 409
    detail = "Memory session error"
    error_code = "MEMORY_SESSION_ERROR"


class MemoryPersistenceError(MemoryError):
    status_code = 500
    detail = "Memory persistence failed"
    error_code = "MEMORY_PERSISTENCE_ERROR"
