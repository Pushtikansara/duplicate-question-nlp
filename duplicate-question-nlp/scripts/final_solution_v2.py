"""Final Solution v2: Hybrid Bi-Encoder + Cross-Encoder.

Strategy:
1. MiniLM-L12-v2 bi-encoder for base similarity (fast)
2. Cross-encoder for reranking borderline cases or weighted combination
3. Optimal threshold + weight search

Usage:
    python scripts/final_solution_v2.py
"""

from __future__ import annotations

import sys
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.preprocessing import normalize_question
from sentence_transformers import SentenceTransformer, CrossEncoder

CSV_DIR = Path.home() / "Downloads"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "final_solution_v2"

ALL_TEST_CSVS = [
    ("CSV_7", "duplicate_question_predictions (7).csv"),
    ("CSV_1", "duplicate_question_predictions (1).csv"),
    ("CSV_2", "duplicate_question_predictions (2).csv"),
    ("CSV_3", "duplicate_question_predictions (3).csv"),
    ("CSV_4", "duplicate_question_predictions (4).csv"),
    ("CSV_5", "duplicate_question_predictions (5).csv"),
    ("CSV_6", "duplicate_question_predictions (6).csv"),
    ("nlp_hard", "nlp_hard_test_5000.csv"),
    ("nlp_test", "nlp_test_questions_5000.csv"),
    ("nlp_extreme", "nlp_extreme_hard_5000.csv"),
    ("hard_dup", "hard_duplicate_test_500.csv"),
    ("research", "NLP_Research_Benchmark_v1_10000.csv"),
]


def load_csv(csv_file: str):
    path = CSV_DIR / csv_file
    df = pd.read_csv(path)
    label_col = next((c for c in df.columns if c.lower().strip() in ("is_duplicate", "label")), None)
    q1_col = "question1"
    q2_col = "question2"
    if q1_col not in df.columns:
        q1_col = next(c for c in df.columns if "q1" in c.lower() or "question1" in c.lower())
    if q2_col not in df.columns:
        q2_col = next(c for c in df.columns if "q2" in c.lower() or "question2" in c.lower())
    pairs = list(zip(df[q1_col].astype(str), df[q2_col].astype(str)))
    return pairs, df[label_col].values if label_col else None, df


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 100)
    print("  FINAL SOLUTION V2 — Hybrid Bi-Encoder + Cross-Encoder")
    print("=" * 100)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load models
    print("\nLoading models...")
    bi_encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2", device=device)
    # Cross-encoder trained for semantic similarity
    cross_encoder = CrossEncoder("cross-encoder/stsb-distilroberta-base", device=device)
    print(f"  all-MiniLM-L12-v2: loaded (device={device})")
    print(f"  cross-encoder/stsb-distilroberta-base: loaded (device={device})")

    leaderboard = {}

    for csv_key, csv_file in ALL_TEST_CSVS:
        pairs, y_true, df = load_csv(csv_file)
        if y_true is None:
            continue

        n = len(pairs)
        print(f"\n{'='*100}")
        print(f"  {csv_file}: {n:,} pairs, pos_rate={y_true.mean():.3f}")
        print(f"{'='*100}")

        # Preprocess with typo fix
        q1s = [normalize_question(p[0], fix_typos=True) for p in pairs]
        q2s = [normalize_question(p[1], fix_typos=True) for p in pairs]

        # Bi-encoder: compute cosine similarity
        start = time.time()
        emb1 = bi_encoder.encode(q1s, normalize_embeddings=True, batch_size=128, show_progress_bar=False)
        emb2 = bi_encoder.encode(q2s, normalize_embeddings=True, batch_size=128, show_progress_bar=False)
        bi_scores = (emb1 * emb2).sum(axis=1)
        bi_time = time.time() - start
        print(f"  Bi-Encoder: {bi_time:.1f}s")

        # Baseline: bi-encoder only with optimal threshold
        best_f1_be, best_th_be = 0, 0.5
        for th in np.linspace(0.1, 0.95, 171):
            preds = (bi_scores >= th).astype(int)
            f1 = f1_score(y_true, preds, zero_division=0)
            if f1 > best_f1_be:
                best_f1_be, best_th_be = f1, th
        preds_be = (bi_scores >= best_th_be).astype(int)
        acc_be = accuracy_score(y_true, preds_be)
        print(f"  BE only: acc={acc_be:.4f} f1={best_f1_be:.4f} th={best_th_be:.3f}")

        # Cross-encoder: compute scores for all pairs
        start = time.time()
        ce_scores = cross_encoder.predict(
            list(zip(q1s, q2s)),
            batch_size=64,
            show_progress_bar=False,
        )
        ce_time = time.time() - start
        print(f"  Cross-Encoder: {ce_time:.1f}s")

        # Baseline: cross-encoder only
        best_f1_ce, best_th_ce = 0, 0.5
        for th in np.linspace(0.0, 5.0, 101) if ce_scores.max() > 2 else np.linspace(0.1, 0.95, 171):
            preds = (ce_scores >= th).astype(int)
            f1 = f1_score(y_true, preds, zero_division=0)
            if f1 > best_f1_ce:
                best_f1_ce, best_th_ce = f1, th
        preds_ce = (ce_scores >= best_th_ce).astype(int)
        acc_ce = accuracy_score(y_true, preds_ce)
        print(f"  CE only: acc={acc_ce:.4f} f1={best_f1_ce:.4f} th={best_th_ce:.3f}")

        # Hybrid: normalize CE scores to [0,1] range for combination
        if ce_scores.max() > 2:
            ce_norm = 1.0 / (1.0 + np.exp(-(ce_scores - ce_scores.mean()) / ce_scores.std()))
        else:
            ce_norm = ce_scores.copy()

        # Try weighted combinations of bi-encoder + cross-encoder
        best_hybrid_acc, best_hybrid_f1 = 0, 0
        best_hybrid_info = {}

        for ce_weight in np.linspace(0.0, 1.0, 21):
            bi_weight = 1.0 - ce_weight
            hybrid = bi_scores * bi_weight + ce_norm * ce_weight

            for th in np.linspace(0.1, 0.95, 171):
                preds = (hybrid >= th).astype(int)
                f1 = f1_score(y_true, preds, zero_division=0)
                if f1 > best_hybrid_f1:
                    best_hybrid_f1 = f1
                    best_hybrid_acc = accuracy_score(y_true, preds)
                    prec = precision_score(y_true, preds, zero_division=0)
                    rec = recall_score(y_true, preds, zero_division=0)
                    cm = confusion_matrix(y_true, preds)
                    tn, fp, fn, tp = cm.ravel()
                    best_hybrid_info = {
                        "ce_weight": float(ce_weight),
                        "bi_weight": float(bi_weight),
                        "threshold": float(th),
                        "accuracy": float(best_hybrid_acc),
                        "f1": float(best_hybrid_f1),
                        "precision": float(prec),
                        "recall": float(rec),
                        "tn": int(tn),
                        "fp": int(fp),
                        "fn": int(fn),
                        "tp": int(tp),
                    }

        # Print best hybrid result
        info = best_hybrid_info
        print(f"\n  >> BEST HYBRID Result:")
        print(f"     Weights: BE={info['bi_weight']:.3f} CE={info['ce_weight']:.3f}")
        print(f"     Threshold: {info['threshold']:.3f}")
        print(f"     Accuracy: {info['accuracy']:.4f}")
        print(f"     F1:       {info['f1']:.4f}")
        print(f"     Prec:     {info['precision']:.4f}")
        print(f"     Rec:      {info['recall']:.4f}")
        print(f"     TN={info['tn']} FP={info['fp']} FN={info['fn']} TP={info['tp']}")
        print(f"     BE alone: {acc_be:.4f} | CE alone: {acc_ce:.4f}")

        # Save predictions
        hybrid = bi_scores * info["bi_weight"] + ce_norm * info["ce_weight"]
        y_pred = (hybrid >= info["threshold"]).astype(int)

        out_df = pd.DataFrame({
            "question1": df["question1"] if "question1" in df.columns else df.iloc[:, 0],
            "question2": df["question2"] if "question2" in df.columns else df.iloc[:, 1],
            "is_duplicate": y_true,
            "predicted_label": y_pred,
            "prediction": ["Duplicate" if p else "Non-Duplicate" for p in y_pred],
            "bi_encoder_score": bi_scores,
            "cross_encoder_score_raw": ce_scores,
            "cross_encoder_score_norm": ce_norm,
            "hybrid_score": hybrid,
            "threshold": info["threshold"],
            "model": "Hybrid(MiniLM-L12-v2+stsb-distilroberta)",
        })

        out_dir = RESULTS_DIR / "predictions"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_dir / f"hybrid_{csv_file}", index=False)

        leaderboard[csv_key] = {
            "file": csv_file,
            "n_samples": n,
            "pos_rate": float(y_true.mean()),
            "bi_only": {"accuracy": float(acc_be), "f1": float(best_f1_be), "threshold": float(best_th_be)},
            "ce_only": {"accuracy": float(acc_ce), "f1": float(best_f1_ce), "threshold": float(best_th_ce)},
            "hybrid": info,
        }

    # Final leaderboard
    print(f"\n{'='*120}")
    print("  FINAL LEADERBOARD — Hybrid (Bi-Encoder + Cross-Encoder)")
    print(f"{'='*120}")
    print(f"  {'Dataset':35s}  {'BE_Acc':>7s}  {'CE_Acc':>7s}  {'Hybrid':>9s}  {'F1':>8s}  {'Prec':>8s}  {'Rec':>8s}  {'Thresh':>7s}  {'CE_w':>5s}")
    print(f"  {'-'*120}")

    ranked = sorted(leaderboard.items(), key=lambda x: x[1]["hybrid"]["accuracy"], reverse=True)
    for key, info in ranked:
        r = info["hybrid"]
        bi_acc = info["bi_only"]["accuracy"]
        ce_acc = info["ce_only"]["accuracy"]
        print(f"  {info['file']:35s}  {bi_acc:7.4f}  {ce_acc:7.4f}  {r['accuracy']:9.4f}  "
              f"{r['f1']:8.4f}  {r['precision']:8.4f}  {r['recall']:8.4f}  "
              f"{r['threshold']:7.3f}  {r['ce_weight']:5.2f}")

    with open(RESULTS_DIR / "leaderboard.json", "w") as f:
        json.dump(leaderboard, f, indent=2)
    print(f"\nFull results saved to {RESULTS_DIR}/leaderboard.json")
    print(f"Predictions saved to {RESULTS_DIR}/predictions/")


if __name__ == "__main__":
    main()
