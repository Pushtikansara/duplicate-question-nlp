"""Export Week 2 baseline models (TF-IDF + LR, TF-IDF + SVM) for use in the Streamlit app.

This script replicates the exact preprocessing and training from baseline_model.ipynb,
then saves the TF-IDF vectorizer, Logistic Regression, and Linear SVM models using joblib.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models" / "week2_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    print("Loading dataset...")
    parquet_path = DATA_DIR / "cleaned_quora.parquet"
    csv_path = DATA_DIR / "cleaned_quora.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        print(f"Loaded {parquet_path}")
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
        print(f"Loaded {csv_path}")
    else:
        raise FileNotFoundError(f"Neither {parquet_path} nor {csv_path} found")

    df["clean_q1"] = df["clean_q1"].fillna("").astype(str)
    df["clean_q2"] = df["clean_q2"].fillna("").astype(str)
    print(f"Dataset shape: {df.shape}")

    # --- TF-IDF Feature Engineering (exact same as notebook) ---
    print("Fitting TF-IDF vectorizer...")
    tfidf = TfidfVectorizer(
        max_features=5000,
        stop_words="english",
        ngram_range=(1, 2),
    )
    q1_tfidf = tfidf.fit_transform(df["clean_q1"])
    q2_tfidf = tfidf.transform(df["clean_q2"])
    X = hstack([q1_tfidf, q2_tfidf])
    y = df["label"]
    print(f"Feature matrix shape: {X.shape}")

    # --- Train Logistic Regression (exact same as notebook) ---
    print("Training Logistic Regression...")
    lr_model = LogisticRegression(max_iter=1000)
    lr_model.fit(X, y)
    print("Logistic Regression training complete.")

    # --- Train Linear SVM (exact same as notebook) ---
    print("Training Linear SVM...")
    svm_model = LinearSVC(max_iter=1000)
    svm_model.fit(X, y)
    print("Linear SVM training complete.")

    # --- Export artifacts ---
    print(f"\nExporting models to {MODELS_DIR}...")
    joblib.dump(tfidf, MODELS_DIR / "tfidf_vectorizer.joblib")
    print("  [OK] tfidf_vectorizer.joblib")
    joblib.dump(lr_model, MODELS_DIR / "logistic_regression.joblib")
    print("  [OK] logistic_regression.joblib")
    joblib.dump(svm_model, MODELS_DIR / "linear_svm.joblib")
    print("  [OK] linear_svm.joblib")

    print("\nAll Week 2 models exported successfully!")


if __name__ == "__main__":
    main()
