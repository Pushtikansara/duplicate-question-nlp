from __future__ import annotations

from collections.abc import Callable
from typing import Any

from duplicate_question_app._integration.pipeline_events import PipelineEvent

EventHandler = Callable[[PipelineEvent, dict[str, Any]], None]


class PipelineHook:
    def __init__(self) -> None:
        self._handlers: dict[PipelineEvent, list[EventHandler]] = {}

    def subscribe(self, event: PipelineEvent, handler: EventHandler) -> None:
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def unsubscribe(self, event: PipelineEvent, handler: EventHandler) -> None:
        if event in self._handlers:
            self._handlers[event] = [h for h in self._handlers[event] if h is not handler]

    def publish(self, event: PipelineEvent, context: dict[str, Any]) -> None:
        for handler in self._handlers.get(event, []):
            handler(event, context)

    def clear(self) -> None:
        self._handlers.clear()
