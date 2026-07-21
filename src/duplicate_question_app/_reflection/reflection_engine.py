from __future__ import annotations

import logging
from typing import Any

from duplicate_question_app._reflection.confidence_auditor import ConfidenceAuditor
from duplicate_question_app._reflection.configuration import ReflectionConfig
from duplicate_question_app._reflection.consistency_checker import ConsistencyChecker
from duplicate_question_app._reflection.debate_auditor import DebateAuditor
from duplicate_question_app._reflection.evidence_analyzer import EvidenceAnalyzer
from duplicate_question_app._reflection.explainability_engine import ExplainabilityEngine
from duplicate_question_app._reflection.human_review import HumanReviewDecider
from duplicate_question_app._reflection.interfaces import ReflectionPlugin
from duplicate_question_app._reflection.memory_auditor import MemoryAuditor
from duplicate_question_app._reflection.quality_estimator import QualityEstimator
from duplicate_question_app._reflection.reasoning_auditor import ReasoningAuditor
from duplicate_question_app._reflection.recommendation_engine import RecommendationEngine
from duplicate_question_app._reflection.reflection_result import ReflectionResult
from duplicate_question_app._reflection.routing_auditor import RoutingAuditor
from duplicate_question_app._reflection.trust_engine import TrustEngine

logger = logging.getLogger(__name__)


class ReflectionEngine:
    def __init__(
        self,
        config: ReflectionConfig | None = None,
        trust_engine: TrustEngine | None = None,
        routing_auditor: RoutingAuditor | None = None,
        reasoning_auditor: ReasoningAuditor | None = None,
        debate_auditor: DebateAuditor | None = None,
        memory_auditor: MemoryAuditor | None = None,
        confidence_auditor: ConfidenceAuditor | None = None,
        explainability_engine: ExplainabilityEngine | None = None,
        consistency_checker: ConsistencyChecker | None = None,
        evidence_analyzer: EvidenceAnalyzer | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        human_review_decider: HumanReviewDecider | None = None,
        quality_estimator: QualityEstimator | None = None,
        plugins: list[ReflectionPlugin] | None = None,
    ) -> None:
        self.config = config or ReflectionConfig()
        self.trust_engine = trust_engine or TrustEngine(self.config)
        self.routing_auditor = routing_auditor or RoutingAuditor()
        self.reasoning_auditor = reasoning_auditor or ReasoningAuditor()
        self.debate_auditor = debate_auditor or DebateAuditor()
        self.memory_auditor = memory_auditor or MemoryAuditor()
        self.confidence_auditor = confidence_auditor or ConfidenceAuditor()
        self.explainability_engine = explainability_engine or ExplainabilityEngine()
        self.consistency_checker = consistency_checker or ConsistencyChecker()
        self.evidence_analyzer = evidence_analyzer or EvidenceAnalyzer()
        self.recommendation_engine = recommendation_engine or RecommendationEngine(self.config)
        self.human_review_decider = human_review_decider or HumanReviewDecider(self.config)
        self.quality_estimator = quality_estimator or QualityEstimator()
        self.plugins = plugins or []

    def reflect(
        self,
        prediction: dict[str, Any],
        routing_result: Any = None,
        reasoning_result: Any = None,
        debate_result: Any = None,
        memory_manager: Any = None,
        pipeline_context: Any = None,
        calibration_data: dict[str, Any] | None = None,
    ) -> ReflectionResult:
        for plugin in self.plugins:
            try:
                plugin.before_reflection(pipeline_context)
            except Exception as e:
                logger.warning("Plugin before_reflection failed: %s", e)

        confidence = float(prediction.get("confidence", 0.5))

        routing_assessment = None
        if self.config.enable_routing_audit:
            try:
                routing_assessment = self.routing_auditor.audit(routing_result)
            except Exception as e:
                logger.warning("Routing audit failed: %s", e)

        reasoning_assessment = None
        if self.config.enable_reasoning_audit:
            try:
                reasoning_assessment = self.reasoning_auditor.audit(reasoning_result)
            except Exception as e:
                logger.warning("Reasoning audit failed: %s", e)

        debate_assessment = None
        if self.config.enable_debate_audit:
            try:
                debate_assessment = self.debate_auditor.audit(debate_result)
            except Exception as e:
                logger.warning("Debate audit failed: %s", e)

        memory_assessment = None
        if self.config.enable_memory_audit:
            try:
                memory_assessment = self.memory_auditor.audit(memory_manager, pipeline_context)
            except Exception as e:
                logger.warning("Memory audit failed: %s", e)

        confidence_assessment = None
        if self.config.enable_confidence_audit:
            try:
                confidence_assessment = self.confidence_auditor.audit(prediction, calibration_data)
            except Exception as e:
                logger.warning("Confidence audit failed: %s", e)

        evidence_analysis = self.evidence_analyzer.analyze(reasoning_result, debate_result)
        evidence_completeness = evidence_analysis.get("completeness", 0.0)

        explainability_data = {}
        if self.config.enable_explainability:
            try:
                assessments_dict = {
                    "routing": routing_assessment,
                    "reasoning": reasoning_assessment,
                    "debate": debate_assessment,
                    "memory": memory_assessment,
                    "confidence": confidence_assessment,
                }
                explainability_data = self.explainability_engine.generate(pipeline_context, 0.0, assessments_dict)
            except Exception as e:
                logger.warning("Explainability generation failed: %s", e)

        explainability_score = 0.0
        if explainability_data.get("module_contributions"):
            scores = list(explainability_data["module_contributions"].values())
            explainability_score = sum(scores) / len(scores) if scores else 0.0

        consistency_warnings: list[Any] = []
        if self.config.enable_consistency_check:
            try:
                consistency_warnings = self.consistency_checker.check(reasoning_result, debate_result, prediction)
            except Exception as e:
                logger.warning("Consistency check failed: %s", e)

        trust_score, trust_level, risk_level = self.trust_engine.compute_trust_score(
            routing_assessment=routing_assessment,
            reasoning_assessment=reasoning_assessment,
            debate_assessment=debate_assessment,
            memory_assessment=memory_assessment,
            confidence_assessment=confidence_assessment,
            explainability_score=explainability_score,
            evidence_completeness=evidence_completeness,
        )

        recommendations = []
        if self.config.enable_recommendations:
            try:
                recommendations = self.recommendation_engine.generate(
                    trust_score=trust_score,
                    confidence=confidence,
                    routing_assessment=routing_assessment,
                    reasoning_assessment=reasoning_assessment,
                    debate_assessment=debate_assessment,
                    memory_assessment=memory_assessment,
                    consistency_warnings=consistency_warnings,
                    evidence_completeness=evidence_completeness,
                )
            except Exception as e:
                logger.warning("Recommendation generation failed: %s", e)

        human_review_required = False
        human_review_reason = ""
        if self.config.enable_human_review:
            try:
                human_review_required, human_review_reason = self.human_review_decider.should_review(
                    trust_score=trust_score,
                    confidence=confidence,
                    routing_assessment=routing_assessment,
                    reasoning_assessment=reasoning_assessment,
                    debate_assessment=debate_assessment,
                    consistency_warnings=consistency_warnings,
                    recommendations=recommendations,
                    explainability_score=explainability_score,
                )
            except Exception as e:
                logger.warning("Human review decision failed: %s", e)

        quality_info = self.quality_estimator.estimate(
            type(
                "_",
                (),
                {
                    "trust_score": trust_score,
                    "consistency_warnings": consistency_warnings,
                    "routing_assessment": routing_assessment,
                    "reasoning_assessment": reasoning_assessment,
                    "debate_assessment": debate_assessment,
                    "memory_assessment": memory_assessment,
                    "confidence_assessment": confidence_assessment,
                },
            )()
        )

        result = ReflectionResult(
            prediction=prediction,
            confidence=confidence,
            trust_score=round(trust_score, 2),
            trust_level=trust_level,
            risk_level=risk_level,
            routing_assessment=routing_assessment,
            reasoning_assessment=reasoning_assessment,
            debate_assessment=debate_assessment,
            memory_assessment=memory_assessment,
            confidence_assessment=confidence_assessment,
            explainability_score=round(explainability_score, 4),
            evidence_completeness=round(evidence_completeness, 4),
            consistency_warnings=consistency_warnings,
            recommendations=recommendations,
            human_review_required=human_review_required,
            human_review_reason=human_review_reason,
            metadata={
                "quality": quality_info,
                "explainability": explainability_data,
                "evidence_analysis": evidence_analysis,
            },
        )

        for plugin in self.plugins:
            try:
                plugin.after_reflection(result)
            except Exception as e:
                logger.warning("Plugin after_reflection failed: %s", e)

        return result
