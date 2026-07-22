"""Error Driven Learning — automatically logs every wrong prediction for analysis.

Creates hard_examples.csv with:
- question1, question2
- prediction, true_label
- confidence, reason
- error categories (entity mismatch, intent mismatch, negation, contradiction, etc.)
- model agreement details
- timestamp

Also provides utilities for:
- Mining hardest examples
- Generating error reports
- Tracking model improvements over time
"""

from __future__ import annotations

import contextlib
import csv
import json
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd


class ErrorCategory(Enum):
    ENTITY_MISMATCH = "entity_mismatch"
    INTENT_MISMATCH = "intent_mismatch"
    NEGATION_MISMATCH = "negation_mismatch"
    CONTRADICTION = "contradiction"
    LEXICAL_MISMATCH = "lexical_mismatch"
    LOW_CONFIDENCE = "low_confidence"
    MODEL_DISAGREEMENT = "model_disagreement"
    SYNONYM_CONFUSION = "synonym_confusion"
    ABBREVIATION_CONFUSION = "abbreviation_confusion"
    VERSION_MISMATCH = "version_mismatch"
    UNKNOWN = "unknown"


@dataclass
class ErrorExample:
    """A single misclassified example with full metadata."""

    # Core fields
    question1: str
    question2: str
    predicted_label: int
    true_label: int
    prob_duplicate: float
    confidence: float

    # Error categorization
    error_categories: list[str] = field(default_factory=list)
    error_details: dict[str, Any] = field(default_factory=dict)

    # Model details
    model_name: str = ""
    model_version: str = ""

    # Ensemble details (if applicable)
    ensemble_weights: dict[str, float] = field(default_factory=dict)
    model_votes: dict[str, int] = field(default_factory=dict)
    model_probs: dict[str, float] = field(default_factory=dict)
    agreement_score: float = 0.0

    # Feature analysis
    lexical_overlap: float = 0.0
    semantic_depth: float = 0.0
    entity_overlap: float = 0.0
    intent_q1: str = ""
    intent_q2: str = ""
    has_negation_q1: bool = False
    has_negation_q2: bool = False
    contradiction_score: float = 0.0
    lexical_penalty: float = 0.0

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Convert enums to strings
        d["error_categories"] = [str(c) for c in self.error_categories]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ErrorExample:
        return cls(**data)


@dataclass
class ErrorLogConfig:
    """Configuration for error logging."""

    log_path: Path = Path("hard_examples.csv")
    append_mode: bool = True
    include_metadata: bool = True
    max_file_size_mb: int = 100
    auto_flush: bool = True


class ErrorLogger:
    """Thread-safe error logger for duplicate question detection."""

    def __init__(self, config: ErrorLogConfig | None = None):
        self.config = config or ErrorLogConfig()
        self._lock = threading.Lock()
        self._buffer: list[ErrorExample] = []
        self._buffer_size = 100
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure directory exists
        self.config.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize CSV if not exists
        if not self.config.log_path.exists() or not self.config.append_mode:
            self._write_header()

    def _write_header(self):
        """Write CSV header."""
        fieldnames = [
            "timestamp",
            "session_id",
            "question1",
            "question2",
            "predicted_label",
            "true_label",
            "prob_duplicate",
            "confidence",
            "error_categories",
            "model_name",
            "model_version",
            "ensemble_weights",
            "model_votes",
            "model_probs",
            "agreement_score",
            "lexical_overlap",
            "semantic_depth",
            "entity_overlap",
            "intent_q1",
            "intent_q2",
            "has_negation_q1",
            "has_negation_q2",
            "contradiction_score",
            "lexical_penalty",
            "notes",
        ]
        with open(self.config.log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    def log_error(
        self,
        question1: str,
        question2: str,
        predicted_label: int,
        true_label: int,
        prob_duplicate: float,
        confidence: float,
        model_name: str = "",
        model_version: str = "",
        error_categories: list[ErrorCategory] | None = None,
        error_details: dict[str, Any] | None = None,
        ensemble_weights: dict[str, float] | None = None,
        model_votes: dict[str, int] | None = None,
        model_probs: dict[str, float] | None = None,
        agreement_score: float = 0.0,
        lexical_overlap: float = 0.0,
        semantic_depth: float = 0.0,
        entity_overlap: float = 0.0,
        intent_q1: str = "",
        intent_q2: str = "",
        has_negation_q1: bool = False,
        has_negation_q2: bool = False,
        contradiction_score: float = 0.0,
        lexical_penalty: float = 0.0,
        notes: str = "",
    ) -> ErrorExample:
        """Log a misclassified example."""
        example = ErrorExample(
            question1=question1,
            question2=question2,
            predicted_label=predicted_label,
            true_label=true_label,
            prob_duplicate=prob_duplicate,
            confidence=confidence,
            model_name=model_name,
            model_version=model_version,
            error_categories=[str(c) for c in (error_categories or [])],
            error_details=error_details or {},
            ensemble_weights=ensemble_weights or {},
            model_votes=model_votes or {},
            model_probs=model_probs or {},
            agreement_score=agreement_score,
            lexical_overlap=lexical_overlap,
            semantic_depth=semantic_depth,
            entity_overlap=entity_overlap,
            intent_q1=intent_q1,
            intent_q2=intent_q2,
            has_negation_q1=has_negation_q1,
            has_negation_q2=has_negation_q2,
            contradiction_score=contradiction_score,
            lexical_penalty=lexical_penalty,
            session_id=self._session_id,
            notes=notes,
        )

        with self._lock:
            self._buffer.append(example)
            if len(self._buffer) >= self._buffer_size or self.config.auto_flush:
                self._flush_buffer()

        return example

    def _flush_buffer(self):
        """Write buffered examples to CSV."""
        if not self._buffer:
            return

        fieldnames = [
            "timestamp",
            "session_id",
            "question1",
            "question2",
            "predicted_label",
            "true_label",
            "prob_duplicate",
            "confidence",
            "error_categories",
            "model_name",
            "model_version",
            "ensemble_weights",
            "model_votes",
            "model_probs",
            "agreement_score",
            "lexical_overlap",
            "semantic_depth",
            "entity_overlap",
            "intent_q1",
            "intent_q2",
            "has_negation_q1",
            "has_negation_q2",
            "contradiction_score",
            "lexical_penalty",
            "notes",
        ]

        with open(self.config.log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            for ex in self._buffer:
                row = {
                    "timestamp": ex.timestamp,
                    "session_id": ex.session_id,
                    "question1": ex.question1,
                    "question2": ex.question2,
                    "predicted_label": ex.predicted_label,
                    "true_label": ex.true_label,
                    "prob_duplicate": ex.prob_duplicate,
                    "confidence": ex.confidence,
                    "error_categories": ";".join(str(c) for c in ex.error_categories),
                    "model_name": ex.model_name,
                    "model_version": ex.model_version,
                    "ensemble_weights": json.dumps(ex.ensemble_weights),
                    "model_votes": json.dumps(ex.model_votes),
                    "model_probs": json.dumps(ex.model_probs),
                    "agreement_score": ex.agreement_score,
                    "lexical_overlap": ex.lexical_overlap,
                    "semantic_depth": ex.semantic_depth,
                    "entity_overlap": ex.entity_overlap,
                    "intent_q1": ex.intent_q1,
                    "intent_q2": ex.intent_q2,
                    "has_negation_q1": ex.has_negation_q1,
                    "has_negation_q2": ex.has_negation_q2,
                    "contradiction_score": ex.contradiction_score,
                    "lexical_penalty": ex.lexical_penalty,
                    "notes": ex.notes,
                }
                writer.writerow(row)

        self._buffer.clear()

        # Check file size, rotate if needed
        if self.config.log_path.stat().st_size > self.config.max_file_size_mb * 1024 * 1024:
            self._rotate_log()

    def _rotate_log(self):
        """Rotate log file when it gets too large."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config.log_path.with_name(f"{self.config.log_path.stem}_{timestamp}.csv")
        self.config.log_path.rename(backup_path)
        self._write_header()

    def flush(self):
        """Force flush buffer."""
        with self._lock:
            self._flush_buffer()

    def log_prediction_error(
        self,
        q1: str,
        q2: str,
        result: dict[str, Any],
        true_label: int,
        error_analysis: dict[str, Any] | None = None,
    ) -> ErrorExample | None:
        """Convenience method to log error from a prediction result."""
        predicted_label = result.get("predicted_label", 0)
        if predicted_label == true_label:
            return None  # Not an error

        prob_duplicate = result.get("prob_duplicate", 0.5)
        confidence = result.get("confidence", 0.0)
        model_name = result.get("model_label", "")
        model_version = result.get("model_version", "")

        # Extract error categories from analysis
        error_categories = []
        if error_analysis:
            for err in error_analysis.get("error_categories", []):
                if err.get("detected"):
                    with contextlib.suppress(ValueError):
                        error_categories.append(ErrorCategory(err["name"].lower().replace(" ", "_")))

        return self.log_error(
            question1=q1,
            question2=q2,
            predicted_label=predicted_label,
            true_label=true_label,
            prob_duplicate=prob_duplicate,
            confidence=confidence,
            model_name=model_name,
            model_version=model_version,
            error_categories=error_categories,
            error_details=error_analysis,
            ensemble_weights=result.get("adaptive_weights", {}),
            model_votes=result.get("models_agreeing", {}),
            model_probs=result.get("feature_breakdown", {}),
            agreement_score=result.get("feature_analysis", {}).get("model_agreement", 0.0),
            lexical_overlap=result.get("feature_analysis", {}).get("lexical_overlap", 0.0),
            semantic_depth=result.get("feature_analysis", {}).get("semantic_depth", 0.0),
        )


def load_error_log(path: Path) -> pd.DataFrame:
    """Load error log as DataFrame."""
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    # Parse JSON columns
    for col in ["ensemble_weights", "model_votes", "model_probs"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.loads(x) if isinstance(x, str) and x else {})

    # Parse error categories
    if "error_categories" in df.columns:
        df["error_categories_list"] = df["error_categories"].apply(
            lambda x: x.split(";") if isinstance(x, str) and x else []
        )

    return df


def analyze_error_log(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze error log and return statistics."""
    if df.empty:
        return {}

    total_errors = len(df)
    fp = df[df["predicted_label"] == 1]  # False positives
    fn = df[df["predicted_label"] == 0]  # False negatives

    # Error category distribution
    cat_counts: dict[str, int] = defaultdict(int)
    for cats in df["error_categories_list"]:
        for cat in cats:
            cat_counts[cat] += 1

    # Confidence distribution for errors
    conf_stats = {
        "mean": df["confidence"].mean(),
        "median": df["confidence"].median(),
        "std": df["confidence"].std(),
        "min": df["confidence"].min(),
        "max": df["confidence"].max(),
    }

    # Most common error patterns
    top_errors = df.nlargest(10, "confidence")[["question1", "question2", "confidence", "error_categories"]].to_dict(
        "records"
    )

    return {
        "total_errors": total_errors,
        "false_positives": len(fp),
        "false_negatives": len(fn),
        "error_categories": dict(cat_counts),
        "confidence_stats": conf_stats,
        "top_confident_errors": top_errors,
        "avg_lexical_overlap": df["lexical_overlap"].mean(),
        "avg_semantic_depth": df["semantic_depth"].mean(),
        "avg_entity_overlap": df["entity_overlap"].mean(),
        "avg_contradiction_score": df["contradiction_score"].mean(),
    }


def mine_hard_examples(
    df: pd.DataFrame,
    n: int = 100,
    strategy: str = "confidence",
) -> pd.DataFrame:
    """Mine hardest examples from error log.

    Strategies:
    - 'confidence': Highest confidence errors (model was sure but wrong)
    - 'disagreement': Highest model disagreement
    - 'lexical': Lowest lexical overlap
    - 'balanced': Mix of all
    """
    if df.empty:
        return df

    if strategy == "confidence":
        return df.nlargest(n, "confidence")
    elif strategy == "disagreement":
        # Low agreement = high disagreement
        if "agreement_score" in df.columns:
            return df.nsmallest(n, "agreement_score")
        return df
    elif strategy == "lexical":
        return df.nsmallest(n, "lexical_overlap")
    elif strategy == "balanced":
        # Score combining multiple factors
        df = df.copy()
        df["hardness"] = (
            df["confidence"] * 0.3
            + (1 - df.get("agreement_score", 0.5)) * 0.3
            + (1 - df.get("lexical_overlap", 0.5)) * 0.2
            + df.get("contradiction_score", 0) * 0.2
        )
        return df.nlargest(n, "hardness")
    else:
        return df.head(n)


def generate_error_report(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generate comprehensive error analysis report."""
    analysis = analyze_error_log(df)

    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": analysis,
        "recommendations": _generate_recommendations(analysis),
    }

    output_path.write_text(json.dumps(report, indent=2, default=str))


def _generate_recommendations(analysis: dict[str, Any]) -> list[str]:
    """Generate improvement recommendations based on error analysis."""
    recs = []

    cat_dist = analysis.get("error_categories", {})
    total = analysis.get("total_errors", 1)

    if cat_dist.get("entity_mismatch", 0) / total > 0.2:
        recs.append("High entity mismatch rate: Improve entity detection and add entity-based penalties")

    if cat_dist.get("intent_mismatch", 0) / total > 0.15:
        recs.append("High intent mismatch rate: Add intent classifier and intent-based routing in ensemble")

    if cat_dist.get("negation_mismatch", 0) / total > 0.1:
        recs.append("Negation errors detected: Strengthen negation detection and add explicit negation features")

    if cat_dist.get("contradiction", 0) / total > 0.05:
        recs.append("Contradiction errors: Integrate NLI-based contradiction detection into ensemble")

    if cat_dist.get("lexical_mismatch", 0) / total > 0.15:
        recs.append("Lexical mismatch: Increase weight of lexical features for low-overlap pairs")

    if cat_dist.get("model_disagreement", 0) / total > 0.2:
        recs.append("High model disagreement: Investigate ensemble weight calibration")

    conf_stats = analysis.get("confidence_stats", {})
    if conf_stats.get("mean", 0) > 0.8:
        recs.append("Errors have high average confidence: Model is overconfident, apply calibration")

    if analysis.get("avg_lexical_overlap", 0) < 0.2:
        recs.append("Low lexical overlap on errors: Ensure semantic models handle low-overlap pairs")

    return recs


# Global logger instance
_default_logger: ErrorLogger | None = None


def get_error_logger(config: ErrorLogConfig | None = None) -> ErrorLogger:
    """Get or create the global error logger."""
    global _default_logger
    if _default_logger is None or config is not None:
        _default_logger = ErrorLogger(config)
    return _default_logger


def log_prediction_error(
    q1: str,
    q2: str,
    result: dict[str, Any],
    true_label: int,
    error_analysis: dict[str, Any] | None = None,
) -> ErrorExample | None:
    """Convenience function to log prediction error."""
    logger = get_error_logger()
    return logger.log_prediction_error(q1, q2, result, true_label, error_analysis)
