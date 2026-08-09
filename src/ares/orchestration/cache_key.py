from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from ares.orchestration.constants import CACHE_SCHEMA_VERSION

_WHITESPACE = re.compile(r"\s+")

#: Default version of the Query Understanding pipeline contract that produced
#: the analysis. Kept in sync with the QU router version so that a change in
#: routing/analyzer behavior automatically invalidates cached analyses.
DEFAULT_ANALYZER_VERSION: str = "1.0.0"

_KEY_NAMESPACE: str = "ares.orchestration.query_understanding"


def normalize_cache_text(text: str) -> str:
    """Return the canonical, deterministic form of a question for cache keys.

    The normalization is intentionally independent from the QU pipeline's
    own normalization: cache keys must be stable across QU implementation
    changes. Semantics:

    - ``unicodedata.normalize("NFKC", ...)`` handles compatibility characters
      (e.g. full-width punctuation, ligatures) so equivalent text maps to the
      same key,
    - ``casefold()`` makes the key case-insensitive,
    - leading/trailing whitespace is stripped and internal whitespace runs are
      collapsed to a single space.
    """
    if not isinstance(text, str):
        raise TypeError("cache key material must be a string")
    if not text:
        return ""
    folded = unicodedata.normalize("NFKC", text).casefold()
    folded = folded.strip()
    return _WHITESPACE.sub(" ", folded)


def build_query_understanding_cache_key(
    question1: str,
    question2: str,
    *,
    schema_version: str = CACHE_SCHEMA_VERSION,
    analyzer_version: str | None = None,
) -> str:
    """Build the deterministic cache key for a Query Understanding request.

    The pair is treated as **ordered**: ``QueryAnalysis`` carries
    ``original_question_1``/``original_question_2`` and per-question metadata,
    so swapping the questions is a semantically different input and yields a
    different key.

    The key is the SHA-256 hex digest of a canonical JSON payload containing:

    - the key schema version (bump ``CACHE_SCHEMA_VERSION`` when the key
      format or normalization semantics change),
    - the Query Understanding analyzer version (``analyzer_version`` defaults
      to the QU router contract version; a QU behavior change invalidates all
      cached analyses),
    - the normalized question texts.

    No timestamps, random ids, memory addresses or process-randomized
    ``hash()`` values are involved: the same logical input always produces
    the same key.
    """
    if analyzer_version is None:
        analyzer_version = _default_analyzer_version()

    payload = {
        "ns": _KEY_NAMESPACE,
        "schema_version": schema_version,
        "analyzer_version": analyzer_version,
        "q1": normalize_cache_text(question1),
        "q2": normalize_cache_text(question2),
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _default_analyzer_version() -> str:
    """Resolve the current QU router contract version without hard import cycles."""
    try:
        from ares.query_understanding.router_engine import RouterEngine
    except ImportError:
        return DEFAULT_ANALYZER_VERSION
    return getattr(RouterEngine, "version", DEFAULT_ANALYZER_VERSION)
