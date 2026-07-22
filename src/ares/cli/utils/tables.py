from __future__ import annotations

from typing import Any

from rich.table import Table
from rich.tree import Tree

from ares.cli.utils.console import console


def create_table(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
    styles: list[str] | None = None,
) -> Table:
    table = Table(title=title, title_style="bold cyan", border_style="blue")
    for i, col in enumerate(columns):
        style = styles[i] if styles else None
        table.add_column(col, style=style)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    return table


def print_table(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
    styles: list[str] | None = None,
) -> None:
    table = create_table(title, columns, rows, styles)
    console.print(table)


def dict_table(title: str, data: dict[str, Any], key_style: str = "cyan") -> Table:
    table = Table(title=title, title_style="bold cyan", border_style="blue")
    table.add_column("Key", style=key_style)
    table.add_column("Value")
    for k, v in data.items():
        table.add_row(str(k), str(v))
    return table


def create_tree(label: str, children: dict[str, Any] | None = None) -> Tree:
    tree = Tree(label)
    if children:
        _populate_tree(tree, children)
    return tree


def _populate_tree(tree: Tree, data: dict[str, Any]) -> None:
    for key, value in data.items():
        if isinstance(value, dict):
            branch = tree.add(f"[bold]{key}[/bold]")
            _populate_tree(branch, value)
        else:
            tree.add(f"{key}: {value}")
