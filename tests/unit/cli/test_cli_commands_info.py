from __future__ import annotations

from ares.cli.commands.info import _get_system_info, info_cmd


class TestInfo:
    def test_get_system_info_keys(self):
        info = _get_system_info()
        assert "python_version" in info
        assert "platform" in info
        assert "cpu_count" in info
        assert "memory" in info
        assert "project_root" in info

    def test_get_system_info_values(self):
        info = _get_system_info()
        assert info["python_version"]
        assert info["platform"]
        assert int(info["cpu_count"]) > 0

    def test_info_cmd_output(self, capsys):
        info_cmd()
        captured = capsys.readouterr()
        assert "ARES System Information" in captured.out
        assert "Version:" in captured.out
        assert "Python:" in captured.out
        assert "CPU Cores:" in captured.out
        assert "Memory:" in captured.out
        assert "Project Root:" in captured.out
