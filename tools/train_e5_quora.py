"""Fine-tune E5-base-v2 on Quora duplicate questions dataset.

Uses MultipleNegativesRankingLoss from sentence-transformers for contrastive
learning. This aligns the embedding space to distinguish duplicate from
non-duplicate question pairs.

Hard negatives from the mining pipeline are used to improve discriminability.

Usage:
    python scripts/train_e5_quora.py [--use-gpu] [--epochs 3] [--batch-size 64]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.data_loader import get_quora_splits
from duplicate_question_app.hard_negative_mining import (
    load_hard_negatives,
    mine_hard_negatives_combined,
)
from duplicate_question_app.preprocessing import normalize_question

RESULTS_DIR = Path(__file__).resolve().parents[1] / "outputs" / "embedding_models"
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"


def prepare_training_data(
    max_train_samples: int | None = None,
    include_hard_negatives: bool = True,
    hard_negatives_path: Path | None = None,
    hard_neg_k: int = 15000,
    val_size: int = 5000,
) -> tuple[list[str], list[str], list[int], list[str], list[str], list[int]]:
    """Prepare Quora data for contrastive training.

    Returns:
        (train_q1s, train_q2s, train_labels, val_q1s, val_q2s, val_labels)
    """
    train_df, val_df, _ = get_quora_splits()

    if max_train_samples and len(train_df) > max_train_samples:
        train_df = train_df.sample(n=max_train_samples, random_state=42)

    # Normalize questions
    train_q1s = [normalize_question(q, expand_abbrevs=True) for q in train_df["q1"]]
    train_q2s = [normalize_question(q, expand_abbrevs=True) for q in train_df["q2"]]
    train_labels = train_df["label"].tolist()

    val_q1s = [normalize_question(q, expand_abbrevs=True) for q in val_df["q1"]]
    val_q2s = [normalize_question(q, expand_abbrevs=True) for q in val_df["q2"]]
    val_labels = val_df["label"].tolist()

    # Add hard negatives to training set
    if include_hard_negatives:
        if hard_negatives_path and hard_negatives_path.exists():
            hns = load_hard_negatives(hard_negatives_path)
        else:
            print("Mining hard negatives...")
            hns = mine_hard_negatives_combined(top_k=hard_neg_k)

        if not hns.empty:
            hn_q1s = [normalize_question(q, expand_abbrevs=True) for q in hns["q1"]]
            hn_q2s = [normalize_question(q, expand_abbrevs=True) for q in hns["q2"]]
            hn_labels = hns["label"].tolist()

            # Upsample hard negatives (they're more informative)
            hn_multiplier = 3
            train_q1s.extend(hn_q1s * hn_multiplier)
            train_q2s.extend(hn_q2s * hn_multiplier)
            train_labels.extend(hn_labels * hn_multiplier)

            print(f"Added {len(hn_q1s) * hn_multiplier:,} hard negative samples")

    print(f"Training samples: {len(train_labels):,}")
    print(f"Validation samples: {len(val_labels):,}")
    print(f"Train duplicate rate: {np.mean(train_labels):.3f}")

    return train_q1s, train_q2s, train_labels, val_q1s, val_q2s, val_labels


def train_with_contrastive_loss(
    model_name: str = "intfloat/e5-base-v2",
    output_name: str = "e5-quora-finetuned",
    max_train_samples: int | None = 200000,
    num_epochs: int = 3,
    batch_size: int = 64,
    learning_rate: float = 2e-5,
    warmup_ratio: float = 0.1,
    use_gpu: bool = False,
    save_model: bool = True,
) -> str:
    """Fine-tune a sentence transformer model using contrastive learning.

    Uses MultipleNegativesRankingLoss which is the standard approach for
    training embedding models on pairwise data.

    Args:
        model_name: Base model to fine-tune.
        output_name: Name for the fine-tuned model.
        max_train_samples: Max training samples (None = all).
        num_epochs: Number of training epochs.
        batch_size: Training batch size.
        learning_rate: Peak learning rate.
        warmup_ratio: Fraction of steps for linear warmup.
        use_gpu: Use GPU if available.
        save_model: Save model to disk.

    Returns:
        Path to the saved model.
    """
    from sentence_transformers import InputExample, SentenceTransformer, losses
    from sentence_transformers.evaluation import BinaryClassificationEvaluator
    from torch.utils.data import DataLoader

    device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    print(f"PyTorch version: {torch.__version__}")

    # Prepare data
    print("\n[1/4] Preparing training data...")
    train_q1s, train_q2s, train_labels, val_q1s, val_q2s, val_labels = prepare_training_data(
        max_train_samples=max_train_samples
    )

    # Load base model
    print(f"\n[2/4] Loading base model: {model_name}...")
    model = SentenceTransformer(model_name, device=device)
    print(f"  Model max_seq_length: {model.max_seq_length}")

    # Prepare training examples
    # For MultipleNegativesRankingLoss, we need anchor-positive pairs
    # Duplicate pairs (label=1) = positive pairs
    # Non-duplicate pairs (label=0) = negative (used as in-batch negatives)
    train_examples = []
    for q1, q2, label in zip(train_q1s, train_q2s, train_labels, strict=False):
        if label == 1:
            # For E5, we use query/passage prefixes
            anchor = f"query: {q1}"
            positive = f"passage: {q2}"
            train_examples.append(InputExample(texts=[anchor, positive]))

    print(f"  Training examples: {len(train_examples):,}")
    print("  (Non-duplicate pairs used as in-batch negatives)")

    train_dataloader = DataLoader(train_examples, batch_size=batch_size, shuffle=True, drop_last=True)

    # Loss function: MultipleNegativesRankingLoss
    # This is the standard loss for training embedding models on pairwise data.
    # It treats each positive pair as the target and uses other samples in the
    # batch as negatives - extremely effective for duplicate detection.
    train_loss = losses.MultipleNegativesRankingLoss(model)

    # Validation evaluator
    print("\n[3/4] Setting up evaluator...")
    val_sentences1 = [f"query: {q}" for q in val_q1s]
    val_sentences2 = [f"passage: {q}" for q in val_q2s]

    evaluator = BinaryClassificationEvaluator(
        sentences1=val_sentences1[:5000],
        sentences2=val_sentences2[:5000],
        labels=np.array(val_labels[:5000]),
        batch_size=batch_size,
        show_progress_bar=False,
    )

    # Save path
    output_path = str(MODELS_DIR / output_name)

    # Training arguments
    num_steps = len(train_dataloader) * num_epochs
    warmup_steps = int(num_steps * warmup_ratio)

    print("\n[4/4] Starting training...")
    print(f"  Epochs: {num_epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Steps per epoch: {len(train_dataloader):,}")
    print(f"  Total steps: {num_steps:,}")
    print(f"  Warmup steps: {warmup_steps}")
    print(f"  Output path: {output_path}")
    print()

    # Train
    start_time = time.time()

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=num_epochs,
        warmup_steps=warmup_steps,
        optimizer_params={"lr": learning_rate},
        output_path=output_path if save_model else None,
        save_best_model=save_model,
        evaluation_steps=min(500, len(train_dataloader)),
        use_amp=bool(use_gpu),
        show_progress_bar=True,
    )

    training_time = time.time() - start_time
    print(f"\n✅ Training completed in {training_time:.1f}s ({training_time / 60:.1f} min)")

    # Evaluate on validation set
    print("\nFinal validation evaluation:")
    val_emb1 = model.encode(
        val_sentences1[:5000], normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False
    )
    val_emb2 = model.encode(
        val_sentences2[:5000], normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False
    )
    similarities = (val_emb1 * val_emb2).sum(axis=1)

    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

    # Find optimal threshold
    best_f1 = 0
    best_thresh = 0.5
    for thresh in np.linspace(0.1, 0.9, 81):
        preds = (similarities >= thresh).astype(int)
        f1 = f1_score(val_labels[:5000], preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh

    preds = (similarities >= best_thresh).astype(int)
    acc = accuracy_score(val_labels[:5000], preds)
    roc_auc = roc_auc_score(val_labels[:5000], similarities)

    print(f"  Best threshold: {best_thresh:.3f}")
    print(f"  Validation Accuracy: {acc:.4f}")
    print(f"  Validation F1: {best_f1:.4f}")
    print(f"  Validation ROC-AUC: {roc_auc:.4f}")

    return output_path


def train_with_multitask_loss(
    model_name: str = "intfloat/e5-base-v2",
    output_name: str = "e5-quora-multitask",
    **kwargs,
) -> str:
    """Fine-tune with both MultipleNegativesRankingLoss and CoSENT loss.

    CoSENT loss uses cosine similarity with margin, which works well when
    we have binary labels. This can be more stable than contrastive loss alone.

    Args:
        model_name: Base model to fine-tune.
        output_name: Name for output model.
        **kwargs: Additional args passed to train_with_contrastive_loss.

    Returns:
        Path to saved model.
    """
    from sentence_transformers import InputExample, SentenceTransformer, losses
    from torch.utils.data import DataLoader

    device = "cuda" if kwargs.get("use_gpu") and torch.cuda.is_available() else "cpu"
    use_gpu = kwargs.get("use_gpu", False)

    # Prepare data
    train_q1s, train_q2s, train_labels, val_q1s, val_q2s, val_labels = prepare_training_data(
        max_train_samples=kwargs.get("max_train_samples", 200000),
        include_hard_negatives=kwargs.get("include_hard_negatives", True),
    )

    model = SentenceTransformer(model_name, device=device)

    # Create both MNRL and CoSENT examples
    mnrl_examples = []
    cosent_examples = []

    for q1, q2, label in zip(train_q1s, train_q2s, train_labels, strict=False):
        anchor = f"query: {q1}"
        text = f"passage: {q2}"
        if label == 1:
            mnrl_examples.append(InputExample(texts=[anchor, text]))
        # For CoSENT, we need pairs with similarity scores
        cosent_examples.append(InputExample(texts=[anchor, text], label=float(label)))

    # Multi-task loss
    mnrl_dataloader = DataLoader(mnrl_examples, batch_size=kwargs.get("batch_size", 64), shuffle=True, drop_last=True)
    mnrl_loss = losses.MultipleNegativesRankingLoss(model)

    cosent_dataloader = DataLoader(
        cosent_examples, batch_size=kwargs.get("batch_size", 64), shuffle=True, drop_last=True
    )
    cosent_loss = losses.CoSENTLoss(model)

    # Combined training
    output_path = str(MODELS_DIR / output_name)
    num_epochs = kwargs.get("num_epochs", 3)
    warmup_ratio = kwargs.get("warmup_ratio", 0.1)
    kwargs.get("batch_size", 64)
    learning_rate = kwargs.get("learning_rate", 2e-5)

    model.fit(
        train_objectives=[
            (mnrl_dataloader, mnrl_loss),
            (cosent_dataloader, cosent_loss),
        ],
        epochs=num_epochs,
        warmup_steps=int(len(mnrl_dataloader) * num_epochs * warmup_ratio),
        optimizer_params={"lr": learning_rate},
        output_path=output_path,
        save_best_model=True,
        use_amp=bool(use_gpu),
        show_progress_bar=True,
    )

    print(f"\n✅ Multi-task training complete. Model saved to {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune E5 on Quora")
    parser.add_argument("--use-gpu", action="store_true", help="Use GPU if available")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--max-samples", type=int, default=200000, help="Max training samples")
    parser.add_argument("--multitask", action="store_true", help="Use multi-task loss (MNRL + CoSENT)")
    parser.add_argument("--no-hard-negatives", action="store_true", help="Skip hard negative mining")

    args = parser.parse_args()

    print("=" * 60)
    print("  E5 Fine-tuning on Quora Dataset")
    print("=" * 60)
    print(f"  GPU: {'ENABLED' if args.use_gpu else 'DISABLED'}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.lr}")
    print(f"  Max samples: {args.max_samples:,}")
    print(f"  Multi-task: {'YES' if args.multitask else 'NO'}")
    print(f"  Hard negatives: {'NO' if args.no_hard_negatives else 'YES'}")
    print("=" * 60)

    if args.multitask:
        output = train_with_multitask_loss(
            model_name="intfloat/e5-base-v2",
            output_name="e5-quora-finetuned",
            max_train_samples=args.max_samples,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
            use_gpu=args.use_gpu,
            include_hard_negatives=not args.no_hard_negatives,
        )
    else:
        output = train_with_contrastive_loss(
            model_name="intfloat/e5-base-v2",
            output_name="e5-quora-finetuned",
            max_train_samples=args.max_samples,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
            use_gpu=args.use_gpu,
        )

    print(f"\n✅ Fine-tuned model saved to: {output}")
    print("\nTo use in inference, add this model to config.py and embedding_models.py")
