from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def format_timestamp(ts: float | None) -> str:
    if ts is None:
        return "N/A"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def format_duration(ms: float) -> str:
    if ms < 1000:
        return f"{ms:.2f}ms"
    if ms < 60000:
        return f"{ms / 1000:.2f}s"
    return f"{ms / 60000:.2f}m"


def format_bytes(n: int | float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def format_percent(value: float) -> str:
    return f"{value:.1%}"


def truncate(text: str, max_length: int = 80) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def to_json(data: Any, indent: int = 2) -> str:
    return json.dumps(data, indent=indent, default=str)


def to_yaml(data: Any) -> str:
    return str(yaml.dump(data, default_flow_style=False, sort_keys=False))


def output_result(data: Any, output_format: str = "text") -> str:
    if output_format == "json":
        return to_json(data)
    if output_format == "yaml":
        return to_yaml(data)
    if isinstance(data, str):
        return data
    return str(data)


def save_output(data: Any, path: Path, output_format: str = "json") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = output_result(data, output_format)
    path.write_text(content)
    return path


def status_tag(passed: bool) -> str:
    return "[green]PASS[/green]" if passed else "[red]FAIL[/red]"


def checkmark(condition: bool) -> str:
    return "[green]\u2713[/green]" if condition else "[red]\u2717[/red]"
