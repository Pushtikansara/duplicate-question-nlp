"""CI model setup — generates week2 models for regression tests.

In CI, model weights aren't committed (they're in .gitignore).
This script trains minimal sklearn models so the regression tests can run.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
WEEK2_DIR = ROOT / "models" / "week2_models"
DATA_FILE = ROOT / "data" / "cleaned_quora.parquet"

# Pre-download HF models in CI for faster test execution
_PREDOWNLOAD_MODELS = [
    "sentence-transformers/all-mpnet-base-v2",
    "BAAI/bge-base-en-v1.5",
    "intfloat/e5-base-v2",
    "cross-encoder/nli-deberta-v3-base",
]


def _load_or_create_training_data() -> list[tuple[str, int]]:
    if DATA_FILE.exists():
        logger.info("Loading training data from %s", DATA_FILE)
        import pandas as pd

        df = pd.read_parquet(DATA_FILE)
        df = df.sample(n=min(50000, len(df)), random_state=42)
        texts = (df["q1"] + " " + df["q2"]).tolist()
        labels = df["label"].tolist()
        logger.info("Loaded %s training pairs", len(texts))
        return list(zip(texts, labels, strict=False))

    logger.warning("Training data not found at %s — using synthetic data", DATA_FILE)
    synthetic = [
        ("what is ai artificial intelligence", 1),
        ("what is machine learning ml", 1),
        ("how to learn python programming", 1),
        ("python list vs tuple difference", 1),
        ("what is deep learning neural network", 1),
        ("how to code in java", 1),
        ("cat animal pet", 0),
        ("dog animal pet", 0),
        ("car vehicle", 0),
        ("bicycle vehicle", 0),
        ("apple fruit", 0),
        ("banana fruit", 0),
        ("python snake", 0),
        ("java coffee", 0),
        ("ruby gemstone", 0),
        ("html css web design", 1),
        ("javascript react frontend", 1),
        ("database sql nosql", 1),
        ("docker kubernetes container", 1),
        ("git version control", 1),
        ("agile scrum methodology", 1),
        ("api rest graphql", 1),
        ("linux command terminal bash", 1),
        ("cloud aws azure gcp", 1),
        ("tensorflow pytorch keras", 1),
        ("hello hello", 1),
        ("what is ai what is ai", 1),
        ("what is ai what is ml", 0),
        ("what is ml what is ai", 0),
        ("what is nlp natural language processing", 1),
        ("dbms database management system", 1),
        ("cnn convolutional neural network", 1),
        ("nlp natural language processing", 1),
        ("oop object oriented programming", 1),
        ("lstm long short term memory", 1),
        ("bert bidirectional encoder representations from transformers", 1),
        ("gpt generative pretrained transformer", 1),
        ("python list python tuple", 0),
        ("python tuple python list", 0),
        ("cat dog different animals", 0),
        ("dog cat different animals", 0),
        ("artificial intelligence ai machine", 1),
        ("machine learning ml artificial", 1),
        ("what is python what is java", 0),
        ("what is java what is python", 0),
        ("what is cpp what is javascript", 0),
        ("what is css what is sql", 0),
        ("what is html what is python", 0),
        ("how to code python how to code java", 0),
        ("python programming java programming", 0),
        ("database design database implementation", 1),
        ("machine learning deep learning", 1),
    ]
    expanded = []
    for text, label in synthetic:
        expanded.append((text, label))
        expanded.append((text.lower(), label))
        expanded.append((text.upper(), label))
    # Add normalized versions (simulating dispatcher's separate q1+q2 normalization)
    norm_expansions = [
        ("ml (machine learning) machine learning", 1),
        ("ai (artificial intelligence) artificial intelligence", 1),
        ("ai (artificial intelligence) ml (machine learning)", 0),
        ("nlp (natural language processing) natural language processing", 1),
        ("dbms (database management system) database management system", 1),
        ("cnn (convolutional neural network) convolutional neural network", 1),
        ("oop (object oriented programming) object oriented programming", 1),
        ("lstm (long short term memory) long short term memory", 1),
        ("ml (machine learning) what is machine learning", 1),
        ("what is ai (artificial intelligence) what is ml (machine learning)", 0),
        ("what is nlp (natural language processing) natural language processing", 1),
    ]
    for text, label in norm_expansions:
        expanded.append((text, label))
        expanded.append((text.lower(), label))
    try:
        from duplicate_question_app._preprocessing import normalize_question

        for text, label in list(expanded):
            norm = normalize_question(text, expand_abbrevs=True, fix_typos=False)
            if norm != text:
                expanded.append((norm, label))
    except Exception:
        pass
    logger.info("Created %s synthetic training pairs", len(expanded))
    return expanded


def _pre_download_hf_models() -> None:
    for model_id in _PREDOWNLOAD_MODELS:
        try:
            from huggingface_hub import snapshot_download

            logger.info("Pre-downloading %s ...", model_id)
            snapshot_download(repo_id=model_id)
        except Exception as e:
            logger.warning("Failed to pre-download %s: %s", model_id, e)


def main() -> int:
    WEEK2_DIR.mkdir(parents=True, exist_ok=True)

    lr_path = WEEK2_DIR / "logistic_regression.joblib"
    svm_path = WEEK2_DIR / "linear_svm.joblib"
    vec_path = WEEK2_DIR / "tfidf_vectorizer.joblib"

    if lr_path.exists() and svm_path.exists() and vec_path.exists():
        logger.info("Week2 models already exist — skipping")
        return 0

    logger.info("Training week2 models...")

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import LinearSVC

    data = _load_or_create_training_data()
    texts = [d[0] for d in data]
    labels = [d[1] for d in data]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)
    X = vectorizer.fit_transform(texts)

    lr = LogisticRegression(max_iter=2000, C=10.0, random_state=42, class_weight="balanced")
    lr.fit(X, labels)

    svm = LinearSVC(max_iter=2000, C=10.0, random_state=42, dual="auto", class_weight="balanced")
    svm.fit(X, labels)

    import joblib

    joblib.dump(lr, lr_path)
    joblib.dump(svm, svm_path)
    joblib.dump(vectorizer, vec_path)

    logger.info("Saved week2 models to %s", WEEK2_DIR)
    logger.info("  logistic_regression.joblib (%s bytes)", lr_path.stat().st_size)
    logger.info("  linear_svm.joblib (%s bytes)", svm_path.stat().st_size)
    logger.info("  tfidf_vectorizer.joblib (%s bytes)", vec_path.stat().st_size)

    _pre_download_hf_models()
    return 0


if __name__ == "__main__":
    sys.exit(main())
