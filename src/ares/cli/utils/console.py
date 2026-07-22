from __future__ import annotations

import functools
import sys
from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

custom_theme = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "dim": "dim white",
        "highlight": "bold magenta",
        "pass": "green",
        "fail": "red",
    }
)

console = Console(theme=custom_theme, highlight=False)
error_console = Console(stderr=True, theme=custom_theme, highlight=False)


def print_info(message: str) -> None:
    console.print(message, style="info")


def print_success(message: str) -> None:
    console.print(message, style="success")


def print_warning(message: str) -> None:
    console.print(message, style="warning")


def print_error(message: str) -> None:
    error_console.print(message, style="error")


def print_panel(title: str, content: str, style: str = "info") -> None:
    console.print(Panel(content, title=title, border_style=style))


def exit_with_error(message: str, code: int = 1) -> None:
    print_error(message)
    sys.exit(code)


def handle_cli_error(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exit_with_error(f"{func.__name__}: {e}")
            return None

    return wrapper
