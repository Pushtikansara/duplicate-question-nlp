from __future__ import annotations

import json
from pathlib import Path

import typer

from ares.cli.utils.console import console, exit_with_error, print_success
from ares.cli.utils.formatting import format_duration
from ares.cli.utils.progress import spinner_progress
from ares.cli.utils.tables import print_table


def inspect_pipeline(
    name: str | None = typer.Option(None, "--name", "-n", help="Pipeline name"),
) -> None:
    try:
        from duplicate_question_app._integration.integration_configuration import IntegrationConfig
    except ImportError:
        exit_with_error("Pipeline modules not available")

    config = IntegrationConfig()

    modules = [
        ("Perception", config.enable_perception),
        ("Routing", config.enable_routing),
        ("Memory Read", config.enable_memory_read),
        ("Semantic", config.enable_semantic),
        ("Reasoning", config.enable_reasoning),
        ("Debate", config.enable_debate),
        ("Decision", config.enable_decision),
        ("Memory Write", config.enable_memory_write),
    ]

    rows = []
    for mod_name, enabled in modules:
        rows.append([mod_name, "[green]Enabled[/green]" if enabled else "[dim]Disabled[/dim]"])

    print_table(
        "Pipeline Modules",
        ["Module", "Status"],
        rows,
    )


def graph_pipeline(
    output: str | None = typer.Option(None, "--output", "-o", help="Output file for graph"),
) -> None:
    modules = [
        "Perception",
        "Routing",
        "Memory Read",
        "Semantic",
        "Reasoning",
        "Debate",
        "Decision",
        "Memory Write",
    ]

    graph_data = {
        "nodes": modules,
        "edges": [(modules[i], modules[i + 1]) for i in range(len(modules) - 1)],
    }

    if output:
        Path(output).write_text(json.dumps(graph_data, indent=2))
        print_success(f"Pipeline graph saved to {output}")
    else:
        console.print("[bold cyan]Pipeline Graph[/bold cyan]")
        for i, mod in enumerate(modules):
            prefix = "  " * i
            console.print(f"{prefix}[green]{mod}[/green]")
            if i < len(modules) - 1:
                console.print(f"{prefix}  [dim]|[/dim]")
                console.print(f"{prefix}  [dim]v[/dim]")

    print_success("Pipeline graph generated")


def run_pipeline(
    question1: str = typer.Argument(..., help="First question"),
    question2: str = typer.Argument(..., help="Second question"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file"),
) -> None:
    try:
        from duplicate_question_app._integration.cognitive_pipeline import CognitivePipeline
    except ImportError:
        exit_with_error("Pipeline modules not available")

    with spinner_progress("Running pipeline..."):
        try:
            pipeline = CognitivePipeline()

            from ares import ARES

            engine = ARES()

            def predict_fn(q1: str, q2: str):
                return engine.predict(q1, q2)

            result = pipeline.run(question1, question2, predict_fn)
        except Exception as e:
            exit_with_error(f"Pipeline execution failed: {e}")

    if output:
        output_data = {
            "success": result.success,
            "prediction": str(result.prediction),
            "metadata": {
                "total_latency_ms": result.metadata.total_latency_ms,
                "modules_executed": result.metadata.modules_executed,
            },
        }
        Path(output).write_text(json.dumps(output_data, indent=2, default=str))
        print_success(f"Pipeline result saved to {output}")
    else:
        console.print("[bold cyan]Pipeline Result[/bold cyan]")
        console.print(f"  Success:  {result.success}")
        console.print(f"  Prediction: {result.prediction}")
        if hasattr(result, "metadata"):
            meta = result.metadata
            console.print(f"  Latency:  {format_duration(meta.total_latency_ms)}")
            console.print(f"  Modules:  {meta.modules_executed}")

    print_success("Pipeline execution complete")
