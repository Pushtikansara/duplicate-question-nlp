from __future__ import annotations

import json

import typer

from ares.cli.utils.console import console, exit_with_error
from ares.cli.utils.formatting import format_duration


def predict(
    question1: str = typer.Argument(..., help="First question"),
    question2: str = typer.Argument(..., help="Second question"),
    model: str | None = typer.Option(None, "--model", "-m", help="Model name"),
    threshold: float | None = typer.Option(None, "--threshold", "-t", help="Decision threshold"),
    reflect: bool = typer.Option(False, "--reflect", help="Enable reflection/trust scoring"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    from ares import ARES

    engine = ARES()
    if model:
        engine.with_model(model)
    if threshold is not None:
        engine.with_threshold(threshold)
    if reflect:
        engine.with_reflection(True)

    try:
        result = engine.predict(question1, question2)
    except Exception as e:
        exit_with_error(f"Prediction failed: {e}")

    if json_output:
        console.print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        console.print(f"Prediction: [bold cyan]{result.prediction}[/bold cyan]")
        console.print(f"Confidence: {result.confidence:.4f}")
        console.print(f"Label:      {result.predicted_label}")
        console.print(f"Model:      {result.model_name}")
        console.print(f"Latency:    {format_duration(result.latency_ms)}")
        if result.trust_score is not None:
            console.print(f"Trust:      {result.trust_score:.1f} ({result.trust_level})")
            console.print(f"Risk:       {result.risk_level}")
