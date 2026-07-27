from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class EventSeverity(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class Event:
    event_id: str
    source: str
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    severity: EventSeverity = EventSeverity.INFO
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: str = ""


logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = {}
        self._events: list[Event] = []
        self._max_events: int = 10000

    @property
    def events(self) -> list[Event]:
        return list(self._events)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: Any) -> None:
        normalized = self._normalize(event)
        if normalized:
            self._events.append(normalized)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events :]
            for handler in self._subscribers.get(normalized.event_type, []):
                from contextlib import suppress

                with suppress(Exception):
                    handler(normalized)

    def emit(self, source: str, *args: Any, **kwargs: Any) -> Event:
        event_type = ""
        data: dict[str, Any] = {}

        if args:
            first_arg = args[0]
            if isinstance(first_arg, str):
                event_type = first_arg
            else:
                data["event_object"] = self._serialize_value(first_arg)
                if hasattr(first_arg, "event_type"):
                    et = getattr(first_arg, "event_type", "")
                    event_type = et.name if hasattr(et, "name") else str(et) if et else "event"
                elif hasattr(first_arg, "type"):
                    t = getattr(first_arg, "type", "")
                    event_type = t.name if hasattr(t, "name") else str(t) if t else "event"
                else:
                    event_type = type(first_arg).__name__

            for arg in args[1:]:
                key = f"arg_{args.index(arg)}"
                data[key] = self._serialize_value(arg)

        for k, v in kwargs.items():
            data[k] = self._serialize_value(v)

        if not event_type:
            event_type = data.get("event_type", "event")

        event = Event(
            event_id=str(uuid.uuid4()),
            source=source,
            event_type=str(event_type),
            data=data,
            severity=EventSeverity.INFO,
            trace_id="",
        )
        self.publish(event)
        return event

    def _serialize_value(self, v: Any) -> Any:
        if isinstance(v, (str, int, float, bool, type(None))):
            return v
        if isinstance(v, dict):
            return {k: self._serialize_value(v) for k, v in v.items()}
        if isinstance(v, list):
            return [self._serialize_value(i) for i in v]
        if hasattr(v, "name"):
            return v.name
        if hasattr(v, "isoformat"):
            return v.isoformat()
        if hasattr(v, "__dict__"):
            result: dict[str, Any] = {}
            for attr in dir(v):
                if not attr.startswith("_") and not callable(getattr(v, attr)):
                    try:
                        val = getattr(v, attr)
                        if isinstance(val, (str, int, float, bool, list, dict, type(None))):
                            result[attr] = val
                        elif hasattr(val, "name"):
                            result[attr] = val.name
                        elif hasattr(val, "isoformat"):
                            result[attr] = val.isoformat()
                        else:
                            result[attr] = str(val)
                    except Exception as exc:
                        logger.warning("Failed to serialize attribute '%s': %s", attr, exc)
            return result
        return str(v)

    def _normalize(self, event: Any) -> Event | None:
        if isinstance(event, Event):
            return event

        event_id = getattr(event, "event_id", str(uuid.uuid4()))
        source = getattr(event, "source", type(event).__name__)

        if hasattr(event, "event_type"):
            et = event.event_type
            event_type = et.name if hasattr(et, "name") else str(et)
        elif hasattr(event, "type"):
            t = event.type
            event_type = t.name if hasattr(t, "name") else str(t)
        else:
            event_type = type(event).__name__

        data: dict[str, Any] = {}
        for attr in dir(event):
            if not attr.startswith("_") and not callable(getattr(event, attr)):
                try:
                    val = getattr(event, attr)
                    if isinstance(val, (str, int, float, bool, list, dict, type(None))):
                        data[attr] = val
                    elif hasattr(val, "name"):
                        data[attr] = val.name
                    elif hasattr(val, "isoformat"):
                        data[attr] = val.isoformat()
                    else:
                        data[attr] = str(val)
                except Exception as exc:
                    logger.warning("Failed to normalize attribute '%s': %s", attr, exc)

        severity = EventSeverity.ERROR if getattr(event, "error", None) else EventSeverity.INFO
        trace_id = getattr(event, "trace_id", "")

        return Event(
            event_id=str(event_id),
            source=str(source),
            event_type=str(event_type),
            data=data,
            severity=severity,
            trace_id=str(trace_id or ""),
        )

    def get_events(self, event_type: str | None = None, source: str | None = None, limit: int = 100) -> list[Event]:
        result = self._events
        if event_type:
            result = [e for e in result if e.event_type == event_type]
        if source:
            result = [e for e in result if e.source == source]
        return result[-limit:]

    def clear(self) -> None:
        self._events.clear()

    def get_stats(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for e in self._events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        return {
            "total_events": len(self._events),
            "event_type_counts": counts,
        }
