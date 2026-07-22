from __future__ import annotations

from typing import Any

import pandas as pd

from duplicate_question_app._evaluation.error_analysis import (
    categorize_error,
    classify_hardness,
    generate_error_report,
)


class ErrorAnalyzer:
    def analyze_single(
        self,
        q1: str,
        q2: str,
        predicted_label: int,
        prob_duplicate: float,
        true_label: int | None = None,
        all_model_probs: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result: Any = generate_error_report(
            q1, q2, predicted_label, prob_duplicate, true_label, all_model_probs, metadata
        )
        return dict(result)

    def analyze_batch(
        self,
        df: pd.DataFrame,
        q1_col: str = "q1",
        q2_col: str = "q2",
        pred_col: str = "predicted_label",
        prob_col: str = "prob_duplicate",
        true_col: str = "true_label",
    ) -> pd.DataFrame:
        results = []
        for _, row in df.iterrows():
            r = self.analyze_single(
                q1=str(row.get(q1_col, "")),
                q2=str(row.get(q2_col, "")),
                predicted_label=int(row.get(pred_col, 0)),
                prob_duplicate=float(row.get(prob_col, 0.5)),
                true_label=int(row.get(true_col, -1)) if true_col in row and pd.notna(row.get(true_col)) else None,
            )
            results.append(r)
        return pd.DataFrame(results)

    def classify_hardness(
        self,
        prob_duplicate: float,
        confidence: float,
        model_agreement: float,
        predicted_label: int,
        true_label: int | None = None,
    ) -> str:
        result: Any = classify_hardness(prob_duplicate, confidence, model_agreement, predicted_label, true_label)
        return str(result)

    def find_errors_by_category(
        self,
        df: pd.DataFrame,
        q1_col: str = "q1",
        q2_col: str = "q2",
        prob_col: str = "prob_duplicate",
        pred_col: str = "predicted_label",
        true_col: str = "true_label",
    ) -> dict[str, list[int]]:
        result: dict[str, list[int]] = {}
        for idx, row in df.iterrows():
            q1 = str(row.get(q1_col, ""))
            q2 = str(row.get(q2_col, ""))
            prob = float(row.get(prob_col, 0.5))
            pred = int(row.get(pred_col, 0))
            true_val = row.get(true_col) if true_col in row else None
            true = int(true_val) if true_val is not None and pd.notna(true_val) else None
            errors = categorize_error(q1, q2, pred, true, prob)
            for e in errors:
                if e.name not in result:
                    result[e.name] = []
                result[e.name].append(idx)
        return result
