from __future__ import annotations

import json
from pathlib import Path

import typer

from ares.cli.utils.console import console, exit_with_error, print_success
from ares.cli.utils.formatting import save_output


def _get_trace_recorder():
    try:
        from duplicate_question_app._reasoning.reasoning_trace import TraceRecorder

        return TraceRecorder()
    except ImportError:
        exit_with_error("TraceRecorder not available")


def _get_decision_trace():
    try:
        from duplicate_question_app._explainability.trace import generate_decision_trace

        return generate_decision_trace
    except ImportError:
        exit_with_error("Decision trace module not available")


def run_trace(
    question1: str = typer.Argument(..., help="First question"),
    question2: str = typer.Argument(..., help="Second question"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output trace file"),
) -> None:
    try:
        from duplicate_question_app._explainability.trace import generate_decision_trace

        trace = generate_decision_trace(question1, question2, {})
        data = trace.to_dict() if hasattr(trace, "to_dict") else {"decision": str(trace)}

        if output:
            path = Path(output)
            save_output(data, path)
            print_success(f"Trace saved to {path}")
        else:
            console.print(json.dumps(data, indent=2, default=str))

    except Exception as e:
        exit_with_error(f"Trace run failed: {e}")


def inspect_trace(
    trace_file: str = typer.Argument(..., help="Path to trace file"),
) -> None:
    path = Path(trace_file)
    if not path.exists():
        exit_with_error(f"Trace file not found: {trace_file}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        exit_with_error(f"Invalid JSON in trace file: {trace_file}")

    console.print("[bold cyan]Trace Details[/bold cyan]")
    for key, value in data.items():
        if isinstance(value, dict):
            console.print(f"  [cyan]{key}:[/cyan]")
            for k, v in value.items():
                console.print(f"    {k}: {v}")
        elif isinstance(value, list):
            console.print(f"  [cyan]{key}:[/cyan]")
            for item in value:
                console.print(f"    - {item}")
        else:
            console.print(f"  [cyan]{key}:[/cyan] {value}")


def export_trace(
    trace_file: str = typer.Argument(..., help="Path to trace file"),
    output: str = typer.Argument("trace_export.json", help="Output file path"),
    fmt: str = typer.Option("json", "--format", "-f", help="Export format (json, chrome)"),
) -> None:
    path = Path(trace_file)
    if not path.exists():
        exit_with_error(f"Trace file not found: {trace_file}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        exit_with_error(f"Invalid JSON in trace file: {trace_file}")

    if fmt == "chrome":
        chrome_events = _to_chrome_trace(data)
        data = chrome_events
    elif fmt != "json":
        exit_with_error(f"Unsupported format: {fmt}")

    out_path = Path(output)
    out_path.write_text(json.dumps(data, indent=2, default=str))
    print_success(f"Trace exported to {out_path}")


def _to_chrome_trace(data: dict) -> list[dict]:
    events = []
    for key, value in data.items():
        events.append(
            {
                "name": key,
                "cat": "trace",
                "ph": "i",
                "ts": 0,
                "args": {"value": str(value)},
            }
        )
    return events


def replay_trace(
    trace_file: str = typer.Argument(..., help="Path to trace file"),
) -> None:
    path = Path(trace_file)
    if not path.exists():
        exit_with_error(f"Trace file not found: {trace_file}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        exit_with_error(f"Invalid JSON in trace file: {trace_file}")

    console.print("[bold cyan]Replaying trace...[/bold cyan]")
    for key, value in data.items():
        console.print(f"  [cyan]{key}:[/cyan] {value}")

    print_success("Trace replay complete")
