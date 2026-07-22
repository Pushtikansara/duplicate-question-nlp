from __future__ import annotations

import json
from pathlib import Path

import typer

from ares.cli.utils.console import console, exit_with_error, print_success
from ares.cli.utils.formatting import format_duration
from ares.cli.utils.progress import spinner_progress
from ares.cli.utils.tables import print_table


def run_benchmark(
    config: str | None = typer.Option(None, "--config", "-c", help="Benchmark configuration name"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    epochs: int = typer.Option(1, "--epochs", "-e", help="Number of epochs"),
) -> None:
    try:
        from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner
        from duplicate_question_app._evaluation.benchmark_suite import BenchmarkSuite
    except ImportError:
        exit_with_error("Benchmark modules not available")

    with spinner_progress("Running benchmark..."):
        runner = BenchmarkRunner()
        suite = BenchmarkSuite(runner)

        result = suite.run_configuration(config) if config else suite.run_all()

    if not result:
        console.print("[yellow]No benchmark results[/yellow]")
        return

    output_data = {
        "config": config or "all",
        "epochs": epochs,
        "results": result if isinstance(result, dict) else {"result": str(result)},
    }

    if output:
        Path(output).write_text(json.dumps(output_data, indent=2, default=str))
        print_success(f"Benchmark results saved to {output}")
    else:
        console.print(json.dumps(output_data, indent=2, default=str))

    print_success("Benchmark complete")


def list_benchmarks() -> None:
    try:
        from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner
    except ImportError:
        exit_with_error("Benchmark modules not available")

    runner = BenchmarkRunner()
    results = runner.get_results() if hasattr(runner, "get_results") else {}

    if not results:
        console.print("[yellow]No benchmark results available[/yellow]")
        console.print("Run [bold]ares benchmark run[/bold] first")
        return

    rows = []
    for name, result in results.items():
        rows.append(
            [
                name,
                format_duration(result.get("total_latency_ms", 0)),
                f"{result.get('accuracy', 0):.3f}",
                str(result.get("samples", 0)),
            ]
        )

    print_table(
        "Benchmark Results",
        ["Config", "Latency", "Accuracy", "Samples"],
        rows,
    )


def compare_benchmarks(
    benchmark1: str = typer.Argument(..., help="First benchmark name"),
    benchmark2: str = typer.Argument(..., help="Second benchmark name"),
) -> None:
    try:
        from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner
    except ImportError:
        exit_with_error("Benchmark modules not available")

    runner = BenchmarkRunner()
    results = runner.get_results() if hasattr(runner, "get_results") else {}

    b1 = results.get(benchmark1)
    b2 = results.get(benchmark2)

    if not b1 or not b2:
        exit_with_error(f"One or both benchmarks not found: {benchmark1}, {benchmark2}")

    rows = [
        ["Latency", format_duration(b1.get("total_latency_ms", 0)), format_duration(b2.get("total_latency_ms", 0))],
        ["Accuracy", f"{b1.get('accuracy', 0):.3f}", f"{b2.get('accuracy', 0):.3f}"],
        ["Samples", str(b1.get("samples", 0)), str(b2.get("samples", 0))],
    ]

    print_table(
        f"Comparison: {benchmark1} vs {benchmark2}",
        ["Metric", benchmark1, benchmark2],
        rows,
    )
