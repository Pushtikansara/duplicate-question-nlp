from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from ares.cli.utils.console import console, exit_with_error, print_success
from ares.cli.utils.formatting import format_duration, save_output
from ares.cli.utils.tables import print_table


def generate_profile(
    output: str | None = typer.Option(None, "--output", "-o", help="Output profile file"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, chrome)"),
) -> None:
    try:
        from duplicate_question_app._profiling import Profiler
    except ImportError:
        exit_with_error("Profiler module not available")

    p = Profiler()
    stats = p.get_stats()
    report = p.get_report()

    profile_data: dict[str, Any] | list[dict[str, Any]] = {
        "stats": stats,
        "report": report,
    }

    if format == "chrome":
        profile_data = _to_chrome_trace(report)

    if output:
        path = Path(output)
        save_output(profile_data, path)
        print_success(f"Profile saved to {path}")
    else:
        console.print(json.dumps(profile_data, indent=2, default=str))
    print_success("Profile generated")


def show_metrics() -> None:
    try:
        from duplicate_question_app._profiling import Profiler
    except ImportError:
        exit_with_error("Profiler module not available")

    p = Profiler()
    stats = p.get_stats()

    if not stats:
        console.print("[yellow]No metrics available[/yellow]")
        console.print("Run some operations first to collect metrics")
        return

    rows = []
    for func_name, entry in stats.items():
        rows.append(
            [
                func_name,
                str(entry.call_count),
                format_duration(entry.total_time_ms),
                format_duration(entry.avg_time_ms),
            ]
        )

    print_table(
        "Profile Metrics",
        ["Function", "Calls", "Total Time", "Avg Time"],
        rows,
    )


def export_metrics(
    output: str = typer.Argument("metrics.json", help="Output file path"),
) -> None:
    try:
        from duplicate_question_app._profiling import Profiler
    except ImportError:
        exit_with_error("Profiler module not available")

    p = Profiler()
    stats = p.get_stats()
    Path(output).write_text(json.dumps(stats, indent=2, default=str))
    print_success(f"Metrics exported to {output}")


def show_stats() -> None:
    try:
        from duplicate_question_app._profiling import Profiler
    except ImportError:
        exit_with_error("Profiler module not available")

    p = Profiler()
    stats = p.get_stats()

    if not stats:
        console.print("[yellow]No statistics available[/yellow]")
        return

    total_calls = sum(e.call_count for e in stats.values())
    total_time = sum(e.total_time_ms for e in stats.values())

    console.print("[bold cyan]Runtime Statistics[/bold cyan]")
    console.print(f"  Total function calls:  {total_calls}")
    console.print(f"  Total time:           {format_duration(total_time)}")
    console.print(f"  Profiled functions:   {len(stats)}")


def export_stats(
    output: str = typer.Argument("stats.json", help="Output file path"),
) -> None:
    try:
        from duplicate_question_app._profiling import Profiler
    except ImportError:
        exit_with_error("Profiler module not available")

    p = Profiler()
    stats = p.get_stats()
    Path(output).write_text(json.dumps(stats, indent=2, default=str))
    print_success(f"Statistics exported to {output}")


def _to_chrome_trace(profiles: list[dict]) -> list[dict]:
    events = []
    for i, profile in enumerate(profiles):
        events.append(
            {
                "name": profile.get("name", f"func_{i}"),
                "cat": "profile",
                "ph": "X",
                "ts": int(profile.get("timestamp", 0) * 1000),
                "dur": int(profile.get("elapsed_ms", 0) * 1000),
                "tid": 1,
                "pid": 1,
                "args": {"detail": str(profile.get("detail", ""))},
            }
        )
    return events
