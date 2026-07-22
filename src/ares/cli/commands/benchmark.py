from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from ares.cli.utils.console import console, exit_with_error, print_success
from ares.cli.utils.formatting import format_duration
from ares.cli.utils.progress import spinner_progress
from ares.cli.utils.tables import print_table

if TYPE_CHECKING:
    from duplicate_question_app._evaluation.benchmark_result import BenchmarkResult


def run_benchmark(
    config: str | None = typer.Option(None, "--config", "-c", help="Benchmark configuration name"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    epochs: int = typer.Option(1, "--epochs", "-e", help="Number of epochs"),
) -> None:
    try:
        from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner
    except ImportError:
        exit_with_error("Benchmark modules not available")

    with spinner_progress("Running benchmark..."):
        runner = BenchmarkRunner()
        test_pairs: list[tuple[str, str, int]] = []
        result: BenchmarkResult | dict[str, BenchmarkResult] | None
        if config:
            result = runner.run_configuration(config, None, test_pairs)
        else:
            result = runner.run_all_configurations(None, test_pairs)

    if not result:
        console.print("[yellow]No benchmark results[/yellow]")
        return

    results_dict = result if isinstance(result, dict) else {config or "default": result}
    output_data = {
        "config": config or "all",
        "epochs": epochs,
        "results": {k: v.to_dict() for k, v in results_dict.items()},
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
    for name, res in results.items():
        rows.append(
            [
                name,
                format_duration(res.total_latency_ms),
                f"{res.throughput:.3f}",
                str(res.num_samples),
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
        return

    assert b1 is not None and b2 is not None
    rows = [
        ["Latency", format_duration(b1.total_latency_ms), format_duration(b2.total_latency_ms)],
        ["Throughput", f"{b1.throughput:.3f}", f"{b2.throughput:.3f}"],
        ["Samples", str(b1.num_samples), str(b2.num_samples)],
    ]

    print_table(
        f"Comparison: {benchmark1} vs {benchmark2}",
        ["Metric", benchmark1, benchmark2],
        rows,
    )
