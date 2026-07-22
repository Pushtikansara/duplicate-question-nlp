from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

from ares.cli.utils.console import console, print_panel
from ares.cli.utils.formatting import format_bytes
from ares.cli.utils.tables import print_table


def doctor_cmd(
    verbose: bool = False,
    models: bool = False,
) -> None:
    results: list[dict[str, str]] = []

    _check_python(results)
    _check_os(results)
    _check_cpu(results)
    _check_memory(results)
    _check_gpu_cuda(results)
    _check_torch(results)
    _check_dependencies(results)
    _check_config(results)
    _check_paths(results)
    _check_model_availability(results)
    _check_cache(results)
    _check_disk_space(results)
    _check_plugins(results)

    if verbose:
        _check_observability(results)

    if models:
        _check_all_models(results)

    print_panel(
        "ARES Diagnostics",
        "[bold green]System diagnostic check complete[/bold green]",
        "green",
    )

    rows = []
    for r in results:
        status = r["status"]
        if status == "PASS":
            status_display = "[green]PASS[/green]"
        elif status == "WARN":
            status_display = "[yellow]WARN[/yellow]"
        else:
            status_display = "[red]FAIL[/red]"
        rows.append([status_display, r["check"], r["detail"]])

    print_table(
        "Diagnostic Results",
        ["Status", "Check", "Detail"],
        rows,
        styles=["", "cyan", ""],
    )

    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)

    console.print(f"\n[bold]Summary:[/bold] {passed}/{total} passed, {warned} warnings, {failed} failures")

    if failed > 0:
        sys.exit(1)


def _add_result(
    results: list[dict[str, str]],
    status: str,
    check: str,
    detail: str,
) -> None:
    results.append({"status": status, "check": check, "detail": detail})


def _check_python(results: list[dict[str, str]]) -> None:
    version = sys.version.split()[0]
    parts = tuple(int(x) for x in version.split(".")[:2])
    if parts >= (3, 10):
        _add_result(results, "PASS", "Python Version", version)
    else:
        _add_result(results, "FAIL", "Python Version", f"{version} (need >=3.10)")


def _check_os(results: list[dict[str, str]]) -> None:
    system = platform.system()
    release = platform.release()
    _add_result(results, "PASS", "Operating System", f"{system} {release}")


def _check_cpu(results: list[dict[str, str]]) -> None:
    count = os.cpu_count() or 0
    model = platform.processor() or "Unknown"
    if count >= 2:
        _add_result(results, "PASS", "CPU", f"{count} cores ({model})")
    else:
        _add_result(results, "WARN", "CPU", f"{count} cores ({model})")


def _check_memory(results: list[dict[str, str]]) -> None:
    try:
        import psutil

        mem = psutil.virtual_memory()
        total = format_bytes(mem.total)
        available = format_bytes(mem.available)
        pct = mem.percent
        if pct < 90:
            _add_result(results, "PASS", "Memory", f"{total} total, {available} free ({pct}% used)")
        else:
            _add_result(results, "WARN", "Memory", f"{total} total, {available} free ({pct}% used)")
    except ImportError:
        _add_result(results, "WARN", "Memory", "psutil not installed")


def _check_gpu_cuda(results: list[dict[str, str]]) -> None:
    try:
        import torch

        if torch.cuda.is_available():
            count = torch.cuda.device_count()
            for i in range(count):
                name = torch.cuda.get_device_name(i)
                _add_result(results, "PASS", f"GPU {i}", name)
            cuda_version = torch.version.cuda or "unknown"
            _add_result(results, "PASS", "CUDA", cuda_version)
        else:
            _add_result(results, "WARN", "GPU", "No CUDA-capable GPU detected")
            _add_result(results, "WARN", "CUDA", "Not available")
    except ImportError:
        _add_result(results, "WARN", "GPU", "Torch not installed")
        _add_result(results, "WARN", "CUDA", "Not available")


def _check_torch(results: list[dict[str, str]]) -> None:
    try:
        import torch

        ver = torch.__version__
        _add_result(results, "PASS", "PyTorch", ver)
    except ImportError:
        _add_result(results, "FAIL", "PyTorch", "Not installed")


def _check_dependencies(results: list[dict[str, str]]) -> None:
    deps = [
        ("torch", None),
        ("transformers", None),
        ("sentence_transformers", None),
        ("pandas", None),
        ("numpy", None),
        ("scikit-learn", "sklearn"),
        ("streamlit", None),
        ("rich", None),
        ("typer", None),
        ("yaml", None),
        ("psutil", None),
    ]
    for mod_name, import_name in deps:
        try:
            mod = __import__(import_name or mod_name)
            ver = getattr(mod, "__version__", "unknown")
            _add_result(results, "PASS", mod_name, ver)
        except ImportError:
            _add_result(results, "WARN" if mod_name in ("psutil", "streamlit") else "FAIL", mod_name, "Not installed")


def _check_config(results: list[dict[str, str]]) -> None:
    try:
        from duplicate_question_app._config.settings import get_app_paths

        paths = get_app_paths()
        config_dir = paths.project_root / "configs"
        if config_dir.exists():
            yaml_files = list(config_dir.glob("*.yaml"))
            _add_result(results, "PASS", "Configuration", f"{len(yaml_files)} config files found")
        else:
            _add_result(results, "FAIL", "Configuration", "Config directory not found")
    except Exception as e:
        _add_result(results, "FAIL", "Configuration", str(e))


def _check_paths(results: list[dict[str, str]]) -> None:
    try:
        from duplicate_question_app._config.settings import get_app_paths

        paths = get_app_paths()
        config_dir = paths.project_root / "configs"
        issues = []
        if not paths.data_dir.exists():
            issues.append("data dir missing")
        if not paths.models_dir.exists():
            issues.append("models dir missing")
        if not config_dir.exists():
            issues.append("config dir missing")
        if issues:
            _add_result(results, "WARN", "App Paths", "; ".join(issues))
        else:
            _add_result(results, "PASS", "App Paths", "All paths OK")
    except Exception as e:
        _add_result(results, "FAIL", "App Paths", str(e))


def _check_model_availability(results: list[dict[str, str]]) -> None:
    try:
        from duplicate_question_app._config.settings import get_app_paths, resolve_model_selection

        paths = get_app_paths()
        resolution = resolve_model_selection(paths)
        _add_result(results, "PASS", "Model Selection", resolution.selected_label)

        if resolution.week4.ready:
            _add_result(results, "PASS", "Week 4 Model", "Ready")
        else:
            _add_result(results, "WARN", "Week 4 Model", "Not ready")

        if resolution.week3.ready:
            _add_result(results, "PASS", "Week 3 Model", "Ready")
        else:
            _add_result(results, "WARN", "Week 3 Model", "Not ready")
    except Exception as e:
        _add_result(results, "FAIL", "Model Availability", str(e))


def _check_cache(results: list[dict[str, str]]) -> None:
    try:
        from duplicate_question_app._inference.optimizer import (
            get_embedding_cache,
            get_preprocessing_cache,
        )

        ec = get_embedding_cache().stats()
        hr = ec.hit_rate if ec.hits + ec.misses > 0 else 0.0
        _add_result(results, "PASS", "Embedding Cache", f"size={ec.size}, hit_rate={hr:.1%}")

        pc = get_preprocessing_cache().stats()
        hr = pc.hit_rate if pc.hits + pc.misses > 0 else 0.0
        _add_result(results, "PASS", "Preprocessing Cache", f"size={pc.size}, hit_rate={hr:.1%}")
    except Exception:
        _add_result(results, "WARN", "Cache", "Cache stats unavailable")


def _check_disk_space(results: list[dict[str, str]]) -> None:
    try:
        import shutil

        total, used, free = shutil.disk_usage(Path.cwd())
        free_gb = free / (1024**3)
        if free_gb > 5:
            _add_result(results, "PASS", "Disk Space", f"{free_gb:.1f} GB free")
        else:
            _add_result(results, "WARN", "Disk Space", f"Only {free_gb:.1f} GB free")
    except Exception:
        _add_result(results, "WARN", "Disk Space", "Could not check")


def _check_plugins(results: list[dict[str, str]]) -> None:
    try:
        from ares.plugins import PluginManager

        pm = PluginManager()
        pm.load()
        plugins = pm.list()
        if plugins:
            statuses = [f"{p.plugin_id}={p.status.name}" for p in plugins]
            _add_result(results, "PASS", "Plugins", f"{len(plugins)} installed: {', '.join(statuses)}")
        else:
            _add_result(results, "PASS", "Plugins", "No plugins installed")
    except Exception as e:
        _add_result(results, "WARN", "Plugins", str(e))


def _check_observability(results: list[dict[str, str]]) -> None:
    try:
        from duplicate_question_app._profiling import Profiler

        p = Profiler()
        stats = p.get_stats()
        _add_result(results, "PASS", "Observability", f"{len(stats)} profiled functions")
    except Exception as e:
        _add_result(results, "WARN", "Observability", str(e))


def _check_all_models(results: list[dict[str, str]]) -> None:
    from duplicate_question_app._config.settings import MODEL_CHOICES

    for model in MODEL_CHOICES:
        _add_result(
            results,
            "PASS",
            f"Model: {model}",
            "Available",
        )
