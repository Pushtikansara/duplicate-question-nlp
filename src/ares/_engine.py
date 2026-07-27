from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from ares._result import PredictionResult
from ares.confidence import (
    compute_final_confidence,
    compute_risk_level,
    compute_trust_level,
    compute_trust_score,
)
from ares.fusion import FusionEngine
from ares.inference.dispatcher import InferenceDispatcher
from ares.model_registry import ModelBackend, find_entry
from ares.semantic_validator import validate_semantic


class ARES:
    def __init__(self) -> None:
        self._model_name: str | None = None
        self._threshold: float | None = None
        self._use_reflection: bool = True
        self._use_semantic_validation: bool = True
        self._mode: str = "selected"
        self._loaded = False

    def with_model(self, name: str) -> ARES:
        self._model_name = name
        return self

    def with_threshold(self, threshold: float) -> ARES:
        self._threshold = threshold
        return self

    def with_reflection(self, enabled: bool = True) -> ARES:
        self._use_reflection = enabled
        return self

    def with_semantic_validation(self, enabled: bool = True) -> ARES:
        self._use_semantic_validation = enabled
        return self

    def with_fusion_mode(self, mode: str = "selected") -> ARES:
        self._mode = mode
        return self

    def _lazy_load(self) -> None:
        if self._loaded:
            return
        if self._model_name:
            InferenceDispatcher.validate_model(self._model_name)
        self._loaded = True

    def predict(self, question1: str, question2: str) -> PredictionResult:
        self._lazy_load()

        if self._model_name:
            model = self._model_name
        else:
            models = InferenceDispatcher.list_models()
            if not models:
                raise RuntimeError("No models available")
            model = models[0]

        if self._mode == "fusion":
            return self._predict_fusion(question1, question2)
        return self._predict_single(model, question1, question2)

    def _predict_single(self, model_name: str, question1: str, question2: str) -> PredictionResult:
        result = InferenceDispatcher.predict(
            model_name=model_name,
            question1=question1,
            question2=question2,
            threshold=self._threshold,
        )

        semantic_result = None
        if self._use_semantic_validation:
            semantic_result = validate_semantic(question1, question2, result)

        if self._use_reflection:
            self._apply_reflection(result, semantic_result, mode="selected")

        return result

    def _predict_fusion(self, question1: str, question2: str) -> PredictionResult:
        engine = FusionEngine()
        models = engine.get_available_models()

        if self._model_name and self._model_name != "Semantic Ensemble":
            entry = find_entry(self._model_name)
            if entry and entry.backend != ModelBackend.ENSEMBLE:
                models = [self._model_name]

        result = engine.fuse(question1, question2, model_names=None, threshold=self._threshold)

        if self._use_reflection:
            self._apply_reflection(result, None, mode="fusion")

        return result

    def _apply_reflection(
        self,
        result: PredictionResult,
        semantic_result: dict[str, Any] | None,
        mode: str = "selected",
    ) -> None:
        try:
            adjusted_conf = (
                semantic_result.get("adjusted_confidence", result.confidence) if semantic_result else result.confidence
            )
            has_contradiction = (
                semantic_result.get("semantic_detail", {}).get("contradiction_count", 0) if semantic_result else 0
            )

            explanations = result.explanations or {}
            agreement = explanations.get("agreement") if isinstance(explanations, dict) else None
            uncertainty = explanations.get("uncertainty") if isinstance(explanations, dict) else None
            model_count = explanations.get("model_count", 1) if isinstance(explanations, dict) else 1

            confidence_result = compute_final_confidence(
                raw_confidence=result.confidence,
                adjusted_confidence=adjusted_conf,
                agreement_score=agreement,
                trust_score=result.trust_score,
                uncertainty=uncertainty,
                mode=mode,
                model_count=model_count,
            )

            result.confidence = confidence_result["final_confidence"]

            trust_score = compute_trust_score(
                confidence=result.confidence,
                agreement=agreement,
                contradiction_count=has_contradiction,
                uncertainty=uncertainty,
            )

            result.trust_score = trust_score
            result.trust_level = compute_trust_level(trust_score)
            result.risk_level = compute_risk_level(
                trust_score=trust_score,
                confidence=result.confidence,
                agreement=agreement,
                uncertainty=uncertainty,
                contradiction_count=has_contradiction,
            )
            result.human_review_required = trust_score < 0.4
            result.recommendations = _generate_recommendations(trust_score)

            if semantic_result:
                result.explanations = {
                    **(result.explanations or {}),
                    "semantic_validation": semantic_result,
                    "confidence_calculation": confidence_result,
                }

        except Exception as exc:
            logger.warning("Reflection/confidence computation failed: %s", exc)

    def predict_batch(self, pairs: list[tuple[str, str]]) -> list[PredictionResult]:
        return [self.predict(q1, q2) for q1, q2 in pairs]

    @staticmethod
    def list_models() -> list[str]:
        return InferenceDispatcher.list_models()

    @staticmethod
    def get_backend_for_model(model_name: str) -> str:
        return InferenceDispatcher.get_backend_for_model(model_name)


def _generate_recommendations(trust_score: float) -> list[str]:
    recs: list[str] = []
    if trust_score >= 0.95:
        return recs
    if trust_score < 0.7:
        recs.append("review_manually")
    if trust_score < 0.5:
        recs.append("recheck_similarity")
    if trust_score < 0.3:
        recs.append("flag_for_expert_review")
    return recs
