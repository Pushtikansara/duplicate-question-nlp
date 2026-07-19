"""Command-line interface for Duplicate Question Detection.

Usage:
    dqd          Show available commands
    dqd-app      Launch the Streamlit dashboard
    dqd-predict  Run prediction on a CSV file
    dqd-benchmark Run model benchmarks
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
    from duplicate_question_app.week2_inference import is_week2_model
    from duplicate_question_app.utils.device import resolve_device

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

    print(f"Duplicate Question Detection v{__version__}")
    print()
    print("Available commands:")
    print("  dqd-app       Launch the Streamlit dashboard")
    print("  dqd-predict   Predict duplicates in a CSV file")
    print("  dqd-benchmark Run model benchmarks")
    print()
    print("Example:")
    print("  dqd-predict data/test.csv --model 'Cross-Encoder-Quora (Trained)' -o predictions.csv")
    print()


if __name__ == "__main__":
    main()
