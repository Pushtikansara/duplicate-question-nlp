from __future__ import annotations

import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
start_time_var: ContextVar[float] = ContextVar("start_time", default=0.0)


class APIRequestContext:
    """Holds per-request contextual data and provides timing utilities.

    Typical usage::

        ctx = APIRequestContext(request_id="...", user_id="...")
        ctx.set_context()
        # ... later ...
        elapsed = ctx.elapsed_ms()
    """

    def __init__(
        self,
        request_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id or "anonymous"
        self.started_at = datetime.now(timezone.utc)
        self.start_time = self.started_at.timestamp()
        self.trace: dict[str, Any] = {}

    def set_context(self) -> None:
        """Persist this context's values into the module-level ``ContextVar``
        variables so they can be retrieved via :func:`get_current_request_id`
        and :func:`get_current_user_id` from anywhere in the call stack.
        """
        request_id_var.set(self.request_id)
        user_id_var.set(self.user_id)
        start_time_var.set(self.start_time)

    def elapsed_ms(self) -> float:
        """Return the number of milliseconds since this context was created.

        Returns:
            Elapsed time in milliseconds.
        """
        return (datetime.now(timezone.utc).timestamp() - self.start_time) * 1000

    def add_trace(self, key: str, value: Any) -> None:
        """Store an arbitrary value in the internal trace dictionary.

        Args:
            key: The trace key.
            value: The value to associate with the key.
        """
        self.trace[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Serialize this context to a JSON-compatible dictionary.

        Returns:
            A dictionary with ``request_id``, ``user_id``, ``started_at``,
            and ``elapsed_ms`` keys.
        """
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "elapsed_ms": self.elapsed_ms(),
        }


def get_current_request_id() -> str:
    """Retrieve the current request ID from the context variable.

    Returns:
        The active request ID, or an empty string if no context has been
        set.
    """
    return request_id_var.get()


def get_current_user_id() -> str:
    """Retrieve the current user ID from the context variable.

    Returns:
        The active user ID, or an empty string if no context has been set.
    """
    return user_id_var.get()
