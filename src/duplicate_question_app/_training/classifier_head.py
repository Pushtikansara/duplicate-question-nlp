"""Classifier heads trained on embedding features.

Replaces cosine-similarity + sigmoid with a trained classifier operating on
concatenated embedding features: [emb1, emb2, |emb1-emb2|, emb1*emb2].

Two approaches:
1. LogisticRegression (LR) on full 3072-dim features — best generalization.
2. EmbeddingMLP — small MLP on full features (prone to overfitting).

Trained LR heads:
- E5:    C=100.0  Test F1=0.7965
- BGE:   C=10.0   Test F1=0.8169
- MPNet: C=10.0   Test F1=0.8169
- Ensemble (avg): Test F1=0.8225  (gap to DistilBERT fine-tuned: 0.077)

The LR approach learns a learned bilinear similarity in the embedding space,
which is much more expressive than cosine similarity (just a single scalar).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app.config import get_app_paths, get_config
from duplicate_question_app.data_loader import get_quora_splits
from duplicate_question_app.embedding_models import (
    _resolve_device,
    get_sentence_transformer_model,
)
from duplicate_question_app.preprocessing import normalize_question

_logger = get_logger(__name__)


def _get_model_dir() -> Path:
    paths = get_app_paths()
    return paths.models_dir


def _build_lr_models() -> dict[str, Path]:
    model_dir = _get_model_dir()
    models_cfg = get_config("models") or {}
    lr_models_cfg = models_cfg.get("lr_head_models", {})
    result = {}
    for hf_name, filename in lr_models_cfg.items():
        result[hf_name] = model_dir / filename
    # Fall back to default if config missing
    if not result:
        result = {
            "E5-base-v2": model_dir / "e5_base_v2_lr_head.pkl",
            "BAAI/bge-base-en-v1.5": model_dir / "bge_lr_head.pkl",
            "sentence-transformers/all-mpnet-base-v2": model_dir / "all_mpnet_base_v2_lr_head.pkl",
        }
    return result


LR_MODELS = _build_lr_models()


class EmbeddingMLP(nn.Module):
    """MLP classifier trained on concatenated embedding features."""

    def __init__(self, input_dim: int = 3072, hidden_dim: int = 256, hidden_dim2: int = 64, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.net(x)).squeeze(-1)


def _load_lr_head(model_name: str) -> LogisticRegression:
    """Load a trained LogisticRegression head for a given embedding model."""
    key = model_name
    if key not in LR_MODELS:
        available = list(LR_MODELS.keys())
        raise ValueError(f"No LR head for '{model_name}'. Available: {available}")
    return joblib.load(LR_MODELS[key])


def build_features(emb1: np.ndarray, emb2: np.ndarray) -> np.ndarray:
    """Build feature vectors from pairs of normalized embeddings."""
    return np.concatenate(
        [
            emb1,
            emb2,
            np.abs(emb1 - emb2),
            emb1 * emb2,
        ],
        axis=1,
    )


def predict_with_lr(
    model_name: str,
    q1: str,
    q2: str,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Predict single pair using embeddings + LR head."""
    start = time.time()
    q1_norm = normalize_question(q1, expand_abbrevs=True)
    q2_norm = normalize_question(q2, expand_abbrevs=True)

    encoder = get_sentence_transformer_model(model_name)
    is_e5 = "e5" in model_name.lower() and "bge" not in model_name.lower()
    q1_enc = f"query: {q1_norm}" if is_e5 else q1_norm
    q2_enc = f"passage: {q2_norm}" if is_e5 else q2_norm

    emb1 = encoder.encode([q1_enc], normalize_embeddings=True)[0]
    emb2 = encoder.encode([q2_enc], normalize_embeddings=True)[0]

    features = build_features(emb1.reshape(1, -1), emb2.reshape(1, -1))
    clf = _load_lr_head(model_name)
    prob_duplicate = float(clf.predict_proba(features)[0, 1])
    prob_non = 1.0 - prob_duplicate
    pred_label = int(prob_duplicate >= threshold)

    return {
        "question1": q1_norm,
        "question2": q2_norm,
        "predicted_label": pred_label,
        "prediction": "Duplicate" if pred_label == 1 else "Non-Duplicate",
        "prob_non_duplicate": prob_non,
        "prob_duplicate": prob_duplicate,
        "confidence": max(prob_non, prob_duplicate),
        "threshold": threshold,
        "model_label": f"{model_name}+LR",
        "device": str(_resolve_device()),
        "latency_ms": (time.time() - start) * 1000,
    }


def batch_predict_with_lr(
    model_name: str,
    pairs: list[tuple[str, str]],
    threshold: float = 0.5,
    batch_size: int = 256,
) -> list[dict[str, Any]]:
    """Batched prediction using embeddings + LR head."""
    if not pairs:
        return []
    start = time.time()

    q1s = [normalize_question(p[0], expand_abbrevs=True) for p in pairs]
    q2s = [normalize_question(p[1], expand_abbrevs=True) for p in pairs]

    is_e5 = "e5" in model_name.lower() and "bge" not in model_name.lower()
    q1_enc = [f"query: {q}" if is_e5 else q for q in q1s]
    q2_enc = [f"passage: {q}" if is_e5 else q for q in q2s]

    encoder = get_sentence_transformer_model(model_name)
    emb1 = encoder.encode(q1_enc, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False)
    emb2 = encoder.encode(q2_enc, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False)

    features = build_features(emb1, emb2)
    clf = _load_lr_head(model_name)
    probs = clf.predict_proba(features)[:, 1]
    preds = (probs >= threshold).astype(int)
    prob_nons = 1.0 - probs

    encode_time_ms = (time.time() - start) * 1000
    return [
        {
            "question1": q1s[i],
            "question2": q2s[i],
            "predicted_label": int(preds[i]),
            "prediction": "Duplicate" if preds[i] == 1 else "Non-Duplicate",
            "prob_non_duplicate": float(prob_nons[i]),
            "prob_duplicate": float(probs[i]),
            "confidence": float(max(probs[i], prob_nons[i])),
            "threshold": threshold,
            "model_label": f"{model_name}+LR",
            "device": str(_resolve_device()),
            "latency_ms": encode_time_ms,
        }
        for i in range(len(pairs))
    ]


def batch_predict_ensemble(
    pairs: list[tuple[str, str]],
    model_names: list[str] | None = None,
    weights: list[float] | None = None,
    threshold: float = 0.52,
    batch_size: int = 256,
) -> list[dict[str, Any]]:
    """Ensemble prediction averaging probabilities from multiple models.

    Args:
        pairs: List of (q1, q2) tuples.
        model_names: Models to ensemble (default: E5, BGE, MPNet).
        weights: Per-model weights (default: [0.3, 0.35, 0.35]).
        threshold: Decision threshold (optimized at 0.52).

    Returns:
        List of prediction dicts.
    """
    if model_names is None:
        model_names = ["E5-base-v2", "BAAI/bge-base-en-v1.5", "sentence-transformers/all-mpnet-base-v2"]
    if weights is None:
        weights = [0.3, 0.35, 0.35]
    weights = np.array(weights) / sum(weights)

    all_probs = []
    for name in model_names:
        preds = batch_predict_with_lr(name, pairs, threshold=threshold, batch_size=batch_size)
        all_probs.append(np.array([p["prob_duplicate"] for p in preds]))

    avg_probs = np.average(all_probs, axis=0, weights=weights)
    final_preds = (avg_probs >= threshold).astype(int)
    prob_nons = 1.0 - avg_probs

    q1s = [normalize_question(p[0], expand_abbrevs=True) for p in pairs]
    q2s = [normalize_question(p[1], expand_abbrevs=True) for p in pairs]

    return [
        {
            "question1": q1s[i],
            "question2": q2s[i],
            "predicted_label": int(final_preds[i]),
            "prediction": "Duplicate" if final_preds[i] == 1 else "Non-Duplicate",
            "prob_non_duplicate": float(prob_nons[i]),
            "prob_duplicate": float(avg_probs[i]),
            "confidence": float(max(avg_probs[i], prob_nons[i])),
            "threshold": threshold,
            "model_label": "Ensemble(E5+BGE+MPNet)+LR",
            "device": str(_resolve_device()),
            "latency_ms": 0.0,
        }
        for i in range(len(pairs))
    ]


def extract_embeddings(model_name: str, texts: list[str], batch_size: int = 128) -> np.ndarray:
    """Extract normalized embeddings from a sentence transformer model."""
    model = get_sentence_transformer_model(model_name)
    is_e5 = "e5" in model_name.lower()
    encoded = [f"query: {t}" if is_e5 else t for t in texts]
    return model.encode(encoded, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)


def train_mlp_head(
    model_name: str = "E5-base-v2",
    max_train_samples: int | None = None,
    epochs: int = 15,
    batch_size: int = 256,
    lr: float = 1e-3,
    patience: int = 3,
    save_path: Path | None = None,
) -> nn.Module:
    """Train MLP head on E5 embeddings from Quora training data.

    Args:
        model_name: Sentence transformer to use.
        max_train_samples: Limit training size (None = all).
        epochs: Max training epochs.
        batch_size: Training batch size.
        lr: Learning rate.
        patience: Early stopping patience (epochs without val improvement).
        save_path: Where to save model weights.

    Returns:
        Trained MLP model.
    """
    device = torch.device(_resolve_device())
    _logger.info("Training on device: %s", device)

    # Load data
    train_df, val_df, _ = get_quora_splits()
    if max_train_samples and len(train_df) > max_train_samples:
        train_df = train_df.sample(n=max_train_samples, random_state=42)

    train_texts_1 = [normalize_question(q, expand_abbrevs=True) for q in train_df["q1"]]
    train_texts_2 = [normalize_question(q, expand_abbrevs=True) for q in train_df["q2"]]
    val_texts_1 = [normalize_question(q, expand_abbrevs=True) for q in val_df["q1"]]
    val_texts_2 = [normalize_question(q, expand_abbrevs=True) for q in val_df["q2"]]

    train_labels = torch.tensor(train_df["label"].values, dtype=torch.float32)
    val_labels = torch.tensor(val_df["label"].values, dtype=torch.float32)

    # Extract embeddings
    _logger.info("Extracting %s embeddings for training (%s pairs)...", model_name, f"{len(train_df):,}")
    t0 = time.time()
    train_emb1 = extract_embeddings(model_name, train_texts_1)
    train_emb2 = extract_embeddings(model_name, train_texts_2)
    _logger.info("  Done in %.1fs", time.time() - t0)

    _logger.info("Extracting %s embeddings for validation (%s pairs)...", model_name, f"{len(val_df):,}")
    t0 = time.time()
    val_emb1 = extract_embeddings(model_name, val_texts_1)
    val_emb2 = extract_embeddings(model_name, val_texts_2)
    _logger.info("  Done in %.1fs", time.time() - t0)

    # Build features
    train_features = build_features(train_emb1, train_emb2)
    val_features = build_features(val_emb1, val_emb2)

    # Convert to tensors
    train_X = torch.tensor(train_features, dtype=torch.float32)
    val_X = torch.tensor(val_features, dtype=torch.float32)
    train_y = train_labels
    val_y = val_labels

    # Create data loader
    dataset = torch.utils.data.TensorDataset(train_X, train_y)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Initialize model
    input_dim = train_features.shape[1]
    model = EmbeddingMLP(input_dim=input_dim).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    # Training loop
    best_val_f1 = 0.0
    best_epoch = -1
    patience_counter = 0

    for epoch in range(epochs):
        model.train()
        train_losses = []
        for batch_X, batch_y in loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            preds = model(batch_X)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        # Validation
        model.eval()
        with torch.no_grad():
            val_preds = model(val_X.to(device)).cpu().numpy()
        val_pred_labels = (val_preds >= 0.5).astype(int)

        from sklearn.metrics import accuracy_score, f1_score

        val_f1 = f1_score(val_y.numpy(), val_pred_labels, zero_division=0)
        val_acc = accuracy_score(val_y.numpy(), val_pred_labels)

        _logger.info(
            "Epoch %2d/%d  Loss: %.4f  Val Acc: %.4f Val F1: %.4f",
            epoch + 1,
            epochs,
            np.mean(train_losses),
            val_acc,
            val_f1,
        )

        # Early stopping
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            patience_counter = 0
            if save_path:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save(model.state_dict(), save_path)
                _logger.info("  -> Saved best model (F1=%.4f) to %s", val_f1, save_path)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                _logger.info("  Early stopping at epoch %d (best epoch %d)", epoch + 1, best_epoch + 1)
                break

    return model


def predict_with_mlp(
    model_name: str,
    q1: str,
    q2: str,
    mlp_head: EmbeddingMLP | None = None,
    weights_path: Path | None = None,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Predict single pair using embeddings + MLP head."""
    device = torch.device(_resolve_device())
    start = time.time()

    q1_norm = normalize_question(q1, expand_abbrevs=True)
    q2_norm = normalize_question(q2, expand_abbrevs=True)

    model = get_sentence_transformer_model(model_name)
    is_e5 = "e5" in model_name.lower()
    q1_enc = f"query: {q1_norm}" if is_e5 else q1_norm
    q2_enc = f"passage: {q2_norm}" if is_e5 else q2_norm

    emb1 = model.encode([q1_enc], normalize_embeddings=True)[0]
    emb2 = model.encode([q2_enc], normalize_embeddings=True)[0]

    features = build_features(emb1.reshape(1, -1), emb2.reshape(1, -1))
    features_t = torch.tensor(features, dtype=torch.float32).to(device)

    if mlp_head is None and weights_path is not None:
        input_dim = features.shape[1]
        mlp_head = EmbeddingMLP(input_dim=input_dim).to(device)
        mlp_head.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))

    if mlp_head is None:
        raise ValueError("Either mlp_head or weights_path must be provided")

    mlp_head.eval()
    with torch.no_grad():
        prob_duplicate = float(mlp_head(features_t).cpu().numpy()[0])

    prob_duplicate = max(0.0, min(1.0, prob_duplicate))
    prob_non = 1.0 - prob_duplicate
    pred_label = int(prob_duplicate >= threshold)
    latency_ms = (time.time() - start) * 1000

    return {
        "question1": q1_norm,
        "question2": q2_norm,
        "predicted_label": pred_label,
        "prediction": "Duplicate" if pred_label == 1 else "Non-Duplicate",
        "prob_non_duplicate": prob_non,
        "prob_duplicate": prob_duplicate,
        "confidence": max(prob_non, prob_duplicate),
        "threshold": threshold,
        "model_label": f"{model_name}+MLP",
        "device": str(device),
        "latency_ms": latency_ms,
    }


def batch_predict_with_mlp(
    model_name: str,
    pairs: list[tuple[str, str]],
    mlp_head: EmbeddingMLP | None = None,
    weights_path: Path | None = None,
    threshold: float = 0.5,
    batch_size: int = 64,
) -> list[dict[str, Any]]:
    """Batched prediction using embeddings + MLP head."""
    if not pairs:
        return []

    device = torch.device(_resolve_device())
    start = time.time()

    # Load model
    mlp_model = mlp_head
    if mlp_model is None and weights_path is not None:
        input_dim = 3072
        mlp_model = EmbeddingMLP(input_dim=input_dim).to(device)
        mlp_model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))

    if mlp_model is None:
        raise ValueError("Either mlp_head or weights_path must be provided")

    # Normalize and embed
    q1s = [normalize_question(p[0], expand_abbrevs=True) for p in pairs]
    q2s = [normalize_question(p[1], expand_abbrevs=True) for p in pairs]

    is_e5 = "e5" in model_name.lower()
    q1_enc = [f"query: {q}" if is_e5 else q for q in q1s]
    q2_enc = [f"passage: {q}" if is_e5 else q for q in q2s]

    encoder = get_sentence_transformer_model(model_name)
    emb1 = encoder.encode(q1_enc, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False)
    emb2 = encoder.encode(q2_enc, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False)

    # Build features
    features = build_features(emb1, emb2)
    features_t = torch.tensor(features, dtype=torch.float32).to(device)

    # Predict
    mlp_model.eval()
    with torch.no_grad():
        probs = mlp_model(features_t).cpu().numpy()
    probs = np.clip(probs, 0.0, 1.0)
    preds = (probs >= threshold).astype(int)
    prob_nons = 1.0 - probs

    encode_time_ms = (time.time() - start) * 1000

    return [
        {
            "question1": q1s[i],
            "question2": q2s[i],
            "predicted_label": int(preds[i]),
            "prediction": "Duplicate" if preds[i] == 1 else "Non-Duplicate",
            "prob_non_duplicate": float(prob_nons[i]),
            "prob_duplicate": float(probs[i]),
            "confidence": float(max(probs[i], prob_nons[i])),
            "threshold": threshold,
            "model_label": f"{model_name}+MLP",
            "device": str(device),
            "latency_ms": encode_time_ms,
        }
        for i in range(len(pairs))
    ]


if __name__ == "__main__":
    # Training script
    from duplicate_question_app.config import get_app_paths

    _paths = get_app_paths()
    MODEL_DIR = _paths.models_dir
    weights_path = MODEL_DIR / "e5_mlp_head.pt"
    _logger.info("=" * 60)
    _logger.info("Training MLP head on E5 embeddings")
    _logger.info("=" * 60)
    train_mlp_head(
        model_name="E5-base-v2",
        max_train_samples=150000,
        epochs=15,
        batch_size=256,
        lr=1e-3,
        patience=3,
        save_path=weights_path,
    )
