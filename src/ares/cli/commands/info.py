from __future__ import annotations

from pathlib import Path

from ares.cli.utils.console import console


def info_cmd() -> None:
    from duplicate_question_app import __version__

    system_info = _get_system_info()
    console.print("[bold cyan]ARES System Information[/bold cyan]")
    console.print(f"  Version:       {__version__}")
    console.print(f"  Python:        {system_info['python_version']}")
    console.print(f"  Platform:      {system_info['platform']}")
    console.print(f"  CPU Cores:     {system_info['cpu_count']}")
    console.print(f"  Memory:        {system_info['memory']}")
    console.print(f"  Project Root:  {system_info['project_root']}")


def _get_system_info() -> dict[str, str]:
    import os

    import psutil

    return {
        "python_version": __import__("sys").version.split()[0],
        "platform": __import__("sys").platform,
        "cpu_count": str(os.cpu_count() or 0),
        "memory": _format_bytes(psutil.virtual_memory().total),
        "project_root": str(_find_project_root()),
    }


def _find_project_root() -> Path:
    from duplicate_question_app._config.settings import get_app_paths

    return get_app_paths().project_root


def _format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n //= 1024
    return f"{n:.1f}PB"
