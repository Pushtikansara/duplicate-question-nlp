from __future__ import annotations

from unittest.mock import MagicMock

import typer

from ares.cli import app, cli
from ares.cli.app import (
    CONTEXT_SETTINGS,
    _get_output_handler,
    _state,
    main_callback,
)
from ares.cli.utils.output import OutputFormat, OutputHandler


class TestApp:
    def test_app_is_typer(self):
        assert isinstance(app, typer.Typer)

    def test_cli_is_app(self):
        assert cli is app

    def test_app_name(self):
        assert app.info.name == "ares"

    def test_app_has_commands(self):
        commands = [c.name for c in app.registered_commands]
        for cmd in ["version", "info", "doctor", "status", "profile", "serve", "shell", "predict"]:
            assert cmd in commands

    def test_app_has_typer_groups(self):
        groups = [g.typer_instance.info.name for g in app.registered_groups if g.typer_instance]
        for group in ["plugin", "trace", "benchmark", "metrics", "stats", "config", "memory", "pipeline"]:
            assert group in groups

    def test_context_settings(self):
        assert "--help" in CONTEXT_SETTINGS["help_option_names"]
        assert "-h" in CONTEXT_SETTINGS["help_option_names"]

    def test_main_callback_sets_state(self):
        ctx = MagicMock()
        main_callback(ctx, verbose=True, debug=False, quiet=False, output="json")
        assert _state["verbose"] is True
        assert _state["debug"] is False
        assert _state["quiet"] is False
        assert _state["output_format"] == OutputFormat.JSON

    def test_main_callback_defaults(self):
        ctx = MagicMock()
        main_callback(ctx, verbose=False, debug=False, quiet=False, output="text")
        assert _state["verbose"] is False
        assert _state["output_format"] == OutputFormat.TEXT

    def test_main_callback_quiet(self):
        ctx = MagicMock()
        main_callback(ctx, verbose=False, debug=False, quiet=True, output="text")
        assert _state["quiet"] is True

    def test_main_callback_debug(self):
        ctx = MagicMock()
        main_callback(ctx, verbose=False, debug=True, quiet=False, output="text")
        assert _state["debug"] is True

    def test_get_output_handler(self):
        handler = _get_output_handler()
        assert isinstance(handler, OutputHandler)

    def test_get_output_handler_verbose(self):
        _state["verbose"] = True
        _state["output_format"] = OutputFormat.TEXT
        handler = _get_output_handler()
        assert handler.verbose is True

    def test_get_output_handler_json(self):
        _state["verbose"] = False
        _state["output_format"] = OutputFormat.JSON
        handler = _get_output_handler()
        assert handler.is_json

    def test_get_output_handler_quiet(self):
        _state["quiet"] = True
        handler = _get_output_handler()
        assert handler.quiet is True

    def test_no_args_is_help(self):
        assert app.info.no_args_is_help is True

    def test_pretty_exceptions_enabled(self):
        assert app.pretty_exceptions_enable is True
