from __future__ import annotations

from unittest.mock import MagicMock, patch

from ares.cli.commands.shell import start_shell


class TestShell:
    def test_start_shell(self):
        with patch("code.InteractiveConsole") as mock_console:
            instance = MagicMock()
            mock_console.return_value = instance
            start_shell()
            mock_console.assert_called_once()
            instance.interact.assert_called_once()

    def test_shell_banner(self, capsys):
        with patch("code.InteractiveConsole") as mock_console:
            instance = MagicMock()
            mock_console.return_value = instance
            start_shell()
            captured = capsys.readouterr()
            assert "ARES Interactive Shell" in captured.out
            assert "ARES" in captured.out

    def test_shell_namespace(self):
        with patch("code.InteractiveConsole") as mock_console:
            instance = MagicMock()
            mock_console.return_value = instance
            start_shell()
            namespace = mock_console.call_args[0][0]
            assert "ARES" in namespace
            assert "PredictionResult" in namespace

    def test_shell_readline_import(self):
        with patch("code.InteractiveConsole") as mock_console:
            instance = MagicMock()
            mock_console.return_value = instance
            with patch("builtins.__import__"):
                start_shell()
                assert True
