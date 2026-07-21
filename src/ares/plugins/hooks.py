from __future__ import annotations

from enum import Enum, auto
from typing import Any

from ares.plugins.context import PluginContext


class HookPoint(Enum):
    """Enumeration of all lifecycle hook points."""

    ON_INSTALL = auto()
    ON_LOAD = auto()
    ON_INITIALIZE = auto()
    BEFORE_PIPELINE = auto()
    AFTER_PIPELINE = auto()
    BEFORE_PERCEPTION = auto()
    AFTER_PERCEPTION = auto()
    BEFORE_SEMANTICS = auto()
    AFTER_SEMANTICS = auto()
    BEFORE_MEMORY = auto()
    AFTER_MEMORY = auto()
    BEFORE_REASONING = auto()
    AFTER_REASONING = auto()
    BEFORE_REFLECTION = auto()
    AFTER_REFLECTION = auto()
    BEFORE_OUTPUT = auto()
    AFTER_OUTPUT = auto()
    ON_SHUTDOWN = auto()


HookHandler = Any


class HookEvent:
    """Data associated with a hook execution."""

    def __init__(
        self,
        hook_point: HookPoint,
        context: PluginContext,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.hook_point = hook_point
        self.context = context
        self.data: dict[str, Any] = data or {}
        self.modified_data: dict[str, Any] = dict(self.data)
        self.cancelled = False
        self.messages: list[str] = []

    def cancel(self, reason: str = "") -> None:
        self.cancelled = True
        if reason:
            self.messages.append(reason)


class EventBus:
    """Simple publish/subscribe event bus for hook execution."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[HookHandler]] = {}

    def subscribe(self, event: str, handler: HookHandler) -> None:
        self._subscribers.setdefault(event, []).append(handler)

    def unsubscribe(self, event: str, handler: HookHandler) -> None:
        handlers = self._subscribers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)

    async def emit(self, event: str, **kwargs: Any) -> list[Any]:
        results: list[Any] = []
        for handler in self._subscribers.get(event, []):
            res = handler(**kwargs)
            if hasattr(res, "__await__"):
                res = await res
            results.append(res)
        return results
