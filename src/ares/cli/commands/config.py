from __future__ import annotations

import json
import os
from pathlib import Path

import typer
import yaml

from ares.cli.utils.console import console, exit_with_error, print_success


def _get_global_config_path() -> Path:
    return Path.home() / ".ares" / "config.toml"


def _get_project_config_path() -> Path:
    return Path.cwd() / ".ares.toml"


def _load_config_section(section: str) -> dict:
    try:
        from duplicate_question_app._config.settings import get_config

        return get_config(section) or {}
    except Exception:
        return {}


def show_config(
    section: str | None = typer.Argument(None, help="Config section to show"),
    verbose: bool = False,
) -> None:
    sections = (
        [section]
        if section
        else ["app", "paths", "inference", "models", "training", "evaluation", "dataset", "logging"]
    )
    if not verbose:
        sections = [s for s in sections if s in ("app", "paths", "inference", "logging")]

    config_data = {}
    for sec in sections:
        cfg = _load_config_section(sec)
        if cfg:
            config_data[sec] = cfg

    if not config_data:
        console.print("[yellow]No configuration loaded[/yellow]")
        return

    for sec, cfg in config_data.items():
        console.print(f"\n[bold cyan][{sec}][/bold cyan]")
        _print_config_dict(cfg, indent=2)


def _print_config_dict(cfg: dict, indent: int = 2) -> None:
    prefix = " " * indent
    for key, value in cfg.items():
        if isinstance(value, dict):
            console.print(f"{prefix}[bold]{key}:[/bold]")
            _print_config_dict(value, indent + 2)
        elif isinstance(value, list):
            console.print(f"{prefix}{key}:")
            for item in value[:5]:
                console.print(f"{prefix}  - {item}")
            if len(value) > 5:
                console.print(f"{prefix}  ... and {len(value) - 5} more")
        else:
            console.print(f"{prefix}{key}: {value}")


def edit_config() -> None:
    import subprocess

    config_path = _get_project_config_path()
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("# ARES Project Configuration\n")

    editor = os.environ.get("EDITOR", "vi")
    try:
        subprocess.run([editor, str(config_path)])
        print_success(f"Configuration saved to {config_path}")
    except FileNotFoundError:
        exit_with_error(f"Editor not found: {editor}. Set EDITOR environment variable.")


def validate_config() -> None:
    issues = []

    global_cfg = _get_global_config_path()
    if global_cfg.exists():
        console.print(f"[green]Global config:[/green] {global_cfg}")
    else:
        console.print(f"[dim]Global config not found: {global_cfg}[/dim]")

    project_cfg = _get_project_config_path()
    if project_cfg.exists():
        console.print(f"[green]Project config:[/green] {project_cfg}")
    else:
        console.print(f"[dim]Project config not found: {project_cfg}[/dim]")

    try:
        from duplicate_question_app._config.settings import get_app_paths

        paths = get_app_paths()
        config_dir = paths.project_root / "configs"
        if config_dir.exists():
            yaml_files = list(config_dir.glob("*.yaml"))
            console.print(f"[green]Config files:[/green] {len(yaml_files)} YAML files")
        else:
            issues.append("Config directory not found")

    except Exception as e:
        issues.append(str(e))

    if issues:
        console.print(f"\n[yellow]{len(issues)} issue(s) found:[/yellow]")
        for issue in issues:
            console.print(f"  - {issue}")
    else:
        print_success("Configuration is valid")


def export_config(
    output: str = typer.Argument("config_export.json", help="Output file path"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, yaml)"),
) -> None:
    sections = ["app", "paths", "inference", "models", "training", "evaluation", "dataset", "logging"]
    config_data = {}

    for sec in sections:
        cfg = _load_config_section(sec)
        if cfg:
            config_data[sec] = cfg

    out_path = Path(output)
    if format == "yaml":
        out_path.write_text(yaml.dump(config_data, default_flow_style=False))
    else:
        out_path.write_text(json.dumps(config_data, indent=2, default=str))

    print_success(f"Configuration exported to {out_path}")
