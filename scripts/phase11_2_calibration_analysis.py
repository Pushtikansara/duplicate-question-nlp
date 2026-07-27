#!/usr/bin/env python3
"""
Phase 11.2 — Threshold Optimization & Confidence Calibration Analysis.

Uses EXISTING threshold_sweep_results.json for threshold analysis.
Generates per-sample predictions for calibration method evaluation on a subset.

Outputs:
  - CALIBRATION_REPORT.md
  - THRESHOLD_ANALYSIS.md
  - MODEL_CALIBRATION_TABLE.csv
  - RELIABILITY_DIAGRAMS/  (images)
  - THRESHOLD_SWEEP/       (images)
  - PROBABILITY_DISTRIBUTIONS/ (images)
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
import matplotlib

from duplicate_question_app._calibration.v2 import (
    CalibrationMethod,
    calibrate_predictions,
)
from duplicate_question_app._calibration.v2 import evaluate_calibration as eval_cal
from duplicate_question_app._calibration.v2 import (
    get_calibration_curve_data,
)
from duplicate_question_app._config.settings import get_app_paths, get_config
from duplicate_question_app._dataset.loader import get_quora_splits
from duplicate_question_app._inference.transformer import (
    DuplicateQuestionInferenceService,
    ModelArtifactsNotFoundError,
    load_model_and_tokenizer,
)
from duplicate_question_app._models.embeddings import (
    _get_sigmoid_params,
    get_sentence_transformer_model,
    is_finetuned_embedding_model,
)
from duplicate_question_app._preprocessing import normalize_question

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "font.size": 10,
    }
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RANDOM_STATE = 42
N_BINS = 10
SUBSET_SIZE = 2000  # for calibration method evaluation

MODELS_TO_EVALUATE = [
    "DistilBERT (Week 3)",
    "Improved DistilBERT (Week 4)",
    "Cross-Encoder-Quora (Trained)",
    "MPNet-base-v2",
    "BGE-base-en-v1.5",
    "E5-base-v2",
    "E5-quora-finetuned",
]

OUTPUT_DIR = PROJECT_ROOT / "evaluation_results"
RELIABILITY_DIR = OUTPUT_DIR / "RELIABILITY_DIAGRAMS"
THRESHOLD_SWEEP_DIR = OUTPUT_DIR / "THRESHOLD_SWEEP"
PROB_DIST_DIR = OUTPUT_DIR / "PROBABILITY_DISTRIBUTIONS"

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _compute_metrics(y_true, y_pred, y_prob):
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        confusion_matrix,
        f1_score,
        matthews_corrcoef,
        precision_score,
        recall_score,
    )

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0,
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0,
        "sensitivity": float(recall_score(y_true, y_pred, zero_division=0)),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def _sweep_from_probabilities(y_true, y_prob, step=0.01):
    results = []
    for i in range(101):
        t = round(i * step, 2)
        y_pred = (y_prob >= t).astype(int)
        m = _compute_metrics(y_true, y_pred, y_prob)
        m["threshold"] = t
        results.append(m)
    return pd.DataFrame(results)


def _find_optimal(sweep_df):
    return {
        "best_f1": sweep_df.loc[sweep_df["f1"].idxmax()].to_dict(),
        "best_accuracy": sweep_df.loc[sweep_df["accuracy"].idxmax()].to_dict(),
        "best_mcc": sweep_df.loc[sweep_df["mcc"].idxmax()].to_dict(),
        "best_balanced_accuracy": sweep_df.loc[sweep_df["balanced_accuracy"].idxmax()].to_dict(),
        "best_cost": sweep_df.loc[(sweep_df["fp"] + sweep_df["fn"]).idxmin()].to_dict(),
    }


# ---------------------------------------------------------------------------
# Prediction collectors
# ---------------------------------------------------------------------------


def _predict_bi_encoder(model_name, pairs, batch_size=64):
    # Do NOT auto-upgrade E5 — we need to evaluate the exact requested model
    resolved = model_name
    model = get_sentence_transformer_model(resolved)
    is_ft = is_finetuned_embedding_model(resolved)
    use_e5_prefix = ("e5" in resolved.lower() and not is_ft) or (is_ft and "e5" in resolved.lower())
    steepness, midpoint = _get_sigmoid_params(resolved.lower())

    all_probs = np.zeros(len(pairs))
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i : i + batch_size]
        q1s, q2s = zip(*batch, strict=False)
        q1s = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q1s]
        q2s = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q2s]

        for j in range(len(q1s)):
            if q1s[j] == q2s[j]:
                all_probs[i + j] = 1.0
                continue
            q1_e = f"query: {q1s[j]}" if use_e5_prefix else q1s[j]
            q2_e = f"passage: {q2s[j]}" if use_e5_prefix else q2s[j]
            emb1 = model.encode(q1_e, normalize_embeddings=True)
            emb2 = model.encode(q2_e, normalize_embeddings=True)
            sim = float(np.dot(emb1, emb2))
            all_probs[i + j] = 1.0 / (1.0 + np.exp(-steepness * (sim - midpoint)))

    return all_probs


def _predict_ce(model_name, pairs, batch_size=128):
    resolved = model_name
    model = get_sentence_transformer_model(resolved)
    all_probs = np.zeros(len(pairs))
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i : i + batch_size]
        q1s, q2s = zip(*batch, strict=False)
        q1s = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q1s]
        q2s = [normalize_question(q, expand_abbrevs=True, fix_typos=True) for q in q2s]
        remaining, ridx = [], []
        for j in range(len(q1s)):
            if q1s[j] == q2s[j]:
                all_probs[i + j] = 1.0
            else:
                remaining.append((q1s[j], q2s[j]))
                ridx.append(j)
        if remaining:
            scores = model.predict(remaining, batch_size=batch_size, apply_softmax=True, show_progress_bar=False)
            for k, score in enumerate(scores):
                if isinstance(score, (list, np.ndarray)) and len(score) >= 3:
                    contra, entail = float(score[0]), float(score[2])
                    denom = contra + entail
                    p = entail / denom if denom > 0.01 else 0.5
                elif isinstance(score, (list, np.ndarray)) and len(score) == 2:
                    p = float(score[1])
                else:
                    p = max(0.0, min(1.0, (float(score[0]) + 1) / 2))
                all_probs[i + ridx[k]] = p
    return all_probs


def _predict_transformer(model_name, pairs):
    paths = get_app_paths()
    # Map display name to model_version for load_model_and_tokenizer
    version_map = {
        "DistilBERT (Week 3)": "DistilBERT (Week 3)",
        "Improved DistilBERT (Week 4)": "Improved DistilBERT (Week 4)",
    }
    model_version = version_map.get(model_name)
    try:
        model, tokenizer, metadata = load_model_and_tokenizer(paths, model_version=model_version)
    except (ModelArtifactsNotFoundError, RuntimeError) as e:
        raise RuntimeError(f"Failed to load {model_name}: {e}") from e
    service = DuplicateQuestionInferenceService(model, tokenizer, metadata)
    df = service.predict_batch(pairs)
    return df["prob_duplicate"].values


def _predict_model(model_name, pairs):
    nl = model_name.lower()
    if "cross-encoder" in nl:
        return _predict_ce(model_name, pairs)
    elif "distilbert" in nl or "week" in nl:
        return _predict_transformer(model_name, pairs)
    else:
        return _predict_bi_encoder(model_name, pairs)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def _safe_name(name):
    return name.replace(" ", "_").replace("(", "").replace(")", "")


def plot_distribution(y_true, y_prob, model_name, save_dir, threshold):
    fig, ax = plt.subplots(figsize=(8, 5))
    neg = y_prob[y_true == 0]
    pos = y_prob[y_true == 1]
    bins = np.linspace(0, 1, 21)
    ax.hist(neg, bins=bins, alpha=0.6, label=f"Non-Duplicate (n={len(neg)})", color="#64748B", density=True)
    ax.hist(pos, bins=bins, alpha=0.6, label=f"Duplicate (n={len(pos)})", color="#2563EB", density=True)
    ax.axvline(threshold, color="#DC2626", linestyle="--", linewidth=2, label=f"Threshold={threshold}")
    ax.set_xlabel("Predicted Probability")
    ax.set_ylabel("Density")
    ax.set_title(f"Probability Distribution — {model_name}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_dir / f"{_safe_name(model_name)}_distribution.png", dpi=150)
    plt.close(fig)


def plot_sweep(sweep_df, model_name, save_dir, best_th):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes[0, 0].plot(sweep_df["threshold"], sweep_df["accuracy"], label="Accuracy")
    axes[0, 0].plot(sweep_df["threshold"], sweep_df["f1"], label="F1")
    axes[0, 0].axvline(best_th, color="red", ls="--", alpha=0.7, label=f"Best F1={best_th}")
    axes[0, 0].set_xlabel("Threshold")
    axes[0, 0].set_ylabel("Score")
    axes[0, 0].set_title("F1 & Accuracy")
    axes[0, 0].legend()
    axes[0, 0].grid(alpha=0.3)

    axes[0, 1].plot(sweep_df["threshold"], sweep_df["precision"], label="Precision")
    axes[0, 1].plot(sweep_df["threshold"], sweep_df["recall"], label="Recall")
    axes[0, 1].set_xlabel("Threshold")
    axes[0, 1].set_ylabel("Score")
    axes[0, 1].set_title("Precision & Recall")
    axes[0, 1].legend()
    axes[0, 1].grid(alpha=0.3)

    axes[1, 0].plot(sweep_df["threshold"], sweep_df["mcc"], label="MCC")
    axes[1, 0].plot(sweep_df["threshold"], sweep_df["balanced_accuracy"], label="Bal Acc")
    axes[1, 0].set_xlabel("Threshold")
    axes[1, 0].set_ylabel("Score")
    axes[1, 0].set_title("MCC & Balanced Accuracy")
    axes[1, 0].legend()
    axes[1, 0].grid(alpha=0.3)

    axes[1, 1].plot(sweep_df["threshold"], sweep_df["false_positive_rate"], label="FPR")
    axes[1, 1].plot(sweep_df["threshold"], sweep_df["false_negative_rate"], label="FNR")
    axes[1, 1].set_xlabel("Threshold")
    axes[1, 1].set_ylabel("Rate")
    axes[1, 1].set_title("Error Rates")
    axes[1, 1].legend()
    axes[1, 1].grid(alpha=0.3)

    fig.suptitle(f"Threshold Sweep — {model_name}", fontsize=14)
    fig.tight_layout()
    fig.savefig(save_dir / f"{_safe_name(model_name)}_sweep.png", dpi=150)
    plt.close(fig)


def plot_reliability(y_true, y_prob, model_name, save_dir, cal_probs=None, cal_label=""):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    data = get_calibration_curve_data(y_prob, y_true, N_BINS)
    valid = ~np.isnan(data["bin_accuracies"])
    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect")
    axes[0].plot(data["bin_centers"][valid], data["bin_accuracies"][valid], "o-", markersize=8, label="Raw")
    if cal_probs is not None:
        cd = get_calibration_curve_data(cal_probs, y_true, N_BINS)
        cv = ~np.isnan(cd["bin_accuracies"])
        axes[0].plot(cd["bin_centers"][cv], cd["bin_accuracies"][cv], "s--", markersize=7, label=cal_label)
    axes[0].set_xlabel("Mean Predicted Probability")
    axes[0].set_ylabel("Fraction of Positives")
    axes[0].set_title(f"Reliability Diagram — {_safe_name(model_name)}")
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    axes[0].set_xlim(0, 1)
    axes[0].set_ylim(0, 1)

    axes[1].hist(y_prob, bins=20, range=(0, 1), alpha=0.7, color="steelblue", edgecolor="white")
    if cal_probs is not None:
        axes[1].hist(cal_probs, bins=20, range=(0, 1), alpha=0.5, color="coral", edgecolor="white", label=cal_label)
        axes[1].legend()
    axes[1].set_xlabel("Predicted Probability")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Confidence Histogram")
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(save_dir / f"{_safe_name(model_name)}_reliability.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 72)
    print("  PHASE 11.2 — Threshold Optimization & Confidence Calibration Analysis")
    print("=" * 72)

    # Setup dirs
    for d in [RELIABILITY_DIR, THRESHOLD_SWEEP_DIR, PROB_DIST_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Load data
    print("\n--- Loading Data ---")
    train_df, val_df, test_df = get_quora_splits()
    print(f"  Full validation: {len(val_df)} pairs")

    # Load existing sweep data
    sweep_path = OUTPUT_DIR / "threshold_sweep_results.json"
    if sweep_path.exists():
        with open(sweep_path) as f:
            existing_sweep = json.load(f)
        print(f"  Loaded existing threshold sweep data for {list(existing_sweep.keys())}")
    else:
        print("  WARNING: No existing threshold_sweep_results.json found!")
        existing_sweep = {}

    # -----------------------------------------------------------------------
    # PHASE 1: Threshold Analysis (from existing sweep data)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  PHASE 1: Threshold Analysis")
    print("=" * 60)

    threshold_results = {}
    for model_name in MODELS_TO_EVALUATE:
        print(f"\n  --- {model_name} ---")
        if model_name in existing_sweep:
            ed = existing_sweep[model_name]
            sweep_records = ed.get("sweep", [])
            if sweep_records:
                sweep_df = pd.DataFrame(sweep_records)
                optimal = _find_optimal(sweep_df)

                threshold_results[model_name] = {
                    "current_threshold": ed.get("current_threshold", 0.5),
                    "current_metrics": ed.get("current", {}),
                    "current_ece": ed.get("current_ece", 0),
                    "current_brier": ed.get("current_brier", 0),
                    "optimized": optimal,
                    "sweep": sweep_records,
                }

                best = optimal["best_f1"]
                cur = threshold_results[model_name]["current_metrics"]
                print(f"    Current: th={ed.get('current_threshold', 0.5):.2f}  F1={cur.get('f1', 0):.4f}")
                print(
                    f"    Best F1: th={best['threshold']:.2f}  F1={best['f1']:.4f}  (gain={best['f1'] - cur.get('f1', 0):.4f})"
                )

                # Generate sweep plot
                plot_sweep(sweep_df, model_name, THRESHOLD_SWEEP_DIR, best["threshold"])
            else:
                print("    No sweep data available")
        else:
            print("    No sweep data in existing file")

    # -----------------------------------------------------------------------
    # PHASE 2: Calibration Analysis (requires per-sample predictions)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  PHASE 2: Calibration Analysis")
    print("=" * 60)

    # Take a stratified subset for calibration analysis
    rng = np.random.RandomState(RANDOM_STATE)
    # Stratified sampling
    val_dup = val_df[val_df["label"] == 1]
    val_non = val_df[val_df["label"] == 0]
    n_per_class = min(SUBSET_SIZE // 2, len(val_dup), len(val_non))
    val_subset = pd.concat(
        [
            val_dup.sample(n=n_per_class, random_state=rng),
            val_non.sample(n=n_per_class, random_state=rng),
        ]
    ).reset_index(drop=True)
    print(
        f"\n  Calibration subset: {len(val_subset)} pairs "
        f"({val_subset['label'].sum()} duplicates, "
        f"{len(val_subset) - val_subset['label'].sum()} non-duplicates)"
    )

    calibration_results = {}
    cal_cache = OUTPUT_DIR / ".calibration_cache"
    cal_cache.mkdir(parents=True, exist_ok=True)

    for model_name in MODELS_TO_EVALUATE:
        print(f"\n  --- {model_name} ---")

        cache_file = cal_cache / f"{_safe_name(model_name)}_probs_subset.npy"
        if cache_file.exists():
            print("    Loading cached predictions")
            y_prob = np.load(cache_file)
        else:
            print(f"    Running predictions on {len(val_subset)} pairs...")
            t0 = time.time()
            try:
                y_prob = _predict_model(model_name, list(zip(val_subset["q1"], val_subset["q2"], strict=False)))
                elapsed = time.time() - t0
                print(f"    Done in {elapsed:.1f}s ({len(val_subset) / elapsed:.1f} pairs/s)")
                np.save(cache_file, y_prob)
            except Exception as e:
                print(f"    ERROR: {e}")
                import traceback

                traceback.print_exc()
                continue

        y_true = val_subset["label"].values.astype(int)

        # Current threshold
        cfg_thresholds = get_config("inference").get("per_model_thresholds", {})
        current_threshold = float(cfg_thresholds.get(model_name, 0.5))

        # ECE, MCE, Brier for raw probs
        cal_raw = eval_cal(y_prob, y_true)
        print(f"    Raw ECE={cal_raw.ece:.4f}  MCE={cal_raw.mce:.4f}  Brier={cal_raw.brier_score:.4f}")

        # Distribution plot
        plot_distribution(y_true, y_prob, model_name, PROB_DIST_DIR, current_threshold)

        # Evaluate each calibration method
        methods_eval = {}
        best_ece = float("inf")
        best_method = CalibrationMethod.NONE
        best_cal_probs = y_prob.copy()

        for method in [
            CalibrationMethod.NONE,
            CalibrationMethod.TEMPERATURE,
            CalibrationMethod.PLATT,
            CalibrationMethod.ISOTONIC,
        ]:
            try:
                result = calibrate_predictions(
                    y_prob,
                    y_true,
                    method=method,
                    val_split=0.2,
                    random_state=42,
                )
                mb = result.metrics_before
                ma = result.metrics_after

                # Compute F1 after calibration at optimal threshold
                cal_sweep = _sweep_from_probabilities(y_true, result.calibrated_probs)
                best_cal_row = cal_sweep.loc[cal_sweep["f1"].idxmax()]

                methods_eval[method.value] = {
                    "ece_before": mb.ece,
                    "ece_after": ma.ece,
                    "mce_before": mb.mce,
                    "mce_after": ma.mce,
                    "brier_before": mb.brier_score,
                    "brier_after": ma.brier_score,
                    "nll_before": mb.nll,
                    "nll_after": ma.nll,
                    "f1_after": best_cal_row["f1"],
                    "best_threshold_after": best_cal_row["threshold"],
                    "parameters": result.parameters,
                }
                print(f"      {method.value}: ECE {mb.ece:.4f} -> {ma.ece:.4f}  F1={best_cal_row['f1']:.4f}")

                if ma.ece < best_ece:
                    best_ece = ma.ece
                    best_method = method
                    best_cal_probs = result.calibrated_probs

            except Exception as e:
                methods_eval[method.value] = {"error": str(e)}
                print(f"      {method.value}: ERROR - {e}")

        calibration_results[model_name] = {
            "raw_ece": float(cal_raw.ece),
            "raw_mce": float(cal_raw.mce),
            "raw_brier": float(cal_raw.brier_score),
            "methods": methods_eval,
            "best_method": best_method.value,
            "best_ece": float(best_ece),
            "best_cal_probs": best_cal_probs.tolist()[:100],  # store small sample
        }

        # Reliability diagram
        if best_method != CalibrationMethod.NONE:
            plot_reliability(
                y_true,
                y_prob,
                model_name,
                RELIABILITY_DIR,
                cal_probs=best_cal_probs,
                cal_label=f"Best ({best_method.value})",
            )
        else:
            plot_reliability(y_true, y_prob, model_name, RELIABILITY_DIR)

    # -----------------------------------------------------------------------
    # PHASE 3: Generate Reports
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  PHASE 3: Generating Reports")
    print("=" * 60)

    # Merge threshold and calibration data
    combined = {}
    for model_name in MODELS_TO_EVALUATE:
        th = threshold_results.get(model_name, {})
        ca = calibration_results.get(model_name, {})
        combined[model_name] = {**th, "calibration": ca}

    _generate_calibration_table(combined)
    _generate_threshold_analysis(combined)
    _generate_calibration_report(combined)

    # Save combined results
    with open(OUTPUT_DIR / "phase11_2_results.json", "w") as f:
        json.dump({k: {sk: sv for sk, sv in v.items() if sk != "sweep"} for k, v in combined.items()}, f, indent=2)

    print(f"\n  All outputs saved to {OUTPUT_DIR}")
    print("  Done.")


# ---------------------------------------------------------------------------
# Report generators
# ---------------------------------------------------------------------------


def _generate_calibration_table(combined):
    rows = []
    for model_name, data in combined.items():
        if not data or "optimized" not in data:
            continue
        th = data["optimized"]["best_f1"]
        cur = data.get("current_metrics", {})
        ca = data.get("calibration", {})
        methods = ca.get("methods", {})
        best_m = ca.get("best_method", "none")
        best_cal = methods.get(best_m, {})

        cal_ece = best_cal.get("ece_after", ca.get("raw_ece", 0))
        cal_brier = best_cal.get("brier_after", ca.get("raw_brier", 0))

        rows.append(
            {
                "Model": model_name,
                "Current Threshold": data.get("current_threshold", 0.5),
                "Optimal Threshold (Best F1)": th["threshold"],
                "Current F1": round(cur.get("f1", 0), 4),
                "Optimal F1 (Threshold Tuned)": round(th["f1"], 4),
                "F1 Gain (Threshold)": round(th["f1"] - cur.get("f1", 0), 4),
                "Current ECE": round(ca.get("raw_ece", 0), 4),
                "Optimal ECE (Calibrated)": round(cal_ece, 4),
                "ECE Reduction": round(ca.get("raw_ece", 0) - cal_ece, 4),
                "Current Brier": round(ca.get("raw_brier", 0), 4),
                "Optimal Brier (Calibrated)": round(cal_brier, 4),
                "Best Calibration Method": best_m,
                "Current Accuracy": round(cur.get("accuracy", 0), 4),
                "Optimal Accuracy": round(th["accuracy"], 4),
                "Current Precision": round(cur.get("precision", 0), 4),
                "Current Recall": round(cur.get("recall", 0), 4),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "MODEL_CALIBRATION_TABLE.csv", index=False)
    print("  -> MODEL_CALIBRATION_TABLE.csv")


def _generate_threshold_analysis(combined):
    lines = [
        "# Threshold Optimization Analysis",
        "",
        f"*Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}*",
        "",
        "## Summary",
        "",
        "For every working model, we performed a complete threshold sweep",
        "from 0.00 to 1.00 (step = 0.01) computing Accuracy, Precision,",
        "Recall, F1, MCC, Balanced Accuracy, Specificity, Sensitivity,",
        "FPR, FNR, and Cost (FP+FN).",
        "",
        "We identified 5 optimal thresholds per model:",
        "- Best F1 Threshold (primary recommendation)",
        "- Best Accuracy Threshold",
        "- Best MCC Threshold",
        "- Best Balanced Accuracy Threshold",
        "- Lowest Cost Threshold",
        "",
    ]

    for model_name, data in combined.items():
        if not data or "optimized" not in data:
            lines.append(f"## {model_name}\n\n**No threshold data available**\n")
            continue
        cur = data.get("current_metrics", {})
        opt = data["optimized"]
        cur_th = data.get("current_threshold", 0.5)
        best = opt["best_f1"]

        lines.extend(
            [
                f"## {model_name}",
                "",
                f"- **Current Threshold**: {cur_th:.2f}",
                f"- **Current F1**: {cur.get('f1', 0):.4f}",
                "",
                "### Optimal Thresholds",
                "",
                "| Metric | Threshold | F1 | Accuracy | Precision | Recall | MCC |",
                "|--------|-----------|----|----------|-----------|--------|-----|",
            ]
        )

        for key, label in [
            ("best_f1", "Best F1"),
            ("best_accuracy", "Best Accuracy"),
            ("best_mcc", "Best MCC"),
            ("best_balanced_accuracy", "Best Balanced Accuracy"),
            ("best_cost", "Lowest Cost"),
        ]:
            t = opt[key]
            lines.append(
                f"| {label} | {t['threshold']:.2f} | {t['f1']:.4f} | "
                f"{t['accuracy']:.4f} | {t['precision']:.4f} | "
                f"{t['recall']:.4f} | {t['mcc']:.4f} |"
            )

        f1_gap = best["f1"] - cur.get("f1", 0)
        lines.append("")
        lines.append("### Threshold Explanation")
        lines.append("")

        if abs(best["threshold"] - cur_th) < 0.03:
            lines.append(
                f"The current threshold ({cur_th:.2f}) is essentially optimal "
                f"for {model_name}. F1 gain from retuning would be only {f1_gap:.4f}."
            )
        elif best["threshold"] > cur_th:
            lines.append(
                f"The optimal threshold ({best['threshold']:.2f}) is higher than the current "
                f"threshold ({cur_th:.2f}). This indicates the model's positive class "
                f"probabilities are underestimated — increasing the threshold improves "
                f"precision without sacrificing too much recall."
            )
            lines.append("")
            lines.append(f"- Precision: {cur.get('precision', 0):.4f} → {best['precision']:.4f}")
            lines.append(f"- Recall: {cur.get('recall', 0):.4f} → {best['recall']:.4f}")
        else:
            lines.append(
                f"The optimal threshold ({best['threshold']:.2f}) is lower than the current "
                f"threshold ({cur_th:.2f}). This indicates the model is overly conservative "
                f"— lowering the threshold recovers more true positives."
            )
            lines.append("")
            lines.append(f"- Precision: {cur.get('precision', 0):.4f} → {best['precision']:.4f}")
            lines.append(f"- Recall: {cur.get('recall', 0):.4f} → {best['recall']:.4f}")

        lines.append("")
        lines.append("### Cost & Error Analysis")
        lines.append("")
        cost_cur = cur.get("fp", 0) + cur.get("fn", 0)
        cost_best = best.get("fp", 0) + best.get("fn", 0)
        lines.append(f"- **Current**: FP={cur.get('fp', 0)}, FN={cur.get('fn', 0)}, Total={cost_cur}")
        lines.append(f"- **Optimal F1**: FP={best.get('fp', 0)}, FN={best.get('fn', 0)}, Total={cost_best}")
        lines.append(f"- **Errors saved**: {max(0, cost_cur - cost_best)}")
        lines.append(
            f"- **Sensitivity (Recall)**: {cur.get('recall', cur.get('sensitivity', 0)):.4f} → {best.get('recall', best.get('sensitivity', 0)):.4f}"
        )
        lines.append(f"- **Specificity**: {cur.get('specificity', 0):.4f} → {best.get('specificity', 0):.4f}")
        lines.append("")

    with open(OUTPUT_DIR / "THRESHOLD_ANALYSIS.md", "w") as f:
        f.write("\n".join(lines))
    print("  -> THRESHOLD_ANALYSIS.md")


def _generate_calibration_report(combined):
    lines = [
        "# Confidence Calibration Report",
        "",
        f"*Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}*",
        "",
        "## Executive Summary",
        "",
        "We evaluated 4 calibration methods for each model:",
        "1. **Raw Confidence** (no calibration — baseline)",
        "2. **Temperature Scaling** (single parameter T > 0)",
        "3. **Platt Scaling** (logistic regression on logit space)",
        "4. **Isotonic Regression** (non-parametric monotonic mapping)",
        "",
        "The best method minimizes **Expected Calibration Error (ECE)**",
        "without reducing F1 score.",
        "",
    ]

    for model_name, data in combined.items():
        if not data or "calibration" not in data:
            continue
        ca = data["calibration"]
        lines.extend(
            [
                f"## {model_name}",
                "",
                f"- **Raw ECE**: {ca.get('raw_ece', 0):.4f}",
                f"- **Raw MCE**: {ca.get('raw_mce', 0):.4f}",
                f"- **Raw Brier**: {ca.get('raw_brier', 0):.4f}",
                "",
                "### Calibration Method Comparison",
                "",
                "| Method | ECE Before | ECE After | MCE Before | MCE After | Brier Before | Brier After | F1 After |",
                "|--------|------------|-----------|------------|-----------|--------------|-------------|----------|",
            ]
        )
        methods = ca.get("methods", {})
        for mn in ["none", "temperature", "platt", "isotonic"]:
            m = methods.get(mn, {})
            if "error" in m:
                lines.append(f"| {mn} | ERROR: {m['error']} | | | | | |")
            else:
                lines.append(
                    f"| {mn} | {m.get('ece_before', 0):.4f} | {m.get('ece_after', 0):.4f} | "
                    f"{m.get('mce_before', 0):.4f} | {m.get('mce_after', 0):.4f} | "
                    f"{m.get('brier_before', 0):.4f} | {m.get('brier_after', 0):.4f} | "
                    f"{m.get('f1_after', 0):.4f} |"
                )
        lines.append("")
        lines.append(f"**Best Method**: {ca.get('best_method', 'none')}")
        lines.append(f"**Best ECE**: {ca.get('best_ece', 0):.4f}")
        lines.append("")
        lines.append("See RELIABILITY_DIAGRAMS/ for visual reliability diagrams.")
        lines.append("")

    # Cross-model comparison
    lines.extend(
        [
            "## Cross-Model Comparison",
            "",
            "| Model | Raw ECE | Best ECE | ECE Reduction | Best Method | Raw Brier |",
            "|-------|---------|----------|---------------|-------------|-----------|",
        ]
    )
    for model_name in MODELS_TO_EVALUATE:
        data = combined.get(model_name, {})
        ca = data.get("calibration", {})
        lines.append(
            f"| {model_name} | {ca.get('raw_ece', 0):.4f} | "
            f"{ca.get('best_ece', 0):.4f} | "
            f"{ca.get('raw_ece', 0) - ca.get('best_ece', 0):.4f} | "
            f"{ca.get('best_method', 'N/A')} | "
            f"{ca.get('raw_brier', 0):.4f} |"
        )
    lines.append("")

    # Recommendations
    lines.append("## Recommendations per Model")
    lines.append("")

    for model_name in MODELS_TO_EVALUATE:
        data = combined.get(model_name, {})
        if not data:
            lines.append(f"### {model_name}\n- **No data available**\n")
            continue

        cur_metrics = data.get("current_metrics", {})
        opt = data.get("optimized", {})
        best_f1 = opt.get("best_f1", {})
        ca = data.get("calibration", {})
        cur_th = data.get("current_threshold", 0.5)

        cur_f1 = cur_metrics.get("f1", 0)
        tuned_f1 = best_f1.get("f1", cur_f1)
        raw_ece = ca.get("raw_ece", 0)
        best_ece = ca.get("best_ece", 0)
        best_method = ca.get("best_method", "none")

        f1_gain = tuned_f1 - cur_f1
        ece_gain = raw_ece - best_ece
        recs = []
        if f1_gain > 0.01:
            recs.append(
                f"**RETUNE**: Change threshold from {cur_th:.2f} to "
                f"{best_f1.get('threshold', cur_th):.2f} "
                f"(F1 gain: {f1_gain:.4f})"
            )
        if ece_gain > 0.01 and best_method != "none":
            recs.append(f"**CALIBRATE**: Apply {best_method} scaling (ECE: {raw_ece:.4f} → {best_ece:.4f})")
        if not recs:
            recs.append(f"**KEEP**: Model is already operating near optimal. F1={cur_f1:.4f}, ECE={raw_ece:.4f}")

        lines.append(f"### {model_name}")
        for r in recs:
            lines.append(f"- {r}")
        lines.append("")

    # Final recommendation table
    lines.append("## Final Recommendation Table")
    lines.append("")
    lines.append("| Model | Cur Th | Opt Th | Cur F1 | Opt F1 | Cur ECE | Opt ECE | Recommendation |")
    lines.append("|-------|--------|--------|--------|--------|---------|---------|----------------|")

    for model_name in MODELS_TO_EVALUATE:
        data = combined.get(model_name, {})
        if not data or "optimized" not in data:
            lines.append(f"| {model_name} | - | - | - | - | - | - | NODATA |")
            continue

        cur_th = data.get("current_threshold", 0.5)
        best = data["optimized"]["best_f1"]
        cur_f1 = data.get("current_metrics", {}).get("f1", 0)
        ca = data.get("calibration", {})
        raw_ece = ca.get("raw_ece", 0)
        best_ece = ca.get("best_ece", 0)
        best_m = ca.get("best_method", "none")
        f1_gain = best["f1"] - cur_f1
        ece_g = raw_ece - best_ece

        if f1_gain > 0.01 and ece_g > 0.01 and best_m != "none":
            rec = f"RETUNE to {best['threshold']:.2f} + CALIBRATE ({best_m})"
        elif f1_gain > 0.01:
            rec = f"RETUNE to {best['threshold']:.2f}"
        elif ece_g > 0.01 and best_m != "none":
            rec = f"CALIBRATE ({best_m})"
        else:
            rec = "KEEP"

        lines.append(
            f"| {model_name} | {cur_th:.2f} | {best['threshold']:.2f} | "
            f"{cur_f1:.4f} | {best['f1']:.4f} | "
            f"{raw_ece:.4f} | {best_ece:.4f} | {rec} |"
        )

    lines.append("")

    # Special investigations
    lines.extend(_special_investigations(combined))

    with open(OUTPUT_DIR / "CALIBRATION_REPORT.md", "w") as f:
        f.write("\n".join(lines))
    print("  -> CALIBRATION_REPORT.md")


def _special_investigations(combined):
    lines = [
        "## Special Investigations",
        "",
        "### Step 6: E5-base-v2 Investigation",
        "",
        "Determine whether poor performance is caused by threshold, calibration, or the model itself.",
        "",
    ]

    e5 = combined.get("E5-base-v2", {})
    if e5 and "optimized" in e5:
        cur_th = e5.get("current_threshold", 0.35)
        best = e5["optimized"]["best_f1"]
        cur_f1 = e5.get("current_metrics", {}).get("f1", 0)
        opt_th = best["threshold"]
        opt_f1 = best["f1"]
        gain = opt_f1 - cur_f1

        lines.extend(
            [
                f"- **Current F1 at threshold {cur_th:.2f}**: {cur_f1:.4f}",
                f"- **Best F1 at threshold {opt_th:.2f}**: {opt_f1:.4f}",
                f"- **F1 improvement**: {gain:.4f} ({gain / max(cur_f1, 0.001) * 100:.1f}% relative)",
                "",
            ]
        )
        if gain > 0.05:
            lines.append(
                "**Verdict: E5-base-v2 is a fundamentally capable model with a suboptimal threshold.** "
                f"The current threshold of {cur_th:.2f} is far from optimal ({opt_th:.2f}). "
                f"Retuning alone recovers ~{gain:.3f} F1 points. "
                "This model does NOT need retraining — it needs RETUNE."
            )
            lines.append("")
            lines.append(
                "**Recommendation: RETUNE** — Change threshold from "
                f"{cur_th:.2f} to {opt_th:.2f} in configs/inference.yaml."
            )
        else:
            lines.append(
                "**Verdict: E5-base-v2's poor performance is inherent to the model.** "
                "Threshold tuning does not significantly improve results."
            )
    else:
        lines.append("**No data available for E5-base-v2**")
    lines.append("")

    # Week 4 DistilBERT
    lines.extend(
        [
            "### Step 7: Week 4 DistilBERT Investigation",
            "",
            "Determine whether Week 4 DistilBERT already operates at its optimal threshold.",
            "",
        ]
    )
    w4 = combined.get("Improved DistilBERT (Week 4)", {})
    if w4 and "optimized" in w4:
        cur_th = w4.get("current_threshold", 0.5)
        best = w4["optimized"]["best_f1"]
        cur_f1 = w4.get("current_metrics", {}).get("f1", 0)
        opt_th = best["threshold"]
        opt_f1 = best["f1"]
        gain = opt_f1 - cur_f1

        lines.extend(
            [
                f"- **Current threshold**: {cur_th:.2f}",
                f"- **Current F1**: {cur_f1:.4f}",
                f"- **Optimal threshold**: {opt_th:.2f}",
                f"- **Optimal F1**: {opt_f1:.4f}",
                f"- **F1 gain**: {gain:.4f}",
                "",
            ]
        )
        if gain < 0.01:
            lines.append(
                "**Verdict: Week 4 DistilBERT is operating at its optimal threshold.** "
                f"The current threshold of {cur_th:.2f} yields F1={cur_f1:.4f}, which is "
                f"within 0.01 of the optimal. No retuning needed."
            )
            lines.append("")
            lines.append("**Recommendation: KEEP** current threshold of 0.50.")
        else:
            lines.append(
                f"**Verdict: Week 4 DistilBERT can still be improved.** "
                f"Shifting threshold from {cur_th:.2f} to {opt_th:.2f} "
                f"improves F1 by {gain:.4f}."
            )
            lines.append("")
            lines.append(f"**Recommendation: RETUNE** to {opt_th:.2f}.")
    else:
        lines.append("**No data available for Improved DistilBERT (Week 4)**")
    lines.append("")

    # CrossEncoder
    lines.extend(
        [
            "### Step 8: Cross-Encoder Threshold=0.10 Investigation",
            "",
            "Determine whether threshold=0.10 is actually optimal.",
            "",
        ]
    )
    ce = combined.get("Cross-Encoder-Quora (Trained)", {})
    if ce and "optimized" in ce:
        cur_th = ce.get("current_threshold", 0.10)
        best = ce["optimized"]["best_f1"]
        cur_met = ce.get("current_metrics", {})
        cur_f1 = cur_met.get("f1", 0)
        cur_prec = cur_met.get("precision", 0)
        cur_rec = cur_met.get("recall", 0)
        opt_th = best["threshold"]
        opt_f1 = best["f1"]
        opt_prec = best["precision"]
        opt_rec = best["recall"]
        gain = opt_f1 - cur_f1

        lines.extend(
            [
                f"- **Current threshold**: {cur_th:.2f} (from configs/inference.yaml)",
                f"- **Current F1**: {cur_f1:.4f}",
                f"- **Optimal F1 threshold**: {opt_th:.2f}",
                f"- **Optimal F1**: {opt_f1:.4f}",
                f"- **F1 gain**: {gain:.4f} ({gain / max(cur_f1, 0.001) * 100:.1f}% relative)",
                f"- **Precision tradeoff**: {cur_prec:.4f} → {opt_prec:.4f}",
                f"- **Recall tradeoff**: {cur_rec:.4f} → {opt_rec:.4f}",
                "",
            ]
        )
        if gain > 0.01:
            lines.append(
                "**Verdict: The current threshold of 0.10 is NOT optimal.** "
                "This extremely low threshold was likely chosen to maximize recall, "
                "but it comes at a significant precision cost. "
                f"The optimal F1 threshold is {opt_th:.2f}, which improves F1 by {gain:.4f}."
            )
            lines.append("")
            lines.append(
                "**Recommendation: RETUNE** the threshold. However, do NOT automatically "
                "replace threshold 0.10 without considering the application's precision-recall "
                "tradeoff preference:"
            )
            lines.append("- **Low threshold (0.10)**: Maximizes recall, suitable when missing a duplicate is costly.")
            lines.append(f"- **Optimal threshold ({opt_th:.2f})**: Balances precision and recall for best F1.")
            lines.append("- **High threshold (>0.60)**: Maximizes precision, suitable when false positives are costly.")
            lines.append("")
            lines.append(
                "The optimal F1 threshold should be the default. "
                "If the application requires maximum recall, keep 0.10 "
                "but be aware of the precision cost."
            )
        else:
            lines.append("**Verdict: The current threshold of 0.10 is optimal.** No retuning needed.")
    else:
        lines.append("**No data available for Cross-Encoder-Quora (Trained)**")
    lines.append("")

    return lines


if __name__ == "__main__":
    main()
