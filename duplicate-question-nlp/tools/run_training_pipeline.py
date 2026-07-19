"""🔥 Master Training Pipeline — runs the complete improvement pipeline.

Order:
1. Hard Negative Mining (finds hardest non-duplicate pairs)
2. Fine-tune E5 embedding model (contrastive learning)
3. Fine-tune Cross-Encoder DeBERTa-v3 (pairwise classification)
4. Enhanced Evaluation (compares all models)

Usage:
    # Full pipeline
    python tools/run_training_pipeline.py --use-gpu --fast

    # Step-by-step
    python tools/run_training_pipeline.py --step mine
    python tools/run_training_pipeline.py --step train-e5
    python tools/run_training_pipeline.py --step train-cross-encoder
    python tools/run_training_pipeline.py --step evaluate
"""

from __future__ import annotations

import sys
import time
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


def run_mining():
    """Run hard negative mining (step 1)."""
    print("\n" + "=" * 60)
    print("  STEP 1/4: Hard Negative Mining")
    print("=" * 60)
    
    from duplicate_question_app.hard_negative_mining import main as mine_main
    mine_main()
    
    print("\n✅ Hard negative mining complete!\n")


def run_train_e5(use_gpu: bool = False, fast: bool = False):
    """Fine-tune E5 on Quora (step 2)."""
    print("\n" + "=" * 60)
    print("  STEP 2/4: Fine-tune E5 Embedding Model")
    print("=" * 60)
    
    # Run training script as subprocess for clean execution
    script = TOOLS_DIR / "train_e5_quora.py"
    cmd = [sys.executable, str(script)]
    if use_gpu:
        cmd.append("--use-gpu")
    if fast:
        cmd.extend(["--epochs", "2", "--max-samples", "100000", "--batch-size", "128"])
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ E5 training failed with exit code {result.returncode}")
    else:
        print(f"\n✅ E5 fine-tuning complete!\n")


def run_train_cross_encoder(use_gpu: bool = False, fast: bool = False):
    """Fine-tune cross-encoder on Quora (step 3)."""
    print("\n" + "=" * 60)
    print("  STEP 3/4: Fine-tune Cross-Encoder (DeBERTa-v3)")
    print("=" * 60)
    
    script = TOOLS_DIR / "train_cross_encoder.py"
    cmd = [sys.executable, str(script)]
    if use_gpu:
        cmd.append("--use-gpu")
    if fast:
        cmd.extend(["--epochs", "2", "--max-samples", "50000", "--batch-size", "16"])
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ Cross-encoder training failed with exit code {result.returncode}")
    else:
        print(f"\n✅ Cross-encoder training complete!\n")


def run_evaluation():
    """Run enhanced evaluation (step 4)."""
    print("\n" + "=" * 60)
    print("  STEP 4/4: Enhanced Evaluation")
    print("=" * 60)
    
    script = TOOLS_DIR / "enhanced_evaluation.py"
    cmd = [sys.executable, str(script)]
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ Evaluation failed with exit code {result.returncode}")
    else:
        print(f"\n✅ Evaluation complete!\n")


def main():
    parser = argparse.ArgumentParser(
        description="Duplicate Question Detection — Training Pipeline"
    )
    parser.add_argument(
        "--step", type=str, default="all",
        choices=["all", "mine", "train-e5", "train-cross-encoder", "evaluate"],
        help="Pipeline step to run (default: all)"
    )
    parser.add_argument(
        "--use-gpu", action="store_true",
        help="Use GPU for training (much faster)"
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Fast mode: fewer samples, fewer epochs for quick testing"
    )
    args = parser.parse_args()

    total_start = time.time()

    print()
    print("🔥" + "=" * 60)
    print("  DUPLICATE QUESTION DETECTION — IMPROVEMENT PIPELINE")
    print("  Target: 90-95% Accuracy on Quora Test Set")
    print("=" * 60)
    print(f"\n  Fast mode: {'YES' if args.fast else 'NO'}")
    print(f"  GPU:      {'ENABLED' if args.use_gpu else 'DISABLED (CPU)'}")
    print(f"  Step:     {args.step}")

    steps = {
        "mine": lambda: run_mining(),
        "train-e5": lambda: run_train_e5(args.use_gpu, args.fast),
        "train-cross-encoder": lambda: run_train_cross_encoder(args.use_gpu, args.fast),
        "evaluate": lambda: run_evaluation(),
    }

    if args.step == "all":
        print("\n\nRunning FULL pipeline (all 4 steps)...\n")
        run_mining()
        run_train_e5(args.use_gpu, args.fast)
        run_train_cross_encoder(args.use_gpu, args.fast)
        run_evaluation()
    else:
        if args.step in steps:
            steps[args.step]()
        else:
            print(f"Unknown step: {args.step}")
            sys.exit(1)

    total_time = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"  PIPELINE COMPLETE! Total time: {total_time:.1f}s ({total_time / 60:.1f}min)")
    print(f"{'=' * 60}")
    print()
    print("📋 Deliverables:")
    print("  1. data/hard_negatives/  — mined hard negatives")
    print("  2. models/e5-quora-finetuned/  — fine-tuned E5 model")
    print("  3. models/cross-encoder-quora/ — fine-tuned cross-encoder")
    print("  4. outputs/enhanced_evaluation/ — benchmark results")
    print()
    print("▶️  Next: Use the Streamlit app to test the new models!")


if __name__ == "__main__":
    main()
