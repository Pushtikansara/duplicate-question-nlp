"""Validate threshold updates by running predictions on the validation set."""

import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from duplicate_question_app._dataset.loader import get_quora_splits
from duplicate_question_app._models.embeddings import (
    _get_sigmoid_params,
    get_sentence_transformer_model,
    is_cross_encoder_model,
    is_finetuned_embedding_model,
)
from duplicate_question_app._preprocessing import normalize_question

THRESHOLD_CHANGES = {
    "Cross-Encoder-Quora (Trained)": (0.10, 0.52),
    "E5-base-v2": (0.35, 0.59),
    "E5-quora-finetuned": (0.40, 0.63),
}

OLD_RESULTS = {
    "Cross-Encoder-Quora (Trained)": {"f1": 0.8536, "ece": 0.0660},
    "E5-base-v2": {"f1": 0.5611, "ece": 0.1632},
    "E5-quora-finetuned": {"f1": 0.7323, "ece": 0.0549},
}

PREDICTED_IMPROVEMENT = {
    "Cross-Encoder-Quora (Trained)": {"f1": 0.8758, "ece": 0.0072},
    "E5-base-v2": {"f1": 0.7068, "ece": 0.0042},
    "E5-quora-finetuned": {"f1": 0.7667, "ece": 0.0065},
}


def _ece(y_true, y_prob, n_bins=10):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        in_bin = (y_prob >= bin_boundaries[i]) & (y_prob < bin_boundaries[i + 1])
        if np.sum(in_bin) > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_prob[in_bin])
            ece += np.sum(in_bin) * abs(bin_acc - bin_conf)
    return ece / len(y_true)


def _predict_ce(model_name, pairs, batch_size=128):
    model = get_sentence_transformer_model(model_name)
    q1s = [normalize_question(p[0], expand_abbrevs=True, fix_typos=True) for p in pairs]
    q2s = [normalize_question(p[1], expand_abbrevs=True, fix_typos=True) for p in pairs]
    all_scores = model.predict(
        list(zip(q1s, q2s, strict=False)), batch_size=batch_size, apply_softmax=True, show_progress_bar=True
    )
    probs = []
    for scores in all_scores:
        if len(scores) >= 3:
            contra, _, entail = float(scores[0]), float(scores[1]), float(scores[2])
            denom = contra + entail
            prob_dup = entail / denom if denom > 0.01 else 0.5
        elif len(scores) == 2:
            prob_dup = float(scores[1])
        else:
            prob_dup = max(0.0, min(1.0, (float(scores[0]) + 1) / 2))
        probs.append(prob_dup)
    return np.array(probs)


def _predict_bi_encoder(model_name, pairs, batch_size=64):
    resolved = model_name
    steepness, midpoint = _get_sigmoid_params(resolved.lower())
    model = get_sentence_transformer_model(resolved)
    is_ft = is_finetuned_embedding_model(resolved)
    use_e5_prefix = ("e5" in resolved.lower()) and not is_ft

    q1s = [normalize_question(p[0], expand_abbrevs=True, fix_typos=True) for p in pairs]
    q2s = [normalize_question(p[1], expand_abbrevs=True, fix_typos=True) for p in pairs]

    q1_encoded = [f"query: {q}" if use_e5_prefix else q for q in q1s]
    q2_encoded = [f"passage: {q}" if use_e5_prefix else q for q in q2s]

    emb1 = model.encode(q1_encoded, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)
    emb2 = model.encode(q2_encoded, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)

    sims = np.sum(emb1 * emb2, axis=1)
    probs = 1 / (1 + np.exp(-steepness * (sims - midpoint)))
    return probs


def main():
    print("=" * 72)
    print("  VALIDATION: Threshold Update Impact")
    print("=" * 72)

    splits = get_quora_splits()
    val_df = splits[1]
    val_texts_a = val_df["q1"].tolist()
    val_texts_b = val_df["q2"].tolist()
    val_labels = np.array(val_df["label"].tolist())
    pairs = list(zip(val_texts_a, val_texts_b, strict=False))
    print(f"\n  Validation set: {len(pairs)} pairs\n")

    results = {}

    for model_name, (old_thr, new_thr) in THRESHOLD_CHANGES.items():
        print(f"  --- {model_name} ---")
        print(f"    Threshold: {old_thr} -> {new_thr}")
        sys.stdout.flush()

        start = time.time()
        try:
            if is_cross_encoder_model(model_name):
                probs = _predict_ce(model_name, pairs)
            else:
                probs = _predict_bi_encoder(model_name, pairs)
        except Exception as e:
            print(f"    ERROR during prediction: {e}")
            import traceback

            traceback.print_exc()
            results[model_name] = {"error": str(e)}
            continue

        elapsed = time.time() - start

        y_pred = (probs >= new_thr).astype(int)
        acc = accuracy_score(val_labels, y_pred)
        prec = precision_score(val_labels, y_pred, zero_division=0)
        rec = recall_score(val_labels, y_pred, zero_division=0)
        f1 = f1_score(val_labels, y_pred, zero_division=0)
        ece_val = _ece(val_labels, probs)

        print(f"    F1={f1:.4f}  Acc={acc:.4f}  P={prec:.4f}  R={rec:.4f}  ECE={ece_val:.4f}")
        print(f"    Time: {elapsed:.1f}s")
        sys.stdout.flush()

        results[model_name] = {
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "ece": float(ece_val),
            "threshold": new_thr,
        }

    print()
    print("=" * 72)
    print("  SUMMARY: Predicted vs Measured F1")
    print("=" * 72)
    print(f"  {'Model':35s} {'Pred F1':>8s} {'Meas F1':>8s} {'ΔF1':>6s} {'Match?':>8s}")
    print("  " + "-" * 67)

    all_ok = True
    for model_name in THRESHOLD_CHANGES:
        r = results.get(model_name, {})
        if "error" in r:
            print(f"  {model_name:35s} {'ERROR':>22s}")
            all_ok = False
            continue
        pred_f1 = PREDICTED_IMPROVEMENT[model_name]["f1"]
        meas_f1 = r.get("f1", 0)
        delta = meas_f1 - pred_f1
        match = "✓" if abs(delta) < 0.02 else "✗ WARN"
        if abs(delta) >= 0.02:
            all_ok = False
        print(f"  {model_name:35s} {pred_f1:8.4f} {meas_f1:8.4f} {delta:+6.4f} {match:>8s}")

    print()
    print("=" * 72)
    print("  VERDICT")
    print("=" * 72)
    if all_ok:
        print("  All 3 threshold changes validated. Measured F1 matches predictions.")
    else:
        print("  WARNING: Some measured F1 deviates from predictions by >0.02.")
        print("  Check individual results above.")

    report = {"threshold_changes": {}, "verdict": "pass" if all_ok else "warn"}
    for model_name in THRESHOLD_CHANGES:
        r = results.get(model_name, {})
        if "error" in r:
            report["threshold_changes"][model_name] = {"error": r["error"]}
            continue
        old_thr, new_thr = THRESHOLD_CHANGES[model_name]
        old_f1 = OLD_RESULTS[model_name]["f1"]
        pred_f1 = PREDICTED_IMPROVEMENT[model_name]["f1"]
        meas_f1 = r["f1"]
        report["threshold_changes"][model_name] = {
            "old_threshold": old_thr,
            "new_threshold": new_thr,
            "old_f1": old_f1,
            "predicted_f1": pred_f1,
            "measured_f1": meas_f1,
            "measured_accuracy": r.get("accuracy"),
            "measured_ece": r.get("ece"),
            "f1_gain": meas_f1 - old_f1,
            "delta_vs_prediction": meas_f1 - pred_f1,
        }

    out_path = ROOT / "evaluation_results" / "threshold_update_validation.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Full report saved to {out_path}")


if __name__ == "__main__":
    main()
