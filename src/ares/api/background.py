from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


class BackgroundTask:
    def __init__(
        self,
        task_id: str,
        name: str,
        fn: Callable[..., Any],
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.task_id = task_id
        self.name = name
        self.fn = fn
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.status: str = "pending"
        self.result: Any = None
        self.error: str | None = None
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self._thread: threading.Thread | None = None

    def run(self) -> None:
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)
        try:
            self.result = self.fn(*self.args, **self.kwargs)
            self.status = "completed"
        except Exception as e:
            self.error = str(e)
            self.status = "failed"
            logger.exception("Background task %s failed: %s", self.task_id, e)
        finally:
            self.completed_at = datetime.now(timezone.utc)

    def start(self) -> None:
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class BackgroundTaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, BackgroundTask] = {}

    def submit(
        self,
        name: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        task_id = str(uuid.uuid4())
        task = BackgroundTask(task_id, name, fn, args, kwargs)
        self._tasks[task_id] = task
        task.start()
        logger.info("Background task submitted: %s (%s)", name, task_id)
        return task_id

    def get(self, task_id: str) -> BackgroundTask | None:
        return self._tasks.get(task_id)

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        task_list = list(self._tasks.values())
        if status:
            task_list = [t for t in task_list if t.status == status]
        return [
            t.to_dict()
            for t in sorted(
                task_list,
                key=lambda t: t.started_at or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
        ]

    def cleanup(self, max_age_hours: int = 24) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        to_remove = [tid for tid, t in self._tasks.items() if t.completed_at and t.completed_at < cutoff]
        for tid in to_remove:
            del self._tasks[tid]
        return len(to_remove)


_background_tasks: BackgroundTaskManager | None = None


def get_background_tasks() -> BackgroundTaskManager:
    global _background_tasks
    if _background_tasks is None:
        _background_tasks = BackgroundTaskManager()
    return _background_tasks
