"""Command-line interface for Duplicate Question Detection.

Usage:
    dqd             Show available commands
    dqd-app         Launch the Streamlit dashboard
    dqd-predict     Run prediction on a CSV file
    dqd-benchmark   Run model benchmarks
    dqd doctor      Run system diagnostics
    dqd health      Quick health check
    dqd validate    Validate configuration and paths
    dqd config      Show current configuration
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _ensure_project_root() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    os.chdir(root)
    return root


def run_app() -> None:
    """Launch the Streamlit dashboard."""
    _ensure_project_root()
    import subprocess

    app_path = Path(__file__).resolve().parent.parent.parent / "app" / "app.py"
    if not app_path.exists():
        print(f"Error: app.py not found at {app_path}")
        sys.exit(1)

    print(f"Starting Streamlit dashboard from {app_path}...")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    subprocess.run(cmd)


def predict() -> None:
    """Run prediction on a CSV file using selected model (CLI wrapper)."""
    _ensure_project_root()
    parser = argparse.ArgumentParser(description="Predict duplicates in a CSV file")
    parser.add_argument("input_csv", type=str, help="Path to input CSV with question1, question2 columns")
    parser.add_argument("--output", "-o", type=str, default=None, help="Path to output CSV")
    parser.add_argument("--model", "-m", type=str, default=None, help="Model name to use")
    parser.add_argument("--threshold", "-t", type=float, default=None, help="Decision threshold")
    args = parser.parse_args()

    import pandas as pd

    from duplicate_question_app.config import get_app_paths, get_config
    from duplicate_question_app.utils.device import resolve_device
    from duplicate_question_app.week2_inference import is_week2_model

    paths = get_app_paths()
    device = resolve_device()
    input_path = Path(args.input_csv)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    required_cols = {"question1", "question2", "q1", "q2"}
    if not required_cols.intersection(df.columns):
        print(f"Error: input CSV must contain one of {required_cols} columns")
        sys.exit(1)

    q1_col = "question1" if "question1" in df.columns else "q1"
    q2_col = "question2" if "question2" in df.columns else "q2"

    model_name = args.model or get_config("app").get("default_model", "Improved DistilBERT (Week 4)")
    threshold = args.threshold or get_config("inference").get("default_threshold", 0.5)

    from duplicate_question_app._config.logging_setup import get_logger

    logger = get_logger("cli.predict")
    logger.info("Predicting with model=%s threshold=%.2f device=%s", model_name, threshold, device)

    if is_week2_model(model_name):
        from duplicate_question_app.week2_inference import Week2InferenceService

        service = Week2InferenceService(paths)
    else:
        from duplicate_question_app.inference import DuplicateQuestionInferenceService, load_model_and_tokenizer

        model, tokenizer, metadata = load_model_and_tokenizer(paths, model_version=model_name)
        service = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)

    results = []
    for _, row in df.iterrows():
        result = service.predict_single(row[q1_col], row[q2_col])
        results.append(result)

    result_df = pd.DataFrame(results)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        print(f"Predictions saved to {output_path}")
    else:
        result_df.to_csv(input_path.parent / f"{input_path.stem}_predictions.csv", index=False)
        print(f"Predictions saved to {input_path.parent / f'{input_path.stem}_predictions.csv'}")

    acc = None
    if "label" in df.columns:
        correct = (result_df["predicted_label"] == df["label"]).sum()
        acc = correct / len(df)
        print(f"Accuracy: {acc:.4f}")

    print(f"Processed {len(df)} pairs with {model_name}")


def benchmark() -> None:
    """Run model benchmarks from the command line."""
    _ensure_project_root()
    from duplicate_question_app._config.logging_setup import configure_logging, get_logger

    configure_logging()
    logger = get_logger("cli.benchmark")
    logger.info("Benchmark command invoked")

    benchmark_script = Path(__file__).resolve().parent.parent.parent / "tools" / "ultimate_benchmark.py"
    if not benchmark_script.exists():
        logger.error("Benchmark script not found at %s", benchmark_script)
        sys.exit(1)

    import subprocess

    cmd = [sys.executable, str(benchmark_script)] + sys.argv[2:]
    subprocess.run(cmd)


def main() -> None:
    """Main entry point: display available commands."""
    _ensure_project_root()
    from duplicate_question_app import __version__

    parser = argparse.ArgumentParser(description="Duplicate Question Detection CLI")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["doctor", "health", "validate", "config", "runtime"],
        help="Diagnostic command (leave empty for help)",
    )
    parser.add_argument("--models", action="store_true", help="Include model diagnostics")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args, _ = parser.parse_known_args()

    if args.command == "doctor":
        _run_doctor(models=args.models, verbose=args.verbose)
        return
    if args.command == "health":
        _run_health()
        return
    if args.command == "validate":
        _run_validate()
        return
    if args.command == "config":
        _run_config(verbose=args.verbose)
        return
    if args.command == "runtime":
        _run_runtime_diagnostics()
        return

    # Default: show help
    print(f"Duplicate Question Detection v{__version__}")
    print()
    print("Available commands:")
    print("  dqd           Show this help")
    print("  dqd-app       Launch the Streamlit dashboard")
    print("  dqd-predict   Predict duplicates in a CSV file")
    print("  dqd-benchmark Run model benchmarks")
    print("  dqd doctor    Run system diagnostics")
    print("  dqd health    Quick health check")
    print("  dqd validate  Validate configuration and paths")
    print("  dqd config    Show current configuration")
    print()
    print("Diagnostic examples:")
    print("  dqd doctor             Full system diagnostics")
    print("  dqd doctor --models    Include model status")
    print("  dqd health             Quick health check")
    print("  dqd validate           Validate config and paths")
    print("  dqd config             Show effective configuration")
    print()
    print("Prediction examples:")
    print("  dqd-predict data/test.csv --model 'Cross-Encoder-Quora (Trained)' -o predictions.csv")
    print()


# ---------------------------------------------------------------------------
# Diagnostic commands
# ---------------------------------------------------------------------------


def _run_doctor(models: bool = False, verbose: bool = False) -> None:
    """Run system diagnostics.

    Reports:
    - Python version and environment
    - Configuration status (config directory, YAML files)
    - Path status (data, models, results)
    - Model availability
    - Dependency versions
    - Cache status
    """
    from duplicate_question_app._config.logging_setup import configure_logging, get_logger
    from duplicate_question_app._config.settings import get_app_paths

    configure_logging()
    logger = get_logger("cli.doctor")

    print("=" * 60)
    print("  Duplicate Question Detection — System Diagnostics")
    print("=" * 60)

    # Python environment
    print()
    print("[1/6] Python Environment")
    print(f"  Python:       {sys.version.split()[0]}")
    print(f"  Executable:   {sys.executable}")
    print(f"  Platform:     {sys.platform}")
    print(f"  Project Root: {_ensure_project_root()}")

    # Configuration
    print()
    print("[2/6] Configuration")
    config_dir = _ensure_project_root() / "configs"
    print(f"  Config dir:   {config_dir}")
    print(f"  Config exists: {'Yes' if config_dir.exists() else 'No'}")
    if config_dir.exists():
        for yaml_file in sorted(config_dir.glob("*.yaml")):
            print(f"    - {yaml_file.name}")

    # Paths
    print()
    print("[3/6] Application Paths")
    try:
        paths = get_app_paths()
        print(f"  Data dir:     {paths.data_dir}  {'Exists' if paths.data_dir.exists() else 'Missing'}")
        print(f"  Models dir:   {paths.models_dir}  {'Exists' if paths.models_dir.exists() else 'Missing'}")
        print(f"  Results dir:  {paths.results_dir}  {'Exists' if paths.results_dir.exists() else 'Missing'}")
    except Exception as exc:
        print(f"  Error loading paths: {exc}")

    # Model status
    if models or verbose:
        print()
        print("[4/6] Model Status")
        try:
            from duplicate_question_app._config.settings import get_app_paths, resolve_model_selection

            paths = get_app_paths()
            resolution = resolve_model_selection(paths)
            print(f"  Week 4 model:  {'Ready' if resolution.week4.ready else 'Not ready'}")
            if not resolution.week4.ready and resolution.week4.issues:
                for issue in resolution.week4.issues:
                    print(f"    - {issue}")
            print(f"  Week 3 model:  {'Ready' if resolution.week3.ready else 'Not ready'}")
            if not resolution.week3.ready and resolution.week3.issues:
                for issue in resolution.week3.issues:
                    print(f"    - {issue}")
            print(f"  Selected:      {resolution.selected_label}")
        except Exception as exc:
            print(f"  Error checking models: {exc}")
    else:
        print()
        print("[4/6] Model Status  (use --models for detailed model check)")
        try:
            from duplicate_question_app._config.settings import get_app_paths, resolve_model_selection

            paths = get_app_paths()
            resolution = resolve_model_selection(paths)
            print(f"  Selected:      {resolution.selected_label}")
        except Exception:
            print("  Models:        Not checked")

    # Dependencies
    if verbose:
        print()
        print("[5/6] Key Dependencies")
        deps = [
            ("torch", None),
            ("transformers", None),
            ("sentence_transformers", None),
            ("pandas", None),
            ("numpy", None),
            ("sklearn", None),
            ("streamlit", None),
            ("yaml", None),
        ]
        for mod_name, _ in deps:
            try:
                mod = __import__(mod_name)
                ver = getattr(mod, "__version__", "unknown")
                print(f"  {mod_name:<20} {ver}")
            except ImportError:
                print(f"  {mod_name:<20} NOT INSTALLED")
    else:
        print()
        print("[5/6] Dependencies  (use --verbose for full dependency list)")

    # Summary
    print()
    print("[6/6] Summary")
    issues = []
    try:
        paths = get_app_paths()
        if not paths.data_dir.exists():
            issues.append("Data directory missing")
        if not paths.models_dir.exists():
            issues.append("Models directory missing")
    except Exception:
        issues.append("Cannot load configuration")

    if issues:
        print(f"  Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  No critical issues detected.")
    print()
    print("=" * 60)


def _run_health() -> None:
    """Quick health check — reports if the system can perform inference."""
    from duplicate_question_app._config.logging_setup import configure_logging
    from duplicate_question_app._config.settings import get_app_paths, resolve_model_selection

    configure_logging()

    print("Checking system health...")

    checks = 0
    passed = 0

    # Config
    checks += 1
    config_dir = _ensure_project_root() / "configs"
    if config_dir.exists():
        passed += 1
    else:
        print("  FAIL: Config directory not found")

    # Paths
    try:
        checks += 1
        paths = get_app_paths()
        if paths.project_root.exists():
            passed += 1
        else:
            print("  FAIL: Project root not found")
    except Exception as exc:
        print(f"  FAIL: Cannot load paths: {exc}")

    # Model resolution
    try:
        checks += 1
        resolution = resolve_model_selection(get_app_paths())
        if resolution.selected_model_dir.exists():
            passed += 1
        else:
            print(f"  WARN: Selected model directory not found: {resolution.selected_label}")
    except Exception as exc:
        print(f"  WARN: Model resolution unavailable: {exc}")

    # Summary
    print()
    if passed == checks:
        print("Health: OK")
    else:
        print(f"Health: {passed}/{checks} checks passed")
    sys.exit(0 if passed == checks else 1)


def _run_validate() -> None:
    """Validate configuration, paths, and model directories."""
    from duplicate_question_app._config.logging_setup import configure_logging, get_logger
    from duplicate_question_app._config.settings import get_app_paths
    from duplicate_question_app._validation import (
        ValidationResult,
        validate_app_paths,
        validate_model_directory,
    )

    configure_logging()
    logger = get_logger("cli.validate")

    print("Validating system...")
    result = ValidationResult()

    # Validate app paths
    try:
        paths = get_app_paths()
        result.merge(validate_app_paths(paths))
    except Exception as exc:
        result.errors.append(f"Cannot load paths: {exc}")

    # Validate model directories
    try:
        paths = get_app_paths()
        w4 = validate_model_directory(paths.week4_model_dir, "Week 4 Improved DistilBERT")
        result.merge(w4)
        w3 = validate_model_directory(paths.week3_model_dir, "Week 3 DistilBERT")
        result.merge(w3)
    except Exception as exc:
        result.errors.append(f"Cannot validate model directories: {exc}")

    # Validate config directory
    config_dir = _ensure_project_root() / "configs"
    if not config_dir.exists():
        result.errors.append(f"Config directory not found: {config_dir}")

    print()
    print(result.summary())
    print()
    logger.info("Validation complete: %s", "PASSED" if result.passed else f"FAILED ({len(result.errors)} errors)")
    sys.exit(0 if result.passed else 1)


def _run_config(verbose: bool = False) -> None:
    """Display current effective configuration."""
    from duplicate_question_app.config import get_config

    print("=" * 60)
    print("  Current Configuration")
    print("=" * 60)

    sections = ["app", "paths", "inference", "logging"]
    if verbose:
        sections = ["app", "paths", "models", "inference", "training", "evaluation", "dataset", "logging"]

    for section in sections:
        print()
        print(f"[{section}]")
        cfg = get_config(section)
        if cfg:
            _print_config(cfg, indent=2)
        else:
            print("  (empty / not configured)")
    print()


def _print_config(cfg: dict, indent: int = 2) -> None:
    """Pretty-print a config dictionary."""
    prefix = " " * indent
    for key, value in cfg.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            _print_config(value, indent + 2)
        elif isinstance(value, list):
            print(f"{prefix}{key}:")
            for item in value[:5]:
                print(f"{prefix}  - {item}")
            if len(value) > 5:
                print(f"{prefix}  ... and {len(value) - 5} more")
        else:
            print(f"{prefix}{key}: {value}")


def _run_runtime_diagnostics() -> None:
    """Display runtime diagnostics."""
    from duplicate_question_app._config.logging_setup import configure_logging
    from duplicate_question_app._inference.optimizer import (
        get_embedding_cache,
        get_preprocessing_cache,
    )

    configure_logging()

    print("=" * 60)
    print("  Runtime Diagnostics")
    print("=" * 60)

    # Cache stats
    print()
    print("Embedding Cache:")
    ec = get_embedding_cache().stats()
    print(f"  Size:   {ec.size} / {ec.max_size}")
    print(f"  Hits:   {ec.hits}")
    print(f"  Misses: {ec.misses}")
    print(f"  Hit Rate: {ec.hit_rate:.1%}")
    print(f"  Evictions: {ec.evictions}")

    print()
    print("Preprocessing Cache:")
    pc = get_preprocessing_cache().stats()
    print(f"  Size:   {pc.size} / {pc.max_size}")
    print(f"  Hits:   {pc.hits}")
    print(f"  Misses: {pc.misses}")
    print(f"  Hit Rate: {pc.hit_rate:.1%}")

    print()


if __name__ == "__main__":
    main()
