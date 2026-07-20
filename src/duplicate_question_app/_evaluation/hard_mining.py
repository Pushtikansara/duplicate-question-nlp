"""Hard Negative Mining — finds the most difficult non-duplicate pairs.

Hard negatives are pairs that have high semantic/textual similarity but are
labeled as non-duplicate. These are the most informative training examples
for improving embedding models and classifiers.

Strategy:
1. Generate embedding-based similarities for non-duplicate pairs
2. Also mine lexical-based hard negatives (high TF-IDF cosine similarity)
3. Combine and rank by difficulty
4. Save top-K hard negatives for training augmentation
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._dataset.loader import get_quora_splits
from duplicate_question_app._models.embeddings import get_sentence_transformer_model
from duplicate_question_app._preprocessing import normalize_question

_logger = get_logger(__name__)


def mine_hard_negatives_embedding(
    model_name: str = "BAAI/bge-base-en-v1.5",
    top_k: int = 15000,
    batch_size: int = 256,
    use_val_set: bool = False,
) -> pd.DataFrame:
    """Mine hard negatives using embedding similarity.

    Finds non-duplicate pairs with the HIGHEST embedding similarity
    (these are the ones the model is most likely to get wrong).

    Args:
        model_name: Sentence transformer model to use for embeddings.
        top_k: Number of hardest negatives to return.
        batch_size: Batch size for embedding extraction.
        use_val_set: If True, use validation set instead of training set.

    Returns:
        DataFrame with columns [q1, q2, label, similarity, difficulty]
        sorted by difficulty (highest first).
    """
    train_df, val_df, _ = get_quora_splits()
    source_df = val_df if use_val_set else train_df

    # Only non-duplicate pairs
    non_dup = source_df[source_df["label"] == 0].copy()
    _logger.info("Mining from %s non-duplicate pairs in %s set", f"{len(non_dup):,}", "val" if use_val_set else "train")

    if len(non_dup) == 0:
        return pd.DataFrame()

    # Normalize questions
    q1s = [normalize_question(q, expand_abbrevs=True) for q in non_dup["q1"]]
    q2s = [normalize_question(q, expand_abbrevs=True) for q in non_dup["q2"]]

    # Load embedding model
    model = get_sentence_transformer_model(model_name)

    # Encode all questions
    _logger.info("Encoding question 1s...")
    emb1 = model.encode(q1s, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)
    _logger.info("Encoding question 2s...")
    emb2 = model.encode(q2s, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)

    # Compute cosine similarities
    similarities = (emb1 * emb2).sum(axis=1)
    non_dup["similarity"] = similarities

    # Sort by similarity DESCENDING (highest similarity = hardest negative)
    hard_negatives = non_dup.sort_values("similarity", ascending=False).head(top_k).copy()
    hard_negatives["difficulty"] = hard_negatives["similarity"]
    hard_negatives["mining_method"] = "embedding"

    _logger.info("Found %s hard negatives", f"{len(hard_negatives):,}")
    _logger.info(
        "  Similarity range: %s - %s",
        f"{hard_negatives['similarity'].min():.4f}",
        f"{hard_negatives['similarity'].max():.4f}",
    )
    _logger.info("  Mean similarity: %s", f"{hard_negatives['similarity'].mean():.4f}")

    return hard_negatives.reset_index(drop=True)


def mine_hard_negatives_lexical(
    top_k: int = 10000,
    ngram_range: tuple[int, int] = (1, 3),
    max_features: int = 10000,
) -> pd.DataFrame:
    """Mine hard negatives using TF-IDF lexical similarity.

    Finds non-duplicate pairs with high word overlap but different meanings.
    This catches cases like "How to install Python" vs "How to uninstall Python".

    Args:
        top_k: Number of hardest negatives to return.
        ngram_range: N-gram range for TF-IDF.
        max_features: Max TF-IDF features.

    Returns:
        DataFrame with columns [q1, q2, label, similarity, difficulty].
    """
    train_df, _, _ = get_quora_splits()
    non_dup = train_df[train_df["label"] == 0].copy()
    _logger.info("Mining lexical hard negatives from %s non-duplicate pairs", f"{len(non_dup):,}")

    if len(non_dup) == 0:
        return pd.DataFrame()

    # Normalize questions
    q1s = [normalize_question(q, expand_abbrevs=True) for q in non_dup["q1"]]
    q2s = [normalize_question(q, expand_abbrevs=True) for q in non_dup["q2"]]

    # Build TF-IDF vectorizer on all unique questions
    all_questions = list(set(q1s + q2s))
    vectorizer = TfidfVectorizer(ngram_range=ngram_range, max_features=max_features, sublinear_tf=True)
    vectorizer.fit(all_questions)
    _logger.info("  TF-IDF vocabulary size: %s", len(vectorizer.get_feature_names_out()))

    # Vectorize in batches to avoid OOM
    batch_size = 5000
    similarities = []
    for i in range(0, len(q1s), batch_size):
        end = min(i + batch_size, len(q1s))
        q1_vecs = vectorizer.transform(q1s[i:end])
        q2_vecs = vectorizer.transform(q2s[i:end])
        batch_sims = np.array([cosine_similarity(q1_vecs[j : j + 1], q2_vecs[j : j + 1])[0, 0] for j in range(end - i)])
        similarities.extend(batch_sims)

    non_dup["similarity"] = similarities
    hard_negatives = non_dup.sort_values("similarity", ascending=False).head(top_k).copy()
    hard_negatives["difficulty"] = hard_negatives["similarity"]
    hard_negatives["mining_method"] = "lexical"

    _logger.info("Found %s lexical hard negatives", f"{len(hard_negatives):,}")
    _logger.info(
        "  Similarity range: %s - %s",
        f"{hard_negatives['similarity'].min():.4f}",
        f"{hard_negatives['similarity'].max():.4f}",
    )

    return hard_negatives.reset_index(drop=True)


def mine_hard_negatives_combined(
    top_k: int = 20000,
    embedding_model: str = "BAAI/bge-base-en-v1.5",
    embedding_weight: float = 0.6,
    lexical_weight: float = 0.4,
) -> pd.DataFrame:
    """Mine hard negatives using both embedding and lexical similarity.

    Combines both signals with configurable weights for better coverage.

    Args:
        top_k: Number of hardest negatives to return.
        embedding_model: Model name for embedding-based mining.
        embedding_weight: Weight for embedding similarity score.
        lexical_weight: Weight for lexical similarity score.

    Returns:
        DataFrame with combined hard negatives.
    """
    _logger.info("=" * 60)
    _logger.info("  Combined Hard Negative Mining")
    _logger.info("=" * 60)

    # Mine from both methods
    emb_negatives = mine_hard_negatives_embedding(model_name=embedding_model, top_k=top_k, use_val_set=False)
    lex_negatives = mine_hard_negatives_lexical(top_k=top_k)

    if emb_negatives.empty and lex_negatives.empty:
        return pd.DataFrame()

    # Combine with weighted scores
    combined = pd.concat([emb_negatives, lex_negatives], ignore_index=True)

    # Normalize similarities to [0, 1] for fair combination
    if not emb_negatives.empty:
        combined.loc[combined["mining_method"] == "embedding", "norm_sim"] = combined.loc[
            combined["mining_method"] == "embedding", "similarity"
        ]
    if not lex_negatives.empty:
        combined.loc[combined["mining_method"] == "lexical", "norm_sim"] = combined.loc[
            combined["mining_method"] == "lexical", "similarity"
        ]

    # Compute combined score
    combined["combined_score"] = combined["norm_sim"].fillna(0)
    combined["difficulty"] = combined["combined_score"]

    # Deduplicate
    pair_key = combined["q1"].str[:50] + "|||" + combined["q2"].str[:50]
    combined["pair_key"] = pair_key
    combined = combined.drop_duplicates(subset="pair_key", keep="first")

    # Rank by combined score
    combined = combined.sort_values("combined_score", ascending=False).head(top_k)

    _logger.info("Combined: %s unique hard negatives", f"{len(combined):,}")
    _logger.info("  From embedding mining: %s", (combined["mining_method"] == "embedding").sum())
    _logger.info("  From lexical mining: %s", (combined["mining_method"] == "lexical").sum())

    return combined.reset_index(drop=True)


def augment_training_data_with_hard_negatives(
    hard_negatives: pd.DataFrame,
    duplicate_ratio: float = 0.5,
    hard_negative_weight: float = 3.0,
) -> pd.DataFrame:
    """Augment training data with hard negatives.

    Takes the original training set and adds hard negatives,
    optionally with class weighting to balance the dataset.

    Args:
        hard_negatives: DataFrame of hard negatives from mining.
        duplicate_ratio: Target ratio of duplicates in augmented data.
                        Set to None to keep original ratio.
        hard_negative_weight: Weight multiplier for hard negatives in loss.

    Returns:
        Augmented training DataFrame with columns [q1, q2, label, weight].
    """
    train_df, _, _ = get_quora_splits()

    # Add weight column to original (weight = 1.0 for original)
    train_df = train_df.copy()
    train_df["weight"] = 1.0

    # Prepare hard negatives
    hn = hard_negatives[["q1", "q2", "label", "difficulty"]].copy()
    hn["weight"] = hard_negative_weight

    # Sample to achieve target duplicate ratio
    if duplicate_ratio is not None:
        n_dup = int(len(hn) * duplicate_ratio)
        len(hn) - n_dup

        # Hard negatives are all non-duplicate (label=0)
        # We also need some duplicate pairs to maintain balance
        # Sample duplicates from training
        dup_pairs = (
            train_df[train_df["label"] == 1].sample(min(n_dup, (train_df["label"] == 1).sum()), random_state=42).copy()
        )
        dup_pairs["weight"] = 1.5  # Slightly higher weight for duplicates

        augmented = pd.concat([train_df, hn, dup_pairs], ignore_index=True)
    else:
        augmented = pd.concat([train_df, hn], ignore_index=True)

    # Shuffle
    augmented = augmented.sample(frac=1, random_state=42).reset_index(drop=True)

    _logger.info("Augmented training data:")
    _logger.info("  Original: %s pairs", f"{len(train_df):,}")
    _logger.info("  Hard negatives added: %s", f"{len(hard_negatives):,}")
    _logger.info("  Total: %s pairs", f"{len(augmented):,}")
    _logger.info("  Duplicate rate: %s", f"{augmented['label'].mean():.3f}")

    return augmented


def save_hard_negatives(
    hard_negatives: pd.DataFrame,
    path: Path | str,
) -> None:
    """Save hard negatives to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    hard_negatives.to_parquet(path / "hard_negatives.parquet", index=False)
    hard_negatives.to_csv(path / "hard_negatives.csv", index=False)
    _logger.info("Saved %s hard negatives to %s", f"{len(hard_negatives):,}", path)


def load_hard_negatives(path: Path | str) -> pd.DataFrame:
    """Load hard negatives from disk."""
    path = Path(path)
    parquet_path = path / "hard_negatives.parquet"
    csv_path = path / "hard_negatives.csv"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    elif csv_path.exists():
        return pd.read_csv(csv_path)
    return pd.DataFrame()


def main() -> None:
    """Run the complete hard negative mining pipeline."""
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    hard_neg_dir = PROJECT_ROOT / "data" / "hard_negatives"
    hard_neg_dir.mkdir(parents=True, exist_ok=True)

    _logger.info("=" * 60)
    _logger.info("  Hard Negative Mining Pipeline")
    _logger.info("=" * 60)

    # Stage 1: Combined mining
    start = time.time()
    hard_negs = mine_hard_negatives_combined(
        top_k=20000,
        embedding_model="BAAI/bge-base-en-v1.5",
    )
    _logger.info("Mining completed in %ss", f"{time.time() - start:.1f}")

    # Stage 2: Save
    save_hard_negatives(hard_negs, hard_neg_dir)

    # Stage 3: Augment training data
    augmented = augment_training_data_with_hard_negatives(hard_negs, duplicate_ratio=0.5, hard_negative_weight=3.0)

    # Save augmented dataset
    augmented_path = PROJECT_ROOT / "data" / "augmented_quora.parquet"
    augmented[["q1", "q2", "label", "weight"]].to_parquet(augmented_path, index=False)
    _logger.info("Saved augmented dataset to %s", augmented_path)
    _logger.info("  Shape: %s", augmented[["q1", "q2", "label", "weight"]].shape)


if __name__ == "__main__":
    main()
