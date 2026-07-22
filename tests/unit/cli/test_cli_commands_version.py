from __future__ import annotations

from ares.cli.commands.version import get_version_info, version_cmd


class TestVersion:
    def test_get_version_info(self):
        info = get_version_info()
        assert "ares" in info
        assert "python" in info
        assert "platform" in info
        assert info["ares"] == "0.2.0"

    def test_version_cmd_output(self, capsys):
        version_cmd()
        captured = capsys.readouterr()
        assert "ARES version:" in captured.out
        assert "0.2.0" in captured.out
        assert "Python:" in captured.out
        assert "Platform:" in captured.out

    def test_version_cmd_contains_python_version(self, capsys):
        import sys

        version_cmd()
        captured = capsys.readouterr()
        assert sys.version.split()[0] in captured.out
