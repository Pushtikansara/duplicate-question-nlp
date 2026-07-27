"""Phase 11.2 — Threshold Optimization & Confidence Calibration
Evidence collection only. No prediction logic changes."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

# ============================================================
# BATCH PREDICTION FUNCTIONS (copied from phase11_evaluation.py)
# to avoid import issues with tools/ directory
# ============================================================


def _classical_batch(entry, q1s, q2s, threshold):
    import joblib

    from ares._config import get_app_paths
    from duplicate_question_app._preprocessing import normalize_question

    paths = get_app_paths()
    model_dir = paths.models_dir / "week2_models"
    if entry.internal_id == "week2_lr":
        path = model_dir / "logistic_regression.joblib"
    elif entry.internal_id == "week2_svm":
        path = model_dir / "linear_svm.joblib"
    else:
        raise ValueError(f"Unknown classical model: {entry.internal_id}")
    vec_path = model_dir / "tfidf_vectorizer.joblib"
    clf = joblib.load(path)
    vectorizer = joblib.load(vec_path)
    q1s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q1s]
    q2s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q2s]
    combined = [a + " " + b for a, b in zip(q1s_n, q2s_n, strict=False)]
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
    return (prob_dup >= threshold).astype(int), prob_dup


def _transformer_batch(entry, q1s, q2s, threshold, batch_size=64):
    import torch

    from ares._config import get_config
    from ares.model_loader import load_model
    from duplicate_question_app._preprocessing import normalize_question

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
        bq1 = q1s_n[i : i + batch_size]
        bq2 = q2s_n[i : i + batch_size]
        inputs = tokenizer(bq1, bq2, max_length=max_length, padding="max_length", truncation=True, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
        all_probs.append(probs[:, 1].cpu().numpy())
    prob_dup = np.concatenate(all_probs)
    return (prob_dup >= threshold).astype(int), prob_dup


def _bi_encoder_batch(entry, q1s, q2s, threshold):
    from ares._config import get_config
    from ares.model_loader import load_model
    from duplicate_question_app._preprocessing import normalize_question

    loaded = load_model(entry.display_name)
    model = loaded["model"]
    use_e5_prefix = loaded.get("use_e5_prefix", False)
    inf_cfg = get_config("inference") or {}
    sigmoid_params = inf_cfg.get("sigmoid_params", {})
    default_sigmoid = (15.0, 0.50)
    name = entry.internal_id
    pmap = {
        "e5_ft": sigmoid_params.get("E5-quora-finetuned", [10.0, 0.73]),
        "e5": sigmoid_params.get("E5-base-v2", [8.0, 0.82]),
        "bge": sigmoid_params.get("BGE-base-en-v1.5", [15.6755, 0.8591]),
        "mpnet": sigmoid_params.get("MPNet-base-v2", [11.5976, 0.8133]),
    }
    steepness, midpoint = pmap.get(name, default_sigmoid)
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
    return (prob_dup >= threshold).astype(int), prob_dup


def _cross_encoder_batch(entry, q1s, q2s, threshold):
    from ares.model_loader import load_model
    from duplicate_question_app._preprocessing import normalize_question

    loaded = load_model(entry.display_name)
    model = loaded["model"]
    q1s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q1s]
    q2s_n = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q2s]
    all_scores = model.predict(
        list(zip(q1s_n, q2s_n, strict=False)), batch_size=64, apply_softmax=True, show_progress_bar=False
    )
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
    return (prob_dup >= threshold).astype(int), prob_dup


# ============================================================
# METRICS
# ============================================================


def compute_threshold_metrics(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        f1_score,
        matthews_corrcoef,
        precision_score,
        recall_score,
    )

    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    mcc = matthews_corrcoef(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return {
        "threshold": float(threshold),
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "mcc": float(mcc),
        "balanced_accuracy": float(bal_acc),
        "specificity": float(specificity),
        "false_positive_rate": float(fpr),
        "false_negative_rate": float(fnr),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def compute_ece(probs, labels, n_bins=10):
    bb = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for bl, bu in zip(bb[:-1], bb[1:], strict=False):
        in_bin = (probs >= bl) & (probs < bu)
        if in_bin.sum() > 0:
            bin_acc = labels[in_bin].mean()
            bin_conf = probs[in_bin].mean()
            ece += np.abs(bin_acc - bin_conf) * in_bin.sum()
    return float(ece / len(labels))


def compute_mce(probs, labels, n_bins=10):
    bb = np.linspace(0, 1, n_bins + 1)
    max_cal_err = 0.0
    for bl, bu in zip(bb[:-1], bb[1:], strict=False):
        in_bin = (probs >= bl) & (probs < bu)
        if in_bin.sum() > 0:
            bin_acc = labels[in_bin].mean()
            bin_conf = probs[in_bin].mean()
            max_cal_err = max(max_cal_err, abs(bin_acc - bin_conf))
    return float(max_cal_err)


def compute_brier(y_true, y_prob):
    return float(np.mean((y_prob - y_true) ** 2))


def reliability_diagram(probs, labels, n_bins=10):
    bb = np.linspace(0, 1, n_bins + 1)
    bins = []
    for bl, bu in zip(bb[:-1], bb[1:], strict=False):
        in_bin = (probs >= bl) & (probs < bu)
        count = int(in_bin.sum())
        if count > 0:
            bins.append(
                {
                    "bin_lower": float(bl),
                    "bin_upper": float(bu),
                    "count": count,
                    "accuracy": float(labels[in_bin].mean()),
                    "confidence": float(probs[in_bin].mean()),
                }
            )
    return bins


# ============================================================
# THRESHOLD SWEEP
# ============================================================


def threshold_sweep(y_true, y_prob, step=0.01):
    thresholds = np.arange(0.0, 1.0 + step, step)
    results = []
    for t in thresholds:
        results.append(compute_threshold_metrics(y_true, y_prob, t))
    return results


def find_best_thresholds(results, y_true, y_prob):
    best = {}
    for metric in ["f1", "accuracy", "mcc", "balanced_accuracy"]:
        best_idx = int(np.argmax([r[metric] for r in results]))
        best[metric] = results[best_idx]

    # Minimal cost threshold (F1-optimal is usually close)
    best["f1_based"] = best["f1"]

    # Also find threshold closest to ECE=0 (best calibrated)
    eces = []
    for _ in results:
        eces.append(compute_ece(y_prob, y_true))
    best_ece_idx = int(np.argmin(eces))
    best["lowest_ece"] = results[best_ece_idx]

    return best


# ============================================================
# CALIBRATION METHODS
# ============================================================


def temperature_scaling(logits, y_true_val, y_true_test, y_prob_test):
    """Find optimal temperature on validation set, apply to test."""
    from scipy.optimize import minimize_scalar

    def nll_loss(T):
        scaled = logits / max(T, 1e-10)
        probs = 1.0 / (1.0 + np.exp(-scaled))
        probs = np.clip(probs, 1e-15, 1 - 1e-15)
        return -np.mean(y_true_val * np.log(probs) + (1 - y_true_val) * np.log(1 - probs))

    result = minimize_scalar(nll_loss, bounds=(0.1, 10.0), method="bounded")
    optimal_T = result.x
    return optimal_T


def platt_scaling(scores, y_true_val, y_true_test, y_prob_test):
    """Fit Platt scaling (logistic regression) to scores."""
    from sklearn.linear_model import LogisticRegression

    lr = LogisticRegression(C=1e10, solver="lbfgs")
    lr.fit(scores.reshape(-1, 1), y_true_val)
    cal_probs = lr.predict_proba(scores.reshape(-1, 1))[:, 1]
    return cal_probs, lr


def isotonic_regression(scores, y_true_val, y_true_test, y_prob_test):
    """Fit isotonic regression for calibration."""
    from sklearn.isotonic import IsotonicRegression

    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(scores, y_true_val)
    cal_probs = iso.predict(scores)
    cal_probs = np.clip(cal_probs, 0.0, 1.0)
    return cal_probs, iso


# ============================================================
# GENERATE PREDICTIONS FOR ALL MODELS
# ============================================================

WORKING_MODELS = [
    "DistilBERT (Week 3)",
    "Improved DistilBERT (Week 4)",
    "BGE-base-en-v1.5",
    "E5-base-v2",
    "E5-quora-finetuned",
    "MPNet-base-v2",
    "Cross-Encoder-Quora (Trained)",
]


def generate_all_predictions(val_df, n_samples=5000, output_dir=None):
    """Generate and save predictions for all working models."""

    np.random.seed(42)
    idx = np.random.choice(len(val_df), n_samples, replace=False)
    q1s = val_df["q1"].values[idx]
    q2s = val_df["q2"].values[idx]
    y_true = val_df["label"].values[idx]

    all_data = {"q1": q1s.tolist(), "q2": q2s.tolist(), "y_true": y_true.tolist(), "idx": idx.tolist()}

    from ares.model_registry import ModelBackend, find_entry

    for model_name in WORKING_MODELS:
        print(f"\n=== Predicting: {model_name} ===")
        entry = find_entry(model_name)
        backend = entry.backend

        start = time.time()
        try:
            if backend == ModelBackend.TRANSFORMER:
                thresh = 0.5
                y_pred, y_prob = _transformer_batch(entry, q1s.tolist(), q2s.tolist(), thresh)
            elif backend == ModelBackend.BI_ENCODER:
                from ares._config import get_config

                inf_cfg = get_config("inference") or {}
                thresholds = inf_cfg.get("per_model_thresholds", {})
                thresh = float(thresholds.get(model_name, 0.5))
                y_pred, y_prob = _bi_encoder_batch(entry, q1s.tolist(), q2s.tolist(), thresh)
            elif backend == ModelBackend.CROSS_ENCODER:
                from ares._config import get_config

                inf_cfg = get_config("inference") or {}
                thresholds = inf_cfg.get("per_model_thresholds", {})
                thresh = float(thresholds.get(model_name, 0.5))
                y_pred, y_prob = _cross_encoder_batch(entry, q1s.tolist(), q2s.tolist(), thresh)
            else:
                print(f"  Skipping backend {backend}")
                continue

            elapsed = time.time() - start
            all_data[model_name] = {
                "y_pred": y_pred.tolist(),
                "y_prob": y_prob.tolist(),
                "threshold": thresh,
                "time_s": round(elapsed, 2),
            }
            print(f"  Done in {elapsed:.1f}s")

        except Exception as e:
            print(f"  FAILED: {e}")
            all_data[model_name] = {"error": str(e)}

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "all_predictions.json", "w") as f:
            json.dump(all_data, f, indent=2, default=str)
        print(f"\nSaved to {output_dir / 'all_predictions.json'}")

    return all_data


# ============================================================
# MAIN ANALYSIS
# ============================================================


def main():
    out_dir = Path(__file__).resolve().parent.parent / "evaluation_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  PHASE 11.2 — THRESHOLD OPTIMIZATION & CALIBRATION")
    print("  Evidence Collection — No Model Changes")
    print("=" * 60)

    # Load validation data
    print("\nLoading validation set...")
    from duplicate_question_app._dataset.loader import get_quora_splits

    _, val_df, _ = get_quora_splits()

    # Generate or load predictions
    pred_path = out_dir / "all_predictions.json"
    if pred_path.exists():
        print("Loading cached predictions...")
        with open(pred_path) as f:
            all_data = json.load(f)
    else:
        all_data = generate_all_predictions(val_df, n_samples=5000, output_dir=out_dir)

    y_true = np.array(all_data["y_true"])
    n = len(y_true)
    print(f"\nValidation set: {n:,} pairs (dup rate: {y_true.mean():.3f})")

    # ============================================================
    # THRESHOLD SWEEP FOR EACH MODEL
    # ============================================================
    print("\n" + "=" * 60)
    print("  THRESHOLD SWEEP ANALYSIS")
    print("=" * 60)

    sweep_results = {}
    for model_name in WORKING_MODELS:
        if model_name not in all_data or "y_prob" not in all_data[model_name]:
            print(f"\n  {model_name}: SKIP (no prediction data)")
            continue

        y_prob = np.array(all_data[model_name]["y_prob"])
        current_thresh = all_data[model_name]["threshold"]

        print(f"\n  {model_name} (current threshold={current_thresh}):")

        sweep = threshold_sweep(y_true, y_prob)
        best = find_best_thresholds(sweep, y_true, y_prob)

        # Compute metric at current threshold
        current = compute_threshold_metrics(y_true, y_prob, current_thresh)
        current_ece = compute_ece(y_prob, y_true)
        current_brier = compute_brier(y_true, y_prob)

        print(f"    Current: F1={current['f1']:.4f}, ECE={current_ece:.4f}")
        print(f"    Best F1:   threshold={best['f1']['threshold']:.2f}, F1={best['f1']['f1']:.4f}")
        print(f"    Best Acc:  threshold={best['accuracy']['threshold']:.2f}, Acc={best['accuracy']['accuracy']:.4f}")
        print(f"    Best MCC:  threshold={best['mcc']['threshold']:.2f}, MCC={best['mcc']['mcc']:.4f}")
        print(
            f"    Best BalAcc: threshold={best['balanced_accuracy']['threshold']:.2f}, BalAcc={best['balanced_accuracy']['balanced_accuracy']:.4f}"
        )

        sweep_results[model_name] = {
            "current_threshold": current_thresh,
            "current": current,
            "current_ece": current_ece,
            "current_brier": current_brier,
            "best_f1": best["f1"],
            "best_accuracy": best["accuracy"],
            "best_mcc": best["mcc"],
            "best_balanced_accuracy": best["balanced_accuracy"],
            "sweep": sweep,
            "reliability": reliability_diagram(y_prob, y_true),
        }

    # Save sweep results
    sweep_save = {}
    for k, v in sweep_results.items():
        sweep_save[k] = {kk: vv for kk, vv in v.items() if kk != "sweep"}
        if "sweep" in v:
            sweep_save[k]["sweep"] = [{kkk: vvv for kkk, vvv in r.items()} for r in v["sweep"]]
        if "reliability" in v:
            sweep_save[k]["reliability"] = v["reliability"]
    with open(out_dir / "threshold_sweep_results.json", "w") as f:
        json.dump(sweep_save, f, indent=2, default=str)
    print(f"\nSweep results saved to {out_dir / 'threshold_sweep_results.json'}")

    # ============================================================
    # CALIBRATION ANALYSIS
    # ============================================================
    print("\n" + "=" * 60)
    print("  CALIBRATION ANALYSIS")
    print("=" * 60)

    cal_table = []
    for model_name in WORKING_MODELS:
        if model_name not in sweep_results:
            continue

        v = sweep_results[model_name]
        y_prob = np.array(all_data[model_name]["y_prob"])
        current_thresh = v["current_threshold"]

        ece = compute_ece(y_prob, y_true)
        mce = compute_mce(y_prob, y_true)
        brier = compute_brier(y_true, y_prob)

        cal_table.append(
            {
                "model": model_name,
                "current_threshold": current_thresh,
                "current_f1": round(v["current"]["f1"], 4),
                "best_f1_threshold": round(v["best_f1"]["threshold"], 2),
                "best_f1": round(v["best_f1"]["f1"], 4),
                "f1_gain": round(v["best_f1"]["f1"] - v["current"]["f1"], 4),
                "ece": round(ece, 4),
                "mce": round(mce, 4),
                "brier": round(brier, 4),
                "n": n,
            }
        )
        print(f"\n  {model_name}:")
        print(f"    ECE={ece:.4f}  MCE={mce:.4f}  Brier={brier:.4f}")
        print(f"    Current F1={v['current']['f1']:.4f} @ thresh={current_thresh}")
        print(f"    Optimal F1={v['best_f1']['f1']:.4f} @ thresh={v['best_f1']['threshold']:.2f}")
        print(f"    F1 Gain={v['best_f1']['f1'] - v['current']['f1']:.4f}")

    # Save calibration table
    import csv

    with open(out_dir / "MODEL_CALIBRATION_TABLE.csv", "w", newline="") as f:
        if cal_table:
            w = csv.DictWriter(f, fieldnames=cal_table[0].keys())
            w.writeheader()
            w.writerows(cal_table)
    print(f"\nCalibration table saved to {out_dir / 'MODEL_CALIBRATION_TABLE.csv'}")

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for row in cal_table:
        flag = ""
        if row["f1_gain"] > 0.01:
            flag = " ⚠️ RETUNE THRESHOLD"
        elif abs(row["f1_gain"]) <= 0.01:
            flag = " ✅ Optimal"
        print(
            f"  {row['model']:>40s}: thresh={row['current_threshold']:.2f}→{row['best_f1_threshold']:.2f} "
            f"F1={row['current_f1']:.4f}→{row['best_f1']:.4f} ({row['f1_gain']:+.4f}){flag}"
        )

    return sweep_results


if __name__ == "__main__":
    main()
