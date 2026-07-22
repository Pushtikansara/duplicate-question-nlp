from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from ares.cli.utils.console import print_success
from ares.cli.utils.formatting import save_output
from ares.cli.utils.progress import spinner_progress


def export_cmd(
    output: str = typer.Argument("ares_export.json", help="Output file path"),
    sections: str = typer.Option("all", "--sections", "-s", help="Sections to export (comma-separated, or 'all')"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, yaml)"),
) -> None:
    export_data: dict[str, Any] = {}

    if sections == "all":
        sections_list = ["version", "config", "plugins", "stats"]
    else:
        sections_list = [s.strip() for s in sections.split(",")]

    with spinner_progress("Exporting system data..."):
        if "version" in sections_list:
            export_data["version"] = _export_version()

        if "config" in sections_list:
            export_data["config"] = _export_config()

        if "plugins" in sections_list:
            export_data["plugins"] = _export_plugins()

        if "stats" in sections_list:
            export_data["stats"] = _export_stats()

    out_path = Path(output)
    save_output(export_data, out_path, format)
    print_success(f"Export saved to {out_path}")


def _export_version() -> dict[str, str]:
    try:
        from duplicate_question_app import __version__

        return {"ares": __version__, "python": __import__("sys").version.split()[0]}
    except ImportError:
        return {"ares": "unknown", "python": __import__("sys").version.split()[0]}


def _export_config() -> dict[str, Any]:
    sections = ["app", "paths", "inference", "models", "training", "evaluation", "dataset", "logging"]
    config_data: dict[str, Any] = {}
    for sec in sections:
        try:
            from duplicate_question_app._config.settings import get_config

            cfg = get_config(sec)
            if cfg:
                config_data[sec] = cfg
        except Exception:
            pass
    return config_data


def _export_plugins() -> list[dict[str, Any]]:
    try:
        from ares.plugins import PluginManager

        pm = PluginManager()
        pm.load()
        plugins = pm.list()
        return [
            {
                "id": p.plugin_id,
                "version": p.metadata.version,
                "status": p.status.name,
                "capabilities": [c.name for c in getattr(p.metadata, "capabilities", [])],
            }
            for p in plugins
        ]
    except Exception:
        return []


def _export_stats() -> dict[str, Any]:
    try:
        from duplicate_question_app._profiling import Profiler

        p = Profiler()
        stats = p.get_stats()
        return {
            "profiled_functions": len(stats),
            "total_calls": sum(s.call_count for s in stats.values()),
        }
    except Exception:
        return {}
