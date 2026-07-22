from __future__ import annotations

from typing import Any

from ares.cli.utils.console import console


def get_version_info() -> dict[str, Any]:
    return {
        "ares": "0.2.0",
        "python": __import__("sys").version.split()[0],
        "platform": __import__("sys").platform,
    }


def version_cmd() -> None:
    info = get_version_info()
    console.print(f"ARES version: [bold cyan]{info['ares']}[/bold cyan]")
    console.print(f"Python:       {info['python']}")
    console.print(f"Platform:     {info['platform']}")
