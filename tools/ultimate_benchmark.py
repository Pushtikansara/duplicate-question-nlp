"""Ultimate benchmark: test every model on CSV (7) and extreme hard test sets.

Usage:
    python scripts/ultimate_benchmark.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix, roc_auc_score

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.preprocessing import normalize_question

CSV_DIR = Path.home() / "Downloads"

TEST_CSVS = [
    ("CSV (7)", "duplicate_question_predictions (7).csv"),
    ("Extreme Hard", "nlp_extreme_hard_5000.csv"),
    ("Hard Test", "nlp_hard_test_5000.csv"),
    ("Test Questions", "nlp_test_questions_5000.csv"),
    ("Hard Duplicate", "hard_duplicate_test_500.csv"),
]

BENCHMARK_MODELS = [
    # Base sentence transformers
    ("E5-base-v2 (frozen)", "intfloat/e5-base-v2", False),
    ("E5-base-v2 (finetuned)", "models/e5-quora-finetuned", True),
    ("BGE-base-en-v1.5", "BAAI/bge-base-en-v1.5", False),
    ("MPNet-base-v2", "sentence-transformers/all-mpnet-base-v2", False),
    ("all-MiniLM-L12-v2", "sentence-transformers/all-MiniLM-L12-v2", False),
    ("all-MiniLM-L6-v2", "sentence-transformers/all-MiniLM-L6-v2", False),
    ("gte-base-en-v1.5", "Alibaba-NLP/gte-base-en-v1.5", False),
]


def load_and_encode(model_name_or_path: str, texts: list[str], batch_size: int = 128, is_local: bool = False):
    from sentence_transformers import SentenceTransformer
    device = "cuda"
    if is_local:
        model = SentenceTransformer(model_name_or_path, device=device)
    else:
        model = SentenceTransformer(model_name_or_path, device=device)

    q1_enc = [f"query: {t}" for t in texts] if "e5" in model_name_or_path.lower() and not is_local else texts
    q2_enc = [f"passage: {t}" for t in texts] if "e5" in model_name_or_path.lower() and not is_local else texts
    
    if is_local:
        q1_enc = [f"query: {t}" for t in texts]
        q2_enc = [f"passage: {t}" for t in texts]

    emb1 = model.encode(q1_enc, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False)
    emb2 = model.encode(q2_enc, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False)
    return (emb1 * emb2).sum(axis=1)


def evaluate_model(name: str, model_name_or_path: str, is_local: bool, test_sets: dict):
    print(f"\n{'='*70}")
    print(f"  MODEL: {name}")
    print(f"{'='*70}")

    for set_name, pairs, y_true in test_sets:
        try:
            start = time.time()
            sims = load_and_encode(model_name_or_path, [p[0] for p in pairs] + [p[1] for p in pairs], 
                                    is_local=is_local)
            
            # Split the concatenated embeddings
            n = len(pairs)
            from sentence_transformers import SentenceTransformer
            device = "cuda"
            if is_local:
                model = SentenceTransformer(model_name_or_path, device=device)
            else:
                model = SentenceTransformer(model_name_or_path, device=device)
                
            q1s = [normalize_question(p[0]) for p in pairs]
            q2s = [normalize_question(p[1]) for p in pairs]
            
            prefix_q1 = [f"query: {q}" for q in q1s] if ("e5" in model_name_or_path.lower() or is_local) else q1s
            prefix_q2 = [f"passage: {q}" for q in q2s] if ("e5" in model_name_or_path.lower() or is_local) else q2s
            
            emb1 = model.encode(prefix_q1, normalize_embeddings=True, batch_size=128, show_progress_bar=False)
            emb2 = model.encode(prefix_q2, normalize_embeddings=True, batch_size=128, show_progress_bar=False)
            sims = (emb1 * emb2).sum(axis=1)
            elapsed = time.time() - start

            # Find optimal threshold for F1
            best_f1 = 0
            best_th = 0.5
            for th in np.linspace(0.1, 0.95, 86):
                preds = (sims >= th).astype(int)
                f1 = f1_score(y_true, preds, zero_division=0)
                if f1 > best_f1:
                    best_f1 = f1
                    best_th = th

            preds = (sims >= best_th).astype(int)
            acc = accuracy_score(y_true, preds)
            f1 = f1_score(y_true, preds, zero_division=0)
            prec = precision_score(y_true, preds, zero_division=0)
            rec = recall_score(y_true, preds, zero_division=0)
            try:
                roc = roc_auc_score(y_true, sims)
            except:
                roc = 0.0
            cm = confusion_matrix(y_true, preds)
            tn, fp, fn, tp = cm.ravel()

            print(f"  {set_name:20s}  Acc={acc:.4f}  F1={f1:.4f}  P={prec:.4f}  R={rec:.4f}  "
                  f"ROC={roc:.4f}  th={best_th:.2f}  TN={tn} FP={fp} FN={fn} TP={tp}  "
                  f"({elapsed:.1f}s)")

        except Exception as e:
            print(f"  {set_name:20s}  ERROR: {e}")


def main():
    # Load all test sets
    test_sets = []
    for set_name, fname in TEST_CSVS:
        path = CSV_DIR / fname
        if not path.exists():
            print(f"SKIP: {fname}")
            continue
        df = pd.read_csv(path)
        label_col = None
        for c in df.columns:
            if c.lower().strip() in ("is_duplicate", "label"):
                label_col = c
                break
        if label_col is None:
            continue
        q1_col = "question1"
        q2_col = "question2"
        if q1_col not in df.columns:
            q1_col = [c for c in df.columns if "question1" in c.lower() or "q1" in c.lower()][0]
        if q2_col not in df.columns:
            q2_col = [c for c in df.columns if "question2" in c.lower() or "q2" in c.lower()][0]
        pairs = list(zip(df[q1_col].astype(str), df[q2_col].astype(str)))
        y_true = df[label_col].values
        test_sets.append((set_name, pairs, y_true))
        print(f"Loaded {set_name}: {len(pairs):,} samples")

    print(f"\nTotal test sets: {len(test_sets)}")
    print(f"\nBenchmarking {len(BENCHMARK_MODELS)} models...")

    for name, model_path, is_local in BENCHMARK_MODELS:
        evaluate_model(name, model_path, is_local, test_sets)


if __name__ == "__main__":
    main()
