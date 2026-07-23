from __future__ import annotations

from ares.tools.exceptions import (
    ToolDisabledError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolRegistrationError,
    ToolTimeoutError,
)


class TestToolExceptions:
    def test_base(self):
        exc = ToolError()
        assert exc.status_code == 500
        assert exc.error_code == "TOOL_ERROR"

    def test_not_found(self):
        exc = ToolNotFoundError(detail="Missing")
        assert exc.status_code == 404
        assert exc.error_code == "TOOL_NOT_FOUND"

    def test_execution_error(self):
        exc = ToolExecutionError(detail="Exec fail")
        assert exc.status_code == 500
        assert exc.error_code == "TOOL_EXECUTION_ERROR"

    def test_permission_denied(self):
        exc = ToolPermissionError(detail="No access")
        assert exc.status_code == 403
        assert exc.error_code == "TOOL_PERMISSION_DENIED"

    def test_timeout(self):
        exc = ToolTimeoutError(detail="Timed out")
        assert exc.status_code == 504
        assert exc.error_code == "TOOL_TIMEOUT"

    def test_disabled(self):
        exc = ToolDisabledError(detail="Disabled")
        assert exc.status_code == 409
        assert exc.error_code == "TOOL_DISABLED"

    def test_registration(self):
        exc = ToolRegistrationError(detail="Duplicate")
        assert exc.status_code == 409
        assert exc.error_code == "TOOL_REGISTRATION_ERROR"

    def test_hierarchy(self):
        assert issubclass(ToolNotFoundError, ToolError)
        assert issubclass(ToolExecutionError, ToolError)
        assert issubclass(ToolPermissionError, ToolError)
        assert issubclass(ToolTimeoutError, ToolError)
        assert issubclass(ToolDisabledError, ToolError)
        assert issubclass(ToolRegistrationError, ToolError)
