from __future__ import annotations

import sys

import typer

from ares.cli.utils.console import console, exit_with_error
from ares.cli.utils.progress import spinner_progress


def start_server(
    host: str = typer.Option("localhost", "--host", "-H", help="Host to bind to"),
    port: int = typer.Option(8501, "--port", "-p", help="Port to bind to"),
    app_path: str | None = typer.Option(None, "--app", "-a", help="Streamlit app path"),
    dev: bool = typer.Option(False, "--dev", help="Run in development mode"),
) -> None:
    if app_path:
        import subprocess

        console.print(f"[bold cyan]Starting ARES server on {host}:{port}[/bold cyan]")
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            app_path,
            "--server.address",
            host,
            "--server.port",
            str(port),
        ]
        if dev:
            cmd.append("--server.runOnSave")
            cmd.append("true")

        with spinner_progress("Starting server..."):
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                console.print("\n[yellow]Server stopped[/yellow]")
    else:
        try:
            from run_app import main as run_app_main

            console.print(f"[bold cyan]Starting ARES server on {host}:{port}[/bold cyan]")
            run_app_main()
        except ImportError:
            exit_with_error("Could not find app entry point. Specify --app or ensure run_app.py exists.")
