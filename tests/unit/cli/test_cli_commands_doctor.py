from __future__ import annotations

import sys
from unittest.mock import patch

from ares.cli.commands.doctor import (
    _add_result,
    _check_cache,
    _check_config,
    _check_cpu,
    _check_dependencies,
    _check_disk_space,
    _check_gpu_cuda,
    _check_memory,
    _check_model_availability,
    _check_observability,
    _check_os,
    _check_paths,
    _check_plugins,
    _check_python,
    _check_torch,
    doctor_cmd,
)


class TestDoctor:
    def test_add_result(self):
        results: list[dict[str, str]] = []
        _add_result(results, "PASS", "check", "detail")
        assert len(results) == 1
        assert results[0]["status"] == "PASS"
        assert results[0]["check"] == "check"
        assert results[0]["detail"] == "detail"

    def test_check_python_pass(self):
        results: list[dict[str, str]] = []
        _check_python(results)
        assert results[0]["status"] == "PASS"

    def test_check_os(self):
        results: list[dict[str, str]] = []
        _check_os(results)
        assert results[0]["status"] == "PASS"

    def test_check_cpu(self):
        results: list[dict[str, str]] = []
        _check_cpu(results)
        assert results[0]["status"] in ("PASS", "WARN")

    def test_check_memory(self):
        results: list[dict[str, str]] = []
        _check_memory(results)
        assert results[0]["status"] in ("PASS", "WARN")

    def test_check_gpu_cuda(self):
        results: list[dict[str, str]] = []
        _check_gpu_cuda(results)
        assert len(results) > 0

    def test_check_torch(self):
        results: list[dict[str, str]] = []
        _check_torch(results)
        statuses = [r["status"] for r in results]
        assert all(s in ("PASS", "WARN", "FAIL") for s in statuses)

    def test_check_dependencies(self):
        results: list[dict[str, str]] = []
        _check_dependencies(results)
        deps_checked = {r["check"] for r in results}
        assert "torch" in deps_checked
        assert "transformers" in deps_checked
        assert "rich" in deps_checked
        assert "typer" in deps_checked

    def test_check_config(self):
        results: list[dict[str, str]] = []
        _check_config(results)
        assert results[0]["status"] in ("PASS", "FAIL")

    def test_check_paths(self):
        results: list[dict[str, str]] = []
        _check_paths(results)
        statuses = [r["status"] for r in results]
        assert all(s in ("PASS", "WARN", "FAIL") for s in statuses)

    def test_check_model_availability(self):
        results: list[dict[str, str]] = []
        _check_model_availability(results)
        assert len(results) >= 1

    def test_check_cache(self):
        results: list[dict[str, str]] = []
        _check_cache(results)
        statuses = [r["status"] for r in results]
        assert all(s in ("PASS", "WARN", "FAIL") for s in statuses)

    def test_check_disk_space(self):
        results: list[dict[str, str]] = []
        _check_disk_space(results)
        assert results[0]["status"] in ("PASS", "WARN")

    def test_check_plugins(self):
        results: list[dict[str, str]] = []
        _check_plugins(results)
        statuses = [r["status"] for r in results]
        assert all(s in ("PASS", "WARN") for s in statuses)

    def test_check_observability(self):
        results: list[dict[str, str]] = []
        _check_observability(results)
        statuses = [r["status"] for r in results]
        assert all(s in ("PASS", "WARN") for s in statuses)

    def test_doctor_cmd_output(self, capsys):
        with patch.object(sys, "exit"):
            doctor_cmd()
            captured = capsys.readouterr()
            assert "ARES Diagnostics" in captured.out
            assert "Diagnostic Results" in captured.out
            assert "Summary:" in captured.out

    def test_doctor_cmd_verbose(self, capsys):
        with patch.object(sys, "exit"):
            doctor_cmd(verbose=True)
            captured = capsys.readouterr()
            assert "ARES Diagnostics" in captured.out

    def test_doctor_cmd_verbose_adds_observability(self, capsys):
        with patch.object(sys, "exit"):
            doctor_cmd(verbose=True)
            captured = capsys.readouterr()
            assert "Summary:" in captured.out
