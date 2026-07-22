from __future__ import annotations

import typer

from ares.cli.utils.console import console, exit_with_error, print_success
from ares.cli.utils.formatting import format_timestamp
from ares.cli.utils.tables import print_table


def _get_memory_manager():
    try:
        from duplicate_question_app._memory.memory_manager import MemoryManager

        return MemoryManager()
    except ImportError:
        exit_with_error("MemoryManager not available")


def list_memory(
    memory_type: str | None = typer.Option(None, "--type", "-t", help="Filter by memory type"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max entries to show"),
) -> None:
    mm = _get_memory_manager()

    try:
        entries = mm.search_by_type(memory_type.upper()) if memory_type else mm.search("")
    except Exception:
        console.print("[yellow]No memory entries available[/yellow]")
        return

    if not entries:
        console.print("[yellow]No memory entries found[/yellow]")
        return

    rows = []
    for e in entries[:limit]:
        mem_type = getattr(e, "memory_type", getattr(e, "type", "unknown"))
        timestamp = format_timestamp(getattr(e, "timestamp", None))
        summary = str(getattr(e, "content", getattr(e, "summary", "")))[:60]
        rows.append(
            [
                getattr(e, "id", getattr(e, "entry_id", "?")),
                str(mem_type),
                timestamp,
                summary,
            ]
        )

    print_table(
        f"Memory Entries (showing {min(len(entries), limit)} of {len(entries)})",
        ["ID", "Type", "Timestamp", "Summary"],
        rows,
    )


def search_memory(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
) -> None:
    mm = _get_memory_manager()

    try:
        entries = mm.search_text(query)
    except Exception:
        try:
            entries = mm.search(query)
        except Exception as e:
            exit_with_error(f"Search failed: {e}")

    if not entries:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        return

    rows = []
    for entry in entries[:limit]:
        timestamp = format_timestamp(getattr(entry, "timestamp", None))
        summary = str(getattr(entry, "content", getattr(entry, "summary", "")))[:60]
        rows.append(
            [
                getattr(entry, "id", getattr(entry, "entry_id", "?")),
                timestamp,
                summary,
            ]
        )

    print_table(
        f"Search results for '{query}'",
        ["ID", "Timestamp", "Content"],
        rows,
    )


def memory_stats() -> None:
    mm = _get_memory_manager()

    try:
        stats = mm.get_statistics()
    except Exception as e:
        exit_with_error(f"Failed to get memory stats: {e}")

    rows = []
    if isinstance(stats, dict):
        for key, value in stats.items():
            rows.append([str(key), str(value)])
    else:
        for key, value in vars(stats).items():
            if not key.startswith("_"):
                rows.append([key.replace("_", " ").title(), str(value)])

    print_table(
        "Memory Statistics",
        ["Metric", "Value"],
        rows,
    )


def clean_memory(
    memory_type: str | None = typer.Option(None, "--type", "-t", help="Memory type to clean"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    if not force:
        confirm = typer.confirm("This will clean memory entries. Continue?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    mm = _get_memory_manager()

    try:
        result = mm.consolidate(memory_type.upper()) if memory_type else mm.consolidate()
        print_success(f"Memory cleaned: {result}")
    except Exception as e:
        exit_with_error(f"Memory clean failed: {e}")
