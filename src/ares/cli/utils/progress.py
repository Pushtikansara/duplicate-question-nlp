from __future__ import annotations

import contextlib
from collections.abc import Generator
from typing import Any

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


@contextlib.contextmanager
def spinner_progress(description: str = "Working...") -> Generator[Progress, Any, None]:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
    )
    with progress:
        task = progress.add_task(description=description, total=None)
        try:
            yield progress
        finally:
            progress.update(task, completed=True)


@contextlib.contextmanager
def task_progress(description: str = "Processing...", total: int = 100) -> Generator[Progress, Any, None]:
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
    )
    with progress:
        task = progress.add_task(description=description, total=total)
        try:
            yield progress
        finally:
            progress.update(task, completed=True)


@contextlib.contextmanager
def indeterminate_progress(description: str = "Working...") -> Generator[Progress, Any, None]:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )
    with progress:
        task = progress.add_task(description=description, total=None)
        try:
            yield progress
        finally:
            progress.update(task, completed=True)
