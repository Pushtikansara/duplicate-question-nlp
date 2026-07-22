from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from ares.cli.utils.console import console, exit_with_error, print_success
from ares.cli.utils.tables import print_table
from ares.plugins import (
    Plugin,
    PluginManager,
    PluginStatus,
)
from ares.plugins.exceptions import PluginNotFoundError, PluginValidationError


def _get_manager() -> PluginManager:
    pm = PluginManager()
    pm.load()
    return pm


def _get_output(plugin: Plugin) -> dict[str, Any]:
    meta = plugin.metadata
    return {
        "id": plugin.plugin_id,
        "name": meta.name,
        "version": meta.version,
        "status": plugin.status.name,
        "author": getattr(meta, "author", ""),
        "description": getattr(meta, "description", ""),
        "priority": meta.priority,
        "capabilities": [c.name for c in getattr(meta, "capabilities", [])],
    }


def list_plugins(
    status: str | None = None,
    verbose: bool = False,
) -> None:
    pm = _get_manager()
    plugins = pm.list()
    if status:
        try:
            target = PluginStatus[status.upper()]
            plugins = [p for p in plugins if p.status == target]
        except KeyError:
            exit_with_error(f"Invalid status: {status}")

    if not plugins:
        console.print("[yellow]No plugins found[/yellow]")
        return

    rows = []
    for p in plugins:
        meta = p.metadata
        caps = (
            ", ".join(c.name for c in getattr(meta, "capabilities", []))
            if verbose
            else str(len(getattr(meta, "capabilities", [])))
        )
        rows.append(
            [
                p.plugin_id,
                meta.version,
                p.status.name,
                caps,
            ]
        )

    print_table(
        "Installed Plugins",
        ["ID", "Version", "Status", "Capabilities"],
        rows,
    )


def install_plugin(
    plugin_path: str = typer.Argument(..., help="Path or module name of plugin"),
) -> None:
    path = Path(plugin_path)
    if not path.exists():
        exit_with_error(f"Plugin path not found: {plugin_path}")

    pm = _get_manager()
    try:
        from ares.plugins.discovery import discover_from_folder

        classes = discover_from_folder(path)
        if not classes:
            exit_with_error(f"No plugin classes found in {plugin_path}")

        for cls in classes:
            pm.install(cls)
            print_success(f"Installed plugin: {cls.__name__}")
    except PluginValidationError as e:
        exit_with_error(f"Plugin validation failed: {e}")
    except Exception as e:
        exit_with_error(f"Installation failed: {e}")


def uninstall_plugin(
    plugin_id: str = typer.Argument(..., help="Plugin ID to uninstall"),
    force: bool = typer.Option(False, "--force", "-f", help="Force uninstall without confirmation"),
) -> None:
    pm = _get_manager()

    if not force:
        from ares.cli.utils.console import console

        confirm = typer.confirm(f"Uninstall plugin '{plugin_id}'?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    try:
        pm.uninstall(plugin_id)
        print_success(f"Uninstalled plugin: {plugin_id}")
    except PluginNotFoundError:
        exit_with_error(f"Plugin not found: {plugin_id}")
    except Exception as e:
        exit_with_error(f"Uninstall failed: {e}")


def enable_plugin(
    plugin_id: str = typer.Argument(..., help="Plugin ID to enable"),
) -> None:
    pm = _get_manager()
    try:
        pm.enable(plugin_id)
        print_success(f"Enabled plugin: {plugin_id}")
    except PluginNotFoundError:
        exit_with_error(f"Plugin not found: {plugin_id}")


def disable_plugin(
    plugin_id: str = typer.Argument(..., help="Plugin ID to disable"),
) -> None:
    pm = _get_manager()
    try:
        pm.disable(plugin_id)
        print_success(f"Disabled plugin: {plugin_id}")
    except PluginNotFoundError:
        exit_with_error(f"Plugin not found: {plugin_id}")


def inspect_plugin(
    plugin_id: str = typer.Argument(..., help="Plugin ID to inspect"),
) -> None:
    pm = _get_manager()
    try:
        p = pm.get(plugin_id)
    except PluginNotFoundError:
        exit_with_error(f"Plugin not found: {plugin_id}")

    meta = p.metadata
    from ares.cli.utils.console import console
    from ares.cli.utils.tables import dict_table

    info = {
        "ID": p.plugin_id,
        "Name": meta.name,
        "Version": meta.version,
        "Status": p.status.name,
        "Author": getattr(meta, "author", "N/A"),
        "Description": getattr(meta, "description", "N/A"),
        "License": getattr(meta, "license", "N/A"),
        "Priority": str(meta.priority),
        "Capabilities": ", ".join(c.name for c in getattr(meta, "capabilities", [])),
        "Dependencies": ", ".join(d.plugin_id for d in getattr(meta, "dependencies", [])),
    }
    console.print(dict_table(f"Plugin: {plugin_id}", info))


def search_plugins(
    query: str = typer.Argument("", help="Search query"),
) -> None:
    pm = _get_manager()
    plugins = pm.list()
    if query:
        q = query.lower()
        plugins = [
            p
            for p in plugins
            if q in p.plugin_id.lower()
            or q in p.metadata.name.lower()
            or q in getattr(p.metadata, "description", "").lower()
        ]

    if not plugins:
        console.print(f"[yellow]No plugins matching '{query}'[/yellow]")
        return

    rows = []
    for p in plugins:
        rows.append(
            [
                p.plugin_id,
                p.metadata.version,
                p.status.name,
            ]
        )

    print_table(
        f"Plugins matching '{query}'",
        ["ID", "Version", "Status"],
        rows,
    )
