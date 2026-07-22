from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ares.cli.utils.console import console, print_error
from ares.cli.utils.formatting import output_result, save_output


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"


@dataclass
class OutputHandler:
    format: OutputFormat = OutputFormat.TEXT
    verbose: bool = False
    quiet: bool = False

    def print(self, data: Any, file: str | None = None) -> None:
        if self.quiet:
            return
        if file:
            out_path = Path(file)
            save_output(data, out_path, self.format.value)
            console.print(f"[dim]Output saved to {out_path.resolve()}[/dim]")
            return
        output = output_result(data, self.format.value)
        console.print(output)

    def print_error(self, message: str) -> None:
        print_error(message)

    def print_info(self, message: str) -> None:
        if not self.quiet:
            console.print(message, style="info")

    def print_success(self, message: str) -> None:
        if not self.quiet:
            console.print(message, style="success")

    def print_table(self, title: str, columns: list[str], rows: list[list[Any]]) -> None:
        if self.quiet:
            return
        if self.format != OutputFormat.TEXT:
            data = [dict(zip(columns, row, strict=False)) for row in rows]
            self.print({title: data})
            return
        from ares.cli.utils.tables import print_table

        print_table(title, columns, rows)

    def print_dict(self, title: str, data: dict[str, Any]) -> None:
        if self.quiet:
            return
        if self.format != OutputFormat.TEXT:
            self.print(data)
            return
        from ares.cli.utils.tables import dict_table

        console.print(dict_table(title, data))

    @property
    def is_json(self) -> bool:
        return self.format == OutputFormat.JSON

    @property
    def is_yaml(self) -> bool:
        return self.format == OutputFormat.YAML

    @property
    def is_text(self) -> bool:
        return self.format == OutputFormat.TEXT
