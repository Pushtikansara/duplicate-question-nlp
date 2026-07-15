"""Train a Cross-Encoder on Quora duplicate questions dataset.

Cross-encoders jointly encode both input questions, allowing full attention
between them. This consistently outperforms bi-encoders by 3-5% F1.

We fine-tune microsoft/deberta-v3-base which is the strongest model for
this task given its disentangled attention mechanism.

Usage:
    python scripts/train_cross_encoder.py [--use-gpu] [--epochs 3] [--batch-size 16]
"""

from __future__ import annotations

import sys
import time
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from torch.optim import AdamW
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, confusion_matrix,
)

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.data_loader import get_quora_splits
from duplicate_question_app.preprocessing import normalize_question

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "embedding_models"
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODEL_NAME = "cross-encoder-quora"
MODEL_PATH = MODELS_DIR / MODEL_NAME


class QuoraPairDataset(Dataset):
    """PyTorch Dataset for Quora question pairs."""

    def __init__(
        self,
        q1s: list[str],
        q2s: list[str],
        labels: list[int],
        tokenizer,
        max_length: int = 128,
    ):
        self.q1s = q1s
        self.q2s = q2s
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        q1 = self.q1s[idx]
        q2 = self.q2s[idx]
        label = self.labels[idx]

        encoding = self.tokenizer(
            q1,
            q2,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(label, dtype=torch.long),
        }


def prepare_data(
    max_train_samples: int | None = None,
    sample_val: bool = True,
    val_size: int = 5000,
) -> tuple[QuoraPairDataset, QuoraPairDataset, pd.DataFrame]:
    """Prepare Quora datasets for cross-encoder training.

    Args:
        max_train_samples: Limit training size.
        sample_val: Use sampled validation set.
        val_size: Validation set size.

    Returns:
        (train_dataset, val_dataset, test_df)
    """
    train_df, val_df, test_df = get_quora_splits()

    if max_train_samples and len(train_df) > max_train_samples:
        train_df = train_df.sample(n=max_train_samples, random_state=42)

    # Normalize
    train_q1s = [normalize_question(q, expand_abbrevs=True) for q in train_df["q1"]]
    train_q2s = [normalize_question(q, expand_abbrevs=True) for q in train_df["q2"]]
    train_labels = train_df["label"].tolist()

    val_q1s = [normalize_question(q, expand_abbrevs=True) for q in val_df["q1"]]
    val_q2s = [normalize_question(q, expand_abbrevs=True) for q in val_df["q2"]]
    val_labels = val_df["label"].tolist()

    if sample_val and len(val_labels) > val_size:
        indices = np.random.RandomState(42).choice(len(val_labels), val_size, replace=False)
        val_q1s = [val_q1s[i] for i in indices]
        val_q2s = [val_q2s[i] for i in indices]
        val_labels = [val_labels[i] for i in indices]

    print(f"Train: {len(train_labels):,} pairs (dup rate: {np.mean(train_labels):.3f})")
    print(f"Val:   {len(val_labels):,} pairs")

    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")

    train_dataset = QuoraPairDataset(train_q1s, train_q2s, train_labels, tokenizer)
    val_dataset = QuoraPairDataset(val_q1s, val_q2s, val_labels, tokenizer)

    return train_dataset, val_dataset, test_df


def train_cross_encoder(
    model_name: str = "microsoft/deberta-v3-base",
    output_path: Path = MODEL_PATH,
    max_train_samples: int | None = 200000,
    num_epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    weight_decay: float = 0.01,
    warmup_ratio: float = 0.1,
    use_gpu: bool = False,
    gradient_accumulation_steps: int = 2,
    max_length: int = 128,
    fp16: bool = False,
) -> Path:
    """Fine-tune a cross-encoder on Quora duplicate questions.

    Cross-encoders process both questions through a single transformer,
    allowing full cross-attention between the two texts. This is more
    accurate than bi-encoders but slower for large-scale retrieval.

    Args:
        model_name: HuggingFace cross-encoder model.
        output_path: Where to save fine-tuned model.
        max_train_samples: Limit training data.
        num_epochs: Training epochs.
        batch_size: Batch size per device.
        learning_rate: Peak learning rate.
        weight_decay: AdamW weight decay.
        warmup_ratio: Linear warmup fraction.
        use_gpu: Use GPU if available. Auto-detects if not set.
        gradient_accumulation_steps: Accumulate gradients.
        max_length: Max sequence length.
        fp16: Use mixed precision training. Auto-enabled on GPU if not set.

    Returns:
        Path to saved model.
    """
    # ============================================================
    # GPU AUTO-DETECTION — no need for --use-gpu flag
    # ============================================================
    if use_gpu is None:
        use_gpu = torch.cuda.is_available()
    device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
    use_fp16 = (fp16 if fp16 is not None else True) and device.type == "cuda"
    
    # ============================================================
    # CUDA OPTIMIZATIONS
    # ============================================================
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True          # Auto-tune cuDNN kernels
        torch.backends.cuda.matmul.allow_tf32 = True   # Enable TF32 on RTX 4060
        torch.backends.cudnn.allow_tf32 = True
        torch.set_float32_matmul_precision('high')     # Use tensor cores
        print(f"  🚀 GPU optimizations: cudnn.benchmark=True, TF32=True")

    print(f"Device: {device}")
    print(f"Mixed Precision (FP16): {use_fp16}")

    # Prepare data
    print("\n[1/4] Preparing data (pre-tokenizing for GPU efficiency)...")
    train_dataset, val_dataset, test_df = prepare_data(
        max_train_samples=max_train_samples,
    )

    # Pre-tokenize training data to avoid CPU tokenization bottleneck each epoch
    print("  Pre-tokenizing training data...")
    train_input_ids = []
    train_attention_masks = []
    train_labels_list = []
    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")
    for i in range(len(train_dataset)):
        item = train_dataset[i]
        train_input_ids.append(item["input_ids"])
        train_attention_masks.append(item["attention_mask"])
        train_labels_list.append(item["labels"])
    
    # Create tensor dataset (keeps tokenized data in memory, avoiding re-tokenization)
    train_tensor_dataset = torch.utils.data.TensorDataset(
        torch.stack(train_input_ids),
        torch.stack(train_attention_masks),
        torch.tensor(train_labels_list),
    )
    
    print("  Pre-tokenizing validation data...")
    val_input_ids = []
    val_attention_masks = []
    val_labels_list = []
    for i in range(len(val_dataset)):
        item = val_dataset[i]
        val_input_ids.append(item["input_ids"])
        val_attention_masks.append(item["attention_mask"])
        val_labels_list.append(item["labels"])
    
    val_tensor_dataset = torch.utils.data.TensorDataset(
        torch.stack(val_input_ids),
        torch.stack(val_attention_masks),
        torch.tensor(val_labels_list),
    )

    # ============================================================
    # GPU-OPTIMIZED DATALOADER
    # ============================================================
    num_cpus = torch.multiprocessing.cpu_count() if hasattr(torch.multiprocessing, 'cpu_count') else 4
    data_num_workers = min(8, num_cpus // 2)  # Use half of available CPUs for data loading
    
    train_loader = DataLoader(
        train_tensor_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=data_num_workers,
        pin_memory=device.type == "cuda",       # Pin memory for faster GPU transfer
        persistent_workers=data_num_workers > 0, # Keep workers alive between epochs
        prefetch_factor=2 if data_num_workers > 0 else None,
    )
    val_loader = DataLoader(
        val_tensor_dataset,
        batch_size=batch_size * 2,
        shuffle=False,
        num_workers=data_num_workers,
        pin_memory=device.type == "cuda",
        persistent_workers=data_num_workers > 0,
    )

    print(f"  DataLoaders: num_workers={data_num_workers}, pin_memory={device.type=='cuda'}")

    # Load model
    print(f"\n[2/4] Loading {model_name}...")
    raw_model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=2, torch_dtype=torch.float32
    )
    raw_model = raw_model.to(device, non_blocking=device.type == "cuda")
    raw_model = raw_model.float()
    
    model = raw_model

    # Handle class imbalance with weighted loss
    train_labels_np = np.array([t.item() for t in train_labels_list])
    n_pos = (train_labels_np == 1).sum()
    n_neg = (train_labels_np == 0).sum()
    weight_neg = 1.0
    weight_pos = n_neg / n_pos if n_pos > 0 else 1.0
    class_weights = torch.tensor([weight_neg, weight_pos], dtype=torch.float).to(device, non_blocking=True)
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)
    print(f"  Class weights: neg={weight_neg:.3f}, pos={weight_pos:.3f}")

    # Fused AdamW for GPU (faster CUDA kernel)
    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay,
                      fused=(device.type == "cuda"))
    total_steps = len(train_loader) * num_epochs // gradient_accumulation_steps
    warmup_steps = int(total_steps * warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    print(f"\n[3/4] Starting training...")
    print(f"  Epochs: {num_epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Gradient accumulation: {gradient_accumulation_steps}")
    print(f"  Effective batch size: {batch_size * gradient_accumulation_steps}")
    print(f"  Steps per epoch: {len(train_loader):,}")
    print(f"  Total steps: {total_steps:,}")
    print(f"  Warmup steps: {warmup_steps}")
    print(f"  GPU memory (pre-training): {torch.cuda.memory_allocated()/1024**3:.2f} GB / {torch.cuda.memory_reserved()/1024**3:.2f} GB reserved" if device.type == "cuda" else "")

    # ============================================================
    # DEVICE VERIFICATION — verify every tensor is on CUDA
    # ============================================================
    print(f"\n  📊 Device verification:")
    print(f"    Model device: {next(model.parameters()).device}")
    print(f"    Optimizer on: {device}")
    sample_batch = next(iter(train_loader))
    sample_ids, sample_mask, sample_labels = sample_batch
    print(f"    input_ids device: CPU (moved to GPU per-batch)")
    print(f"    Loss function weights device: {class_weights.device}")
    if device.type == "cuda":
        print(f"    ✅ All tensors will be on CUDA during training")
        print(f"    🎯 GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.memory_reserved()/1024**3:.2f}GB reserved)")

    # Training loop
    best_val_f1 = 0.0
    best_epoch = -1
    patience = 2
    patience_counter = 0

    scaler = torch.amp.GradScaler(device.type) if use_fp16 else None

    for epoch in range(num_epochs):
        epoch_start = time.time()
        model.train()
        total_loss = 0
        optimizer.zero_grad()

        for step, batch in enumerate(train_loader):
            # Unpack pre-tokenized batch (TensorDataset returns tuple)
            input_ids, attention_mask, labels = batch
            
            # Move to GPU with non_blocking for async transfer
            input_ids = input_ids.to(device, non_blocking=True)
            attention_mask = attention_mask.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            if use_fp16:
                with torch.amp.autocast(device_type=device.type):
                    outputs = model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels,
                    )
                    loss = loss_fn(outputs.logits, labels) / gradient_accumulation_steps
                scaler.scale(loss).backward()
            else:
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )
                loss = loss_fn(outputs.logits, labels) / gradient_accumulation_steps
                loss.backward()

            total_loss += loss.item() * gradient_accumulation_steps

            if (step + 1) % gradient_accumulation_steps == 0:
                if use_fp16:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            if (step + 1) % 500 == 0:
                avg_loss = total_loss / (step + 1)
                gpu_info = ""
                if device.type == "cuda":
                    alloc = torch.cuda.memory_allocated() / 1024**3
                    reserved = torch.cuda.memory_reserved() / 1024**3
                    gpu_info = f"GPU: {alloc:.2f}GB/{reserved:.2f}GB"
                print(f"  Epoch {epoch+1} Step {step+1}/{len(train_loader)} "
                      f"Loss: {avg_loss:.4f} LR: {scheduler.get_last_lr()[0]:.2e} {gpu_info}")

        # Validation
        model.eval()
        val_loss = 0
        all_preds = []
        all_labels = []
        all_probs = []
        with torch.no_grad():
            for batch in val_loader:
                input_ids, attention_mask, labels = batch
                input_ids = input_ids.to(device, non_blocking=True)
                attention_mask = attention_mask.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)

                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                )
                val_loss += loss_fn(outputs.logits, labels).item()

                probs = torch.softmax(outputs.logits, dim=1)
                all_probs.extend(probs[:, 1].cpu().numpy())
                all_preds.extend(torch.argmax(probs, dim=1).cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        val_acc = accuracy_score(all_labels, all_preds)
        val_f1 = f1_score(all_labels, all_preds, zero_division=0)
        val_prec = precision_score(all_labels, all_preds, zero_division=0)
        val_rec = recall_score(all_labels, all_preds, zero_division=0)
        val_roc = roc_auc_score(all_labels, all_probs)

        epoch_time = time.time() - epoch_start
        gpu_report = ""
        if device.type == "cuda":
            alloc = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            gpu_report = f"GPU: {alloc:.2f}GB/{reserved:.2f}GB"
        print(f"\n  Epoch {epoch+1} — Val Loss: {val_loss/len(val_loader):.4f}")
        print(f"    Accuracy: {val_acc:.4f}  F1: {val_f1:.4f}")
        print(f"    Precision: {val_prec:.4f}  Recall: {val_rec:.4f}")
        print(f"    ROC-AUC: {val_roc:.4f}  Time: {epoch_time:.0f}s {gpu_report}")

        # Save best model (save unwrapped version to avoid torch.compile wrapper)
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            patience_counter = 0
            print(f"    → New best F1! Saving model...")

            output_path.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(output_path)
            tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")
            tokenizer.save_pretrained(output_path)
            print(f"    → Model saved to {output_path}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\n  Early stopping at epoch {epoch+1} (best epoch {best_epoch+1})")
                break

    # Load best model
    print(f"\n[4/4] Loading best model from epoch {best_epoch+1}...")
    best_model = AutoModelForSequenceClassification.from_pretrained(output_path)
    best_model.to(device, non_blocking=device.type == "cuda")

    # Evaluate on test set with GPU-optimized DataLoader
    print("\nEvaluating on test set...")
    test_q1s = [normalize_question(q, expand_abbrevs=True) for q in test_df["q1"]]
    test_q2s = [normalize_question(q, expand_abbrevs=True) for q in test_df["q2"]]
    test_labels = test_df["label"].tolist()

    # Pre-tokenize test data
    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")
    test_input_ids = []
    test_attention_masks = []
    for q1, q2 in zip(test_q1s, test_q2s):
        enc = tokenizer(q1, q2, max_length=128, padding="max_length", truncation=True, return_tensors="pt")
        test_input_ids.append(enc["input_ids"].squeeze(0))
        test_attention_masks.append(enc["attention_mask"].squeeze(0))
    test_tensor_dataset = torch.utils.data.TensorDataset(
        torch.stack(test_input_ids),
        torch.stack(test_attention_masks),
    )
    test_loader = DataLoader(
        test_tensor_dataset,
        batch_size=batch_size * 2,
        shuffle=False,
        num_workers=data_num_workers,
        pin_memory=device.type == "cuda",
    )

    best_model.eval()
    test_preds = []
    test_probs = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids, attention_mask = batch
            input_ids = input_ids.to(device, non_blocking=True)
            attention_mask = attention_mask.to(device, non_blocking=True)
            outputs = best_model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=1)
            test_probs.extend(probs[:, 1].cpu().numpy())
            test_preds.extend(torch.argmax(probs, dim=1).cpu().numpy())

    # Find optimal threshold
    best_test_f1 = 0
    best_thresh = 0.5
    for thresh in np.linspace(0.1, 0.9, 81):
        preds = (np.array(test_probs) >= thresh).astype(int)
        f1 = f1_score(test_labels, preds, zero_division=0)
        if f1 > best_test_f1:
            best_test_f1 = f1
            best_thresh = thresh

    test_preds_opt = (np.array(test_probs) >= best_thresh).astype(int)
    test_acc = accuracy_score(test_labels, test_preds_opt)
    test_f1 = f1_score(test_labels, test_preds_opt, zero_division=0)
    test_prec = precision_score(test_labels, test_preds_opt, zero_division=0)
    test_rec = recall_score(test_labels, test_preds_opt, zero_division=0)
    test_roc = roc_auc_score(test_labels, test_probs)
    cm = confusion_matrix(test_labels, test_preds_opt)

    print(f"\n{'='*60}")
    print(f"  TEST SET RESULTS — Cross-Encoder (DeBERTa-v3)")
    print(f"  Best threshold: {best_thresh:.3f}")
    print(f"  Accuracy:  {test_acc:.4f}")
    print(f"  F1:        {test_f1:.4f}")
    print(f"  Precision: {test_prec:.4f}")
    print(f"  Recall:    {test_rec:.4f}")
    print(f"  ROC-AUC:   {test_roc:.4f}")
    print(f"  Confusion: TN={cm[0,0]} FP={cm[0,1]} FN={cm[1,0]} TP={cm[1,1]}")
    print(f"{'='*60}")

    # Save test results
    results = {
        "model": "deberta-v3-cross-encoder-quora",
        "threshold": float(best_thresh),
        "accuracy": float(test_acc),
        "f1": float(test_f1),
        "precision": float(test_prec),
        "recall": float(test_rec),
        "roc_auc": float(test_roc),
        "confusion_matrix": cm.tolist(),
        "n_test_samples": len(test_labels),
    }

    results_path = RESULTS_DIR / "cross_encoder_metrics.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Cross-Encoder on Quora")
    parser.add_argument("--cpu", action="store_true", help="Force CPU (default: use GPU if available)")
    parser.add_argument("--no-fp16", action="store_true", help="Disable mixed precision (default: enabled on GPU)")
    parser.add_argument("--no-compile", action="store_true", help="Disable torch.compile")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (increase for GPU)")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--max-samples", type=int, default=200000,
                        help="Max training samples")
    parser.add_argument("--max-length", type=int, default=128, help="Max sequence length")
    args = parser.parse_args()

    print("=" * 60)
    print("  Cross-Encoder Training on Quora Dataset")
    print("=" * 60)
    print(f"  GPU: {'AUTO (CUDA detected)' if not args.cpu else 'FORCE CPU'}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size} (GPU optimized)")
    print(f"  Learning rate: {args.lr}")
    print(f"  Max samples: {args.max_samples:,}")
    print(f"  Max length: {args.max_length}")
    print(f"  FP16: {'AUTO-ENABLED on GPU' if not args.no_fp16 else 'DISABLED'}")
    print(f"  torch.compile: {'ENABLED' if not args.no_compile else 'DISABLED'}")
    print(f"  Data: Quora train/val/test (stratified 80/10/10)")
    print("=" * 60)

    output = train_cross_encoder(
        model_name="microsoft/deberta-v3-base",
        output_path=MODEL_PATH,
        max_train_samples=args.max_samples,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        use_gpu=not args.cpu,
        fp16=not args.no_fp16,
        max_length=args.max_length,
    )

    print(f"\n✅ Cross-Encoder model saved to: {output}")
    print("\nNext steps:")
    print("1. Add model path to config.py")
    print("2. Add inference support in embedding_models.py")
    print("3. Run evaluation to compare with baselines")
