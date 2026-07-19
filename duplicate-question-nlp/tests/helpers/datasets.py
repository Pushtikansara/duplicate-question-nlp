from __future__ import annotations

import pandas as pd


SAMPLE_PAIRS = [
    ("How to learn Python?", "How can I learn Python programming?"),
    ("What is the capital of France?", "What is the largest city in Germany?"),
    ("How to make pizza?", "How to prepare pizza at home?"),
    ("What is machine learning?", "What is deep learning?"),
    ("Best programming languages?", "Which programming language should I learn?"),
    ("How to lose weight?", "How to gain weight fast?"),
    ("What is the meaning of life?", "How old is the Earth?"),
    ("Python vs Java", "Java vs Python"),
    ("How to code?", "How to write code?"),
    ("What is 2+2?", "What is the square root of 4?"),
]

LABELS = [1, 0, 1, 0, 1, 0, 0, 1, 1, 0]


def sample_dataframe(n: int = 10) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "question1": [p[0] for p in SAMPLE_PAIRS[:n]],
            "question2": [p[1] for p in SAMPLE_PAIRS[:n]],
            "label": LABELS[:n],
            "id": [f"test_{i}" for i in range(n)],
        }
    )
    return df


def sample_dataframe_q1_q2(n: int = 10) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "q1": [p[0] for p in SAMPLE_PAIRS[:n]],
            "q2": [p[1] for p in SAMPLE_PAIRS[:n]],
            "label": LABELS[:n],
            "id": [f"test_{i}" for i in range(n)],
        }
    )
    return df


def get_duplicate_pairs() -> list[tuple[str, str]]:
    return [(SAMPLE_PAIRS[i][0], SAMPLE_PAIRS[i][1]) for i in range(len(SAMPLE_PAIRS)) if LABELS[i] == 1]


def get_non_duplicate_pairs() -> list[tuple[str, str]]:
    return [(SAMPLE_PAIRS[i][0], SAMPLE_PAIRS[i][1]) for i in range(len(SAMPLE_PAIRS)) if LABELS[i] == 0]
