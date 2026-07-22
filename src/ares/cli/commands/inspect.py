from __future__ import annotations

from pathlib import Path

from ares.cli.utils.console import console, exit_with_error
from ares.cli.utils.tables import dict_table


def inspect_cmd() -> None:
    try:
        from duplicate_question_app._config.settings import (
            MODEL_CHOICES,
            get_app_paths,
            resolve_model_selection,
        )

        paths = get_app_paths()
        resolution = resolve_model_selection(paths)

        console.print("[bold cyan]ARES System Inspection[/bold cyan]")
        console.print()

        model_info = {
            "Selected Model": resolution.selected_label,
            "Week 4 Ready": "Yes" if resolution.week4.ready else "No",
            "Week 4 Model Dir": str(resolution.week4.model_dir),
            "Week 3 Ready": "Yes" if resolution.week3.ready else "No",
            "Week 3 Model Dir": str(resolution.week3.model_dir),
            "Available Models": str(len(MODEL_CHOICES)),
        }
        console.print(dict_table("Model Status", model_info))

        dir_info = {
            "Project Root": str(paths.project_root),
            "Data Dir": str(paths.data_dir),
            "Models Dir": str(paths.models_dir),
            "Results Dir": str(paths.results_dir),
            "Config Dir": str(Path(paths.project_root) / "configs"),
            "Logs Dir": str(Path(paths.project_root) / "logs"),
        }
        console.print(dict_table("Paths", dir_info))

    except Exception as e:
        exit_with_error(f"Inspection failed: {e}")
