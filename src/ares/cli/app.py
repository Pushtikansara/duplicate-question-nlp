from __future__ import annotations

from typing import Any

import typer

from ares.cli.commands import benchmark as benchmark_cmd
from ares.cli.commands import config as config_cmd
from ares.cli.commands import doctor as doctor_cmd
from ares.cli.commands import export as export_cmd
from ares.cli.commands import info as info_cmd
from ares.cli.commands import inspect as inspect_cmd
from ares.cli.commands import memory as memory_cmd
from ares.cli.commands import pipeline as pipeline_cmd
from ares.cli.commands import plugin as plugin_cmd
from ares.cli.commands import predict as predict_cmd
from ares.cli.commands import profile as profile_cmd
from ares.cli.commands import serve as serve_cmd
from ares.cli.commands import shell as shell_cmd
from ares.cli.commands import trace as trace_cmd
from ares.cli.commands import version as version_cmd
from ares.cli.utils.output import OutputFormat, OutputHandler

CONTEXT_SETTINGS = {
    "help_option_names": ["--help", "-h"],
}

app = typer.Typer(
    name="ares",
    help="ARES - Advanced Reasoning Engine for Semantic Understanding",
    rich_markup_mode="rich",
    no_args_is_help=True,
    context_settings=CONTEXT_SETTINGS,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=True,
)

_state: dict[str, Any] = {
    "verbose": False,
    "debug": False,
    "quiet": False,
    "output_format": OutputFormat.TEXT,
}


def _get_output_handler() -> OutputHandler:
    return OutputHandler(
        format=_state["output_format"],
        verbose=_state["verbose"],
        quiet=_state["quiet"],
    )


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output"),
    output: str = typer.Option(
        "text",
        "--output",
        "-o",
        help="Output format (text, json, yaml)",
    ),
) -> None:
    _state["verbose"] = verbose
    _state["debug"] = debug
    _state["quiet"] = quiet
    _state["output_format"] = OutputFormat(output)


app.command(name="version")(version_cmd.version_cmd)
app.command(name="info")(info_cmd.info_cmd)
app.command(name="doctor")(doctor_cmd.doctor_cmd)
app.command(
    name="status",
    help="Alias for `ares info`",
)(info_cmd.info_cmd)

plugin_typer = typer.Typer(name="plugin", help="Manage plugins", no_args_is_help=True, rich_markup_mode="rich")
plugin_typer.command(name="list")(plugin_cmd.list_plugins)
plugin_typer.command(name="install")(plugin_cmd.install_plugin)
plugin_typer.command(name="uninstall")(plugin_cmd.uninstall_plugin)
plugin_typer.command(name="enable")(plugin_cmd.enable_plugin)
plugin_typer.command(name="disable")(plugin_cmd.disable_plugin)
plugin_typer.command(name="inspect")(plugin_cmd.inspect_plugin)
plugin_typer.command(name="search")(plugin_cmd.search_plugins)
app.add_typer(plugin_typer)

trace_typer = typer.Typer(name="trace", help="Manage traces", no_args_is_help=True, rich_markup_mode="rich")
trace_typer.command(name="run")(trace_cmd.run_trace)
trace_typer.command(name="inspect")(trace_cmd.inspect_trace)
trace_typer.command(name="export")(trace_cmd.export_trace)
trace_typer.command(name="replay")(trace_cmd.replay_trace)
app.add_typer(trace_typer)

benchmark_typer = typer.Typer(name="benchmark", help="Run benchmarks", no_args_is_help=True, rich_markup_mode="rich")
benchmark_typer.command(name="run")(benchmark_cmd.run_benchmark)
benchmark_typer.command(name="list")(benchmark_cmd.list_benchmarks)
benchmark_typer.command(name="compare")(benchmark_cmd.compare_benchmarks)
app.add_typer(benchmark_typer)

app.command(name="profile")(profile_cmd.generate_profile)

metrics_typer = typer.Typer(name="metrics", help="View metrics", no_args_is_help=True, rich_markup_mode="rich")
metrics_typer.command(name="show")(profile_cmd.show_metrics)
metrics_typer.command(name="export")(profile_cmd.export_metrics)
app.add_typer(metrics_typer)

stats_typer = typer.Typer(name="stats", help="View statistics", no_args_is_help=True, rich_markup_mode="rich")
stats_typer.command(name="show")(profile_cmd.show_stats)
stats_typer.command(name="export")(profile_cmd.export_stats)
app.add_typer(stats_typer)

config_typer = typer.Typer(name="config", help="Manage configuration", no_args_is_help=True, rich_markup_mode="rich")
config_typer.command(name="show")(config_cmd.show_config)
config_typer.command(name="edit")(config_cmd.edit_config)
config_typer.command(name="validate")(config_cmd.validate_config)
config_typer.command(name="export")(config_cmd.export_config)
app.add_typer(config_typer)

memory_typer = typer.Typer(name="memory", help="Manage memory", no_args_is_help=True, rich_markup_mode="rich")
memory_typer.command(name="list")(memory_cmd.list_memory)
memory_typer.command(name="search")(memory_cmd.search_memory)
memory_typer.command(name="stats")(memory_cmd.memory_stats)
memory_typer.command(name="clean")(memory_cmd.clean_memory)
app.add_typer(memory_typer)

pipeline_typer = typer.Typer(name="pipeline", help="Manage pipelines", no_args_is_help=True, rich_markup_mode="rich")
pipeline_typer.command(name="inspect")(pipeline_cmd.inspect_pipeline)
pipeline_typer.command(name="graph")(pipeline_cmd.graph_pipeline)
pipeline_typer.command(name="run")(pipeline_cmd.run_pipeline)
app.add_typer(pipeline_typer)

app.command(name="serve")(serve_cmd.start_server)
app.command(name="shell")(shell_cmd.start_shell)
app.command(name="predict")(predict_cmd.predict)
app.command(name="export")(export_cmd.export_cmd)
app.command(name="inspect")(inspect_cmd.inspect_cmd)

cli = app
