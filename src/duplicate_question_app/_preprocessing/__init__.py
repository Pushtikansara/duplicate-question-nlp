"""Text preprocessing — normalization, tokenisation, abbreviation expansion."""

from duplicate_question_app._preprocessing.text import (  # noqa: F401
    _ABBREVIATIONS,
    _TYPO_MAP,
    normalize_question,
)
