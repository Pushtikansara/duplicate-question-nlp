"""Phase 11.1 — Model Validation & Benchmark
Evidence collection only. NO prediction logic changes.
Evaluates ALL 11 models on identical validation split."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from ares.model_registry import ModelBackend, find_entry
from duplicate_question_app._dataset.loader import get_quora_splits
from duplicate_question_app._preprocessing import normalize_question

# ============================================================
# METRICS
# ============================================================


def compute_metrics(y_true, y_pred, y_prob):
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        brier_score_loss,
        confusion_matrix,
        f1_score,
        log_loss,
        matthews_corrcoef,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_prob = np.array(y_prob)

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    try:
        roc_auc = roc_auc_score(y_true, y_prob)
    except Exception:
        roc_auc = float("nan")
    try:
        pr_auc = average_precision_score(y_true, y_prob)
    except Exception:
        pr_auc = float("nan")
    mcc = matthews_corrcoef(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)
    brier = brier_score_loss(y_true, y_prob)
    try:
        ll = log_loss(y_true, np.stack([1 - y_prob, y_prob], axis=1))
    except Exception:
        ll = float("nan")

    avg_conf = float(np.mean(np.maximum(y_prob, 1 - y_prob)))
    ece = compute_ece(y_prob, y_true, n_bins=10)

    return {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "mcc": float(mcc),
        "confusion_matrix": cm.tolist(),
        "brier_score": float(brier),
        "log_loss": float(ll),
        "avg_confidence": float(avg_conf),
        "ece": float(ece),
    }


def compute_ece(probs, labels, n_bins=10):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    ece = 0.0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (probs >= bin_lower) & (probs < bin_upper)
        if in_bin.sum() > 0:
            bin_acc = labels[in_bin].mean()
            bin_conf = probs[in_bin].mean()
            ece += np.abs(bin_acc - bin_conf) * in_bin.sum()
    return float(ece / len(labels))


# ============================================================
# PREDICTION FUNCTIONS (replicate dispatcher logic in batch)
# ============================================================


def _get_threshold_cfg(model_display_name):
    from ares._config import get_config

    inf_cfg = get_config("inference") or {}
    thresholds = inf_cfg.get("per_model_thresholds", {})
    return float(thresholds.get(model_display_name, inf_cfg.get("default_threshold", 0.5)))


def predict_classical_batch(entry, q1s, q2s, threshold):
    import joblib

    from ares._config import get_app_paths

    paths = get_app_paths()
    model_dir = paths.models_dir / "week2_models"
    if entry.internal_id == "week2_lr":
        path = model_dir / "logistic_regression.joblib"
    elif entry.internal_id == "week2_svm":
        path = model_dir / "linear_svm.joblib"
    else:
        raise ValueError(f"Unknown classical model: {entry.internal_id}")
    vectorizer_path = model_dir / "tfidf_vectorizer.joblib"
    if not path.exists() or not vectorizer_path.exists():
        raise FileNotFoundError(f"Classical model artifacts not found in {model_dir}")
    clf = joblib.load(path)
    vectorizer = joblib.load(vectorizer_path)

    q1s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q1s]
    q2s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q2s]
    combined = [a + " " + b for a, b in zip(q1s_n, q2s_n)]
    X = vectorizer.transform(combined)

    if hasattr(clf, "predict_proba"):
        probas = clf.predict_proba(X)
        prob_dup = probas[:, 1] if probas.shape[1] > 1 else clf.predict(X)
    else:
        if hasattr(clf, "decision_function"):
            decision = clf.decision_function(X)
            prob_dup = 1.0 / (1.0 + np.exp(-decision))
        else:
            prob_dup = clf.predict(X).astype(float)

    prob_dup = np.array(prob_dup).flatten()
    prob_non = 1.0 - prob_dup
    preds = (prob_dup >= threshold).astype(int)
    return preds, prob_dup


def predict_transformer_batch(entry, q1s, q2s, threshold, batch_size=64):
    import torch

    from ares._config import get_app_paths, get_config
    from ares.model_loader import load_model

    paths = get_app_paths()
    loaded = load_model(entry.display_name)
    model = loaded["model"]
    tokenizer = loaded["tokenizer"]
    device = loaded["device"]
    inf_cfg = get_config("inference") or {}
    max_length = inf_cfg.get("max_length", 128)

    q1s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q1s]
    q2s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q2s]

    all_probs = []
    n = len(q1s_n)
    for i in range(0, n, batch_size):
        batch_q1 = q1s_n[i : i + batch_size]
        batch_q2 = q2s_n[i : i + batch_size]
        inputs = tokenizer(
            batch_q1,
            batch_q2,
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
        all_probs.append(probs[:, 1].cpu().numpy())
    prob_dup = np.concatenate(all_probs)
    prob_non = 1.0 - prob_dup
    preds = (prob_dup >= threshold).astype(int)
    return preds, prob_dup


def predict_bi_encoder_batch(entry, q1s, q2s, threshold):
    from ares._config import get_config
    from ares.model_loader import load_model

    loaded = load_model(entry.display_name)
    model = loaded["model"]
    use_e5_prefix = loaded.get("use_e5_prefix", False)
    inf_cfg = get_config("inference") or {}
    sigmoid_params = inf_cfg.get("sigmoid_params", {})
    default_sigmoid = (15.0, 0.50)
    name = entry.internal_id
    params_map = {
        "e5_ft": sigmoid_params.get("E5-quora-finetuned", [10.0, 0.73]),
        "e5": sigmoid_params.get("E5-base-v2", [8.0, 0.82]),
        "bge": sigmoid_params.get("BGE-base-en-v1.5", [15.6755, 0.8591]),
        "mpnet": sigmoid_params.get("MPNet-base-v2", [11.5976, 0.8133]),
    }
    steepness, midpoint = params_map.get(name, default_sigmoid)
    if isinstance(steepness, list):
        steepness, midpoint = steepness[0], steepness[1]

    q1s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q1s]
    q2s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q2s]
    q1_enc = [f"query: {q}" if use_e5_prefix else q for q in q1s_n]
    q2_enc = [f"passage: {q}" if use_e5_prefix else q for q in q2s_n]

    emb1 = model.encode(q1_enc, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    emb2 = model.encode(q2_enc, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    similarities = (emb1 * emb2).sum(axis=1)
    prob_dup = 1.0 / (1.0 + np.exp(-steepness * (similarities - midpoint)))
    prob_dup = np.array(prob_dup).flatten()
    prob_non = 1.0 - prob_dup
    preds = (prob_dup >= threshold).astype(int)
    return preds, prob_dup


def predict_cross_encoder_batch(entry, q1s, q2s, threshold):
    from ares.model_loader import load_model

    loaded = load_model(entry.display_name)
    model = loaded["model"]

    q1s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q1s]
    q2s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q2s]

    all_scores = model.predict(list(zip(q1s_n, q2s_n)), batch_size=64, apply_softmax=True, show_progress_bar=False)
    prob_dup = np.array(
        [
            float(s[1])
            if len(s) == 2
            else (
                float(s[2]) / (float(s[0]) + float(s[2]) + 1e-10)
                if len(s) >= 3
                else max(0.0, min(1.0, (float(s[0]) + 1) / 2))
            )
            for s in all_scores
        ]
    )
    prob_non = 1.0 - prob_dup
    preds = (prob_dup >= threshold).astype(int)
    return preds, prob_dup


def predict_ensemble_single(display_name, q1, q2, threshold):
    from ares.inference.dispatcher import InferenceDispatcher

    start = time.time()
    result = InferenceDispatcher.predict(display_name, q1, q2, threshold=threshold)
    elapsed = (time.time() - start) * 1000
    return result.predicted_label, result.prob_duplicate, elapsed


# ============================================================
# MODEL EVALUATION
# ============================================================

ALL_MODELS = [
    "TF-IDF + Logistic Regression (Week 2)",
    "TF-IDF + Linear SVM (Week 2)",
    "DistilBERT (Week 3)",
    "Improved DistilBERT (Week 4)",
    "BGE-base-en-v1.5",
    "E5-base-v2",
    "E5-quora-finetuned",
    "MPNet-base-v2",
    "DeBERTa-v3 Cross-Encoder",
    "Cross-Encoder-Quora (Trained)",
    "Semantic Ensemble",
]

BACKEND_MAP = {}


def get_backend(model_name):
    if model_name not in BACKEND_MAP:
        entry = find_entry(model_name)
        BACKEND_MAP[model_name] = entry.backend if entry else None
    return BACKEND_MAP[model_name]


def evaluate_model(model_name, q1s, q2s, y_true, max_samples=5000, ensemble_limit=500):
    print(f"\n{'=' * 60}")
    print(f"  Evaluating: {model_name}")
    print(f"{'=' * 60}")

    entry = find_entry(model_name)
    if entry is None:
        print(f"  ❌ Unknown model: {model_name}")
        return None

    backend = entry.backend
    threshold = _get_threshold_cfg(model_name)

    # Subsample for practical evaluation
    if max_samples and len(q1s) > max_samples and backend != ModelBackend.ENSEMBLE:
        idx = np.random.RandomState(42).choice(len(q1s), max_samples, replace=False)
        q1s = [q1s[i] for i in idx]
        q2s = [q2s[i] for i in idx]
        y_true = y_true[idx]

    # ---- LOADING ----
    load_start = time.time()
    load_success = True
    load_error = None
    try:
        if backend == ModelBackend.CLASSICAL_ML:
            pass
        elif backend in (ModelBackend.TRANSFORMER, ModelBackend.BI_ENCODER, ModelBackend.CROSS_ENCODER):
            from ares.model_loader import load_model

            _ = load_model(model_name)
        elif backend == ModelBackend.ENSEMBLE:
            pass
    except Exception as e:
        load_success = False
        load_error = str(e)
    load_time = time.time() - load_start

    if not load_success:
        print(f"  ❌ Load failed: {load_error}")
        return {
            "model_name": model_name,
            "backend": backend.value,
            "threshold": threshold,
            "load_success": False,
            "load_error": load_error,
            "load_time_s": load_time,
            "load_memory_mb": None,
        }

    # ---- PREDICTION ----
    pred_start = time.time()
    try:
        if backend == ModelBackend.CLASSICAL_ML:
            y_pred, y_prob = predict_classical_batch(entry, q1s, q2s, threshold)
            pred_time = time.time() - pred_start
            actual_n = len(y_true)
        elif backend == ModelBackend.TRANSFORMER:
            y_pred, y_prob = predict_transformer_batch(entry, q1s, q2s, threshold)
            pred_time = time.time() - pred_start
            actual_n = len(y_true)
        elif backend == ModelBackend.BI_ENCODER:
            y_pred, y_prob = predict_bi_encoder_batch(entry, q1s, q2s, threshold)
            pred_time = time.time() - pred_start
            actual_n = len(y_true)
        elif backend == ModelBackend.CROSS_ENCODER:
            y_pred, y_prob = predict_cross_encoder_batch(entry, q1s, q2s, threshold)
            pred_time = time.time() - pred_start
            actual_n = len(y_true)
        elif backend == ModelBackend.ENSEMBLE:
            subset_n = min(ensemble_limit, len(q1s))
            idx = np.random.RandomState(42).choice(len(q1s), subset_n, replace=False)
            y_pred = np.zeros(subset_n, dtype=int)
            y_prob = np.zeros(subset_n, dtype=float)
            y_true_subset = y_true[idx]
            q1s_sub = [q1s[i] for i in idx]
            q2s_sub = [q2s[i] for i in idx]
            for i in range(subset_n):
                pred, prob, _ = predict_ensemble_single(model_name, q1s_sub[i], q2s_sub[i], threshold)
                y_pred[i] = pred
                y_prob[i] = prob
            pred_time = time.time() - pred_start
            actual_n = subset_n
            y_true = y_true_subset
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    except Exception as e:
        print(f"  ❌ Prediction failed: {e}")
        return {
            "model_name": model_name,
            "backend": backend.value,
            "threshold": threshold,
            "load_success": True,
            "load_time_s": load_time,
            "prediction_failed": True,
            "pred_error": str(e),
        }

    metrics = compute_metrics(y_true, y_pred, y_prob)
    avg_latency = (pred_time / len(y_true)) * 1000 if len(y_true) > 0 else 0

    results = {
        "model_name": model_name,
        "backend": backend.value,
        "threshold": threshold,
        "load_success": True,
        "prediction_failed": False,
        "load_time_s": round(load_time, 3),
        "pred_time_s": round(pred_time, 3),
        "avg_latency_ms": round(avg_latency, 4),
        "n_pairs": len(y_true),
        **metrics,
    }

    print(f"  Load: {load_time:.2f}s | Predict: {pred_time:.1f}s | Latency: {avg_latency:.1f}ms/pair")
    print(f"  F1={metrics['f1']:.4f} Acc={metrics['accuracy']:.4f} ROC-AUC={metrics['roc_auc']:.4f}")
    print(f"  PR-AUC={metrics['pr_auc']:.4f} MCC={metrics['mcc']:.4f}")
    print(f"  ECE={metrics['ece']:.4f} Brier={metrics['brier_score']:.4f}")
    print(f"  Avg Conf={metrics['avg_confidence']:.4f}")
    tn, fp, fn, tp = (
        metrics["confusion_matrix"][0][0],
        metrics["confusion_matrix"][0][1],
        metrics["confusion_matrix"][1][0],
        metrics["confusion_matrix"][1][1],
    )
    print(f"  CM: TN={tn} FP={fp} FN={fn} TP={tp}")

    return results


# ============================================================
# MAIN
# ============================================================


def main():
    out_dir = Path(__file__).resolve().parent.parent / "evaluation_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  PHASE 11.1 — MODEL VALIDATION & BENCHMARK")
    print("  Evidence Collection — No Changes Made")
    print("=" * 60)

    # Load validation set
    print("\nLoading validation set...")
    _, val_df, _ = get_quora_splits()
    q1s = val_df["q1"].tolist()
    q2s = val_df["q2"].tolist()
    y_true = val_df["label"].values
    print(f"  Validation set: {len(val_df):,} pairs (dup rate: {y_true.mean():.3f})")

    all_results = []
    for model_name in ALL_MODELS:
        res = evaluate_model(model_name, q1s, q2s, y_true)
        if res:
            all_results.append(res)
        # Save incremental
        pd.DataFrame(all_results).to_csv(out_dir / "benchmark_raw.csv", index=False)

    # Build summary table
    summary = []
    for r in all_results:
        if r.get("load_success") and not r.get("prediction_failed"):
            summary.append(
                {
                    "model": r["model_name"],
                    "backend": r["backend"],
                    "f1": r["f1"],
                    "accuracy": r["accuracy"],
                    "precision": r["precision"],
                    "recall": r["recall"],
                    "roc_auc": r["roc_auc"],
                    "pr_auc": r["pr_auc"],
                    "mcc": r["mcc"],
                    "ece": r["ece"],
                    "brier_score": r["brier_score"],
                    "avg_confidence": r["avg_confidence"],
                    "avg_latency_ms": r["avg_latency_ms"],
                    "load_time_s": r["load_time_s"],
                    "threshold": r["threshold"],
                    "n_pairs": r["n_pairs"],
                }
            )
        else:
            summary.append(
                {
                    "model": r["model_name"],
                    "backend": r.get("backend", "?"),
                    "f1": None,
                    "accuracy": None,
                    "precision": None,
                    "recall": None,
                    "roc_auc": None,
                    "pr_auc": None,
                    "mcc": None,
                    "ece": None,
                    "brier_score": None,
                    "avg_confidence": None,
                    "avg_latency_ms": None,
                    "load_time_s": r.get("load_time_s"),
                    "threshold": r.get("threshold"),
                    "n_pairs": r.get("n_pairs", 0),
                    "error": r.get("load_error") or r.get("pred_error", "unknown"),
                }
            )

    df_summary = pd.DataFrame(summary)
    df_summary.to_csv(out_dir / "MODEL_RANKING.csv", index=False)
    print(f"\nResults saved to {out_dir}/")

    # Print ranking
    print("\n" + "=" * 60)
    print("  RANKING (by F1)")
    print("=" * 60)
    ranked = [s for s in summary if s["f1"] is not None]
    ranked.sort(key=lambda x: x["f1"], reverse=True)
    for i, r in enumerate(ranked):
        print(f"  {i + 1:2d}. {r['model']:>45s}  F1={r['f1']:.4f}  ECE={r['ece']:.4f}  Lat={r['avg_latency_ms']:.1f}ms")

    # Save detailed per-model results
    for r in all_results:
        fname = r["model_name"].replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
        fpath = out_dir / f"{fname}_results.json"
        with open(fpath, "w") as f:
            json.dump(r, f, indent=2, default=str)

    return df_summary


if __name__ == "__main__":
    main()
