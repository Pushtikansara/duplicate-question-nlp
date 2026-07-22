from __future__ import annotations

import sys
from unittest.mock import patch

from rich.console import Console

from ares.cli.utils.console import (
    console,
    error_console,
    exit_with_error,
    handle_cli_error,
    print_error,
    print_info,
    print_panel,
    print_success,
    print_warning,
)


class TestConsole:
    def test_console_is_rich_console(self):
        assert isinstance(console, Console)

    def test_error_console_is_rich_console(self):
        assert isinstance(error_console, Console)

    def test_print_info(self, capsys):
        print_info("hello")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_print_success(self, capsys):
        print_success("done")
        captured = capsys.readouterr()
        assert "done" in captured.out

    def test_print_warning(self, capsys):
        print_warning("warn")
        captured = capsys.readouterr()
        assert "warn" in captured.out

    def test_print_error(self, capsys):
        print_error("error msg")
        captured = capsys.readouterr()
        assert "error msg" in captured.err

    def test_print_panel(self, capsys):
        print_panel("Title", "Content", "info")
        captured = capsys.readouterr()
        assert "Content" in captured.out

    def test_exit_with_error(self):
        with patch.object(sys, "exit") as mock_exit:
            exit_with_error("fail")
            mock_exit.assert_called_once_with(1)

    def test_exit_with_error_custom_code(self):
        with patch.object(sys, "exit") as mock_exit:
            exit_with_error("fail", 42)
            mock_exit.assert_called_once_with(42)

    def test_handle_cli_error_success(self):
        @handle_cli_error
        def good():
            return 42

        assert good() == 42

    def test_handle_cli_error_failure(self):
        @handle_cli_error
        def bad():
            raise ValueError("boom")

        with patch.object(sys, "exit") as mock_exit:
            result = bad()
            assert result is None
            mock_exit.assert_called_once_with(1)

    def test_console_theme_has_custom_styles(self):
        from ares.cli.utils.console import custom_theme

        assert "info" in custom_theme.styles
        assert "success" in custom_theme.styles
        assert "error" in custom_theme.styles
        assert "warning" in custom_theme.styles
