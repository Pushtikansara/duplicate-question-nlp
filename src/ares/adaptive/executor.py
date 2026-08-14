from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any

from ares._result import PredictionResult
from ares.adaptive.budget import BudgetPolicy
from ares.adaptive.config_loader import AdaptiveRoutingConfig
from ares.adaptive.difficulty import DifficultyAnalyzer
from ares.adaptive.disagreement import DisagreementDetector
from ares.adaptive.models import (
    ComputeBudget,
    DifficultyAssessment,
    DisagreementAssessment,
    ModelEvidence,
    ReflectionRecord,
    RoutingPlan,
)
from ares.adaptive.policy import AdaptiveRoutingPolicy
from ares.adaptive.profiles import ModelProfileRegistry
from ares.adaptive.reflection import AdaptiveReflection
from ares.adaptive.trust import TrustAnalyzer, TrustAssessment
from ares.orchestration.constants import DEFAULT_THRESHOLD
from ares.orchestration.exceptions import OrchestrationError, TaskExecutionError
from ares.orchestration.interfaces import PredictionEngine
from ares.orchestration.strategy_registry import StrategyRegistry


@dataclass
class AdaptiveRun:
    """Complete record of one adaptive execution."""

    assessment: DifficultyAssessment = field(default_factory=DifficultyAssessment)
    plan: RoutingPlan = field(default_factory=RoutingPlan)
    budget: ComputeBudget = field(
        default_factory=lambda: ComputeBudget(
            name="low",
            max_model_calls=1,
            max_escalation_level=0,
            max_latency_ms=1000,
            reflection_allowed=False,
            fusion_min_models=0,
        )
    )
    evidences: list[ModelEvidence] = field(default_factory=list)
    results: list[PredictionResult] = field(default_factory=list)
    disagreement: DisagreementAssessment | None = None
    escalation_count: int = 0
    escalation_reasons: list[str] = field(default_factory=list)
    trust: TrustAssessment | None = None
    early_exit: bool = False
    early_exit_reason: str | None = None
    stopping_reason: str | None = None
    reflection: ReflectionRecord = field(default_factory=ReflectionRecord)
    final_strategy: str = ""
    final_model: str = ""
    final_confidence: float = 0.0
    review_required: bool = False
    total_latency_ms: float = 0.0
    routing_explanation: str = ""
    error: str | None = None
    error_code: str | None = None
    fallback_used: bool = False
    final_result: PredictionResult | None = None

    def to_trace_dict(self) -> dict[str, Any]:
        from ares.adaptive.trace import build_adaptive_trace

        trace = build_adaptive_trace(
            assessment=self.assessment,
            plan=self.plan,
            budget=self.budget,
            evidences=self.evidences,
            disagreement=self.disagreement,
            escalation_count=self.escalation_count,
            escalation_reasons=self.escalation_reasons,
            early_exit=self.early_exit,
            early_exit_reason=self.early_exit_reason,
            stopping_reason=self.stopping_reason,
            reflection=self.reflection,
            stages_executed=[],
            stages_skipped=[],
            consumed_latency_ms=self.total_latency_ms,
            final_strategy=self.final_strategy,
            final_model=self.final_model,
            final_confidence=self.final_confidence,
            review_required=self.review_required,
            routing_explanation=self.routing_explanation,
            error=self.error,
            error_code=self.error_code,
            fallback_used=self.fallback_used,
            trust=self.trust,
        )
        return trace

    def to_dict(self) -> dict[str, Any]:
        data = self.to_trace_dict()
        data["assessment"] = self.assessment.to_dict()
        data["final"] = {
            "final_strategy": self.final_strategy,
            "final_model": self.final_model,
            "final_confidence": self.final_confidence,
            "review_required": self.review_required,
        }
        return data


class AdaptiveExecutor:
    """Executes a routing plan against a prediction engine.

    Flows through: difficulty assessment -> budget allocation -> plan ->
    initial model -> early exit? -> escalation -> multi-model evidence ->
    disagreement-aware resolution -> conditional reflection -> final decision.
    Deterministic: no randomness, no external LLM.
    """

    def __init__(
        self,
        engine: PredictionEngine,
        *,
        config: dict[str, Any] | None = None,
        difficulty_analyzer: DifficultyAnalyzer | None = None,
        budget_policy: BudgetPolicy | None = None,
        routing_policy: AdaptiveRoutingPolicy | None = None,
        profile_registry: ModelProfileRegistry | None = None,
        disagreement_detector: DisagreementDetector | None = None,
        reflection_service: AdaptiveReflection | None = None,
        strategy_registry: StrategyRegistry | None = None,
        trust_analyzer: TrustAnalyzer | None = None,
    ) -> None:
        self._engine = engine or self._default_engine()
        self._config = AdaptiveRoutingConfig(config)
        self._strategies = strategy_registry or StrategyRegistry.with_defaults()
        if profile_registry is None:
            profile_registry = ModelProfileRegistry(config)
        if routing_policy is None:
            routing_policy = AdaptiveRoutingPolicy(
                config, strategy_registry=self._strategies, profile_registry=profile_registry
            )
        if disagreement_detector is None:
            disagreement_detector = DisagreementDetector(config, profile_registry=profile_registry)
        self._difficulty = difficulty_analyzer or DifficultyAnalyzer(config)
        self._budget = budget_policy or BudgetPolicy(config)
        self._policy = routing_policy
        self._profiles = profile_registry
        self._disagreement = disagreement_detector
        self._reflection = reflection_service or AdaptiveReflection(config)
        self._trust = trust_analyzer or TrustAnalyzer(config, profile_registry=profile_registry)
        self._last_run: AdaptiveRun | None = None

    @property
    def last_run(self) -> AdaptiveRun | None:
        return self._last_run

    @staticmethod
    def _default_engine() -> PredictionEngine:
        from ares.orchestration.engine_adapter import ARESPredictionEngine

        return ARESPredictionEngine()

    def execute(
        self,
        question1: str,
        question2: str,
        *,
        analysis: Any = None,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
        timeout_ms: float | None = None,
    ) -> AdaptiveRun:
        run = AdaptiveRun()
        self._last_run = run
        threshold = threshold if threshold is not None else DEFAULT_THRESHOLD

        cheap_confidence = None
        if analysis is not None:
            complexity = getattr(analysis, "complexity_analysis", None)
            if complexity is not None:
                estimate = getattr(complexity, "confidence_estimate", None)
                if estimate is not None:
                    try:
                        cheap_confidence = float(estimate)
                    except (TypeError, ValueError):
                        cheap_confidence = None

        assessment = self._difficulty.analyze(
            question1, question2, cheap_confidence=cheap_confidence, analysis=analysis
        )
        run.assessment = assessment
        budget = self._budget.allocate(assessment.difficulty_level, assessment.risk_level)
        if model:
            budget = _adjust_budget_for_override(budget)
        run.budget = budget
        run.routing_explanation = assessment.explanation

        plan = self._policy.make_plan(assessment, budget)
        if model:
            plan.initial_model = model
        run.plan = plan

        ladder = [plan.initial_strategy] + [s for s in plan.escalation_ladder if s != plan.initial_strategy]
        strategy_models = self._strategy_model_map()
        ladder_models: list[str] = []
        for strategy in ladder:
            model_name = strategy_models.get(strategy, plan.initial_model if strategy == plan.initial_strategy else "")
            if model_name and model_name not in ladder_models:
                ladder_models.append(model_name)
        if model and (not ladder_models or ladder_models[0] != model):
            ladder_models.insert(0, model)

        consumed_latency = 0.0
        initial_done = False
        early_exit = False
        early_exit_reason: str | None = None
        escalation_reasons: list[str] = []
        escalation_count = 0

        candidate_models: list[str] = []
        for model_name in ladder_models:
            if len(candidate_models) >= budget.max_model_calls:
                break
            candidate_models.append(model_name)
        if len(candidate_models) < budget.max_model_calls and self._config.fusion_enabled:
            for extra in self._fusion_candidates(ladder_models):
                if len(candidate_models) >= budget.max_model_calls:
                    break
                candidate_models.append(extra)

        results_acc: list[PredictionResult] = []
        evidences: list[ModelEvidence] = []
        errors: list[str] = []
        last_error: Exception | None = None
        stopping_reason: str | None = None

        for index, model_name in enumerate(candidate_models, start=1):
            if early_exit:
                break
            strategy_name = self._strategy_for_model(model_name, plan, strategy_models)
            if index > 1 and not self._config.escalation_enabled:
                stopping_reason = "escalation disabled by configuration"
                break
            if index > 1 and escalation_count >= budget.max_escalation_level:
                stopping_reason = f"escalation cap reached ({budget.max_escalation_level})"
                break
            if consumed_latency >= budget.max_latency_ms and index > 1:
                escalation_reasons.append("budget latency exhausted")
                stopping_reason = "budget latency exhausted"
                break

            call_started = time.perf_counter()
            result: PredictionResult | None = None
            error: str | None = None
            try:
                result = self._engine.predict(
                    question1,
                    question2,
                    model=model_name,
                    threshold=threshold,
                    reflect=False,
                    semantic_validation=False,
                    timeout_ms=timeout_ms,
                )
            except OrchestrationError as exc:
                error = str(exc)
                last_error = exc
            except Exception as exc:
                error = str(exc)
                last_error = exc

            call_latency = (time.perf_counter() - call_started) * 1000
            inference_latency = float(result.latency_ms) if result is not None and result.latency_ms else call_latency
            consumed_latency += inference_latency

            if result is not None:
                evidence = ModelEvidence(
                    model_name=result.model_name or model_name,
                    strategy=strategy_name,
                    predicted_label=result.predicted_label,
                    prediction=result.prediction,
                    confidence=result.confidence,
                    prob_duplicate=result.prob_duplicate,
                    latency_ms=result.latency_ms or call_latency,
                    rank=index,
                )
                evidences.append(evidence)
                results_acc.append(copy.copy(result))
            else:
                evidence = ModelEvidence(
                    model_name=model_name,
                    strategy=strategy_name,
                    predicted_label=-1,
                    prediction="error",
                    confidence=0.0,
                    prob_duplicate=0.0,
                    latency_ms=call_latency,
                    error=error,
                    rank=index,
                )
                evidences.append(evidence)
                errors.append(f"{model_name}: {error}")

            if not initial_done:
                initial_done = True
                if result is not None and len(evidences) == 1:
                    trust = self._trust.assess(assessment, evidences[0])
                    run.trust = trust
                    early_exit, early_exit_reason = self._check_early_exit(plan, assessment, result, threshold, trust)
                    if early_exit:
                        run.early_exit = True
                        run.early_exit_reason = early_exit_reason
                        run.escalation_count = 0
                        break

            if index > 1 and result is not None:
                escalation_count += 1
                if result.confidence is not None and result.confidence < self._config.confidence_medium:
                    escalation_reasons.append(f"confidence {result.confidence:.2f} below medium threshold")
                elif assessment.difficulty_level in ("hard", "critical"):
                    escalation_reasons.append(f"difficulty level {assessment.difficulty_level}")

        # Trust-based escalation: never let a cheap model decide blindly.  For
        # requests carrying structural signals a cheap lexical model cannot
        # judge (an acronym that expands to a phrase present in the other
        # question, or a positive prediction on near-zero content overlap --
        # the entity-substitution false-positive pattern), escalate once to the
        # strongest available model even when the difficulty plan said "easy".
        if (
            not early_exit
            and self._config.escalation_enabled
            and self._config.trust_escalation_enabled
            and consumed_latency < budget.max_latency_ms
            and escalation_count < self._config.trust_max_extra_models
        ):
            trusted_evidences = [e for e in evidences if e.error is None and e.prediction != "error"]
            if trusted_evidences:
                trust = run.trust or self._trust.assess(assessment, trusted_evidences[0])
                run.trust = trust
                strong = self._strong_verification_model(strategy_models, [e.model_name for e in evidences])
                if trust.escalation_required and strong:
                    trust_strategy = self._strategy_for_model(strong, plan, strategy_models)
                    try:
                        trust_result = self._engine.predict(
                            question1,
                            question2,
                            model=strong,
                            threshold=threshold,
                            reflect=False,
                            semantic_validation=False,
                            timeout_ms=timeout_ms,
                        )
                    except Exception as exc:
                        errors.append(f"{strong}: {exc}")
                        trust_result = None
                    trust_latency = (
                        float(trust_result.latency_ms) if trust_result is not None and trust_result.latency_ms else 0.0
                    )
                    consumed_latency += trust_latency
                    if trust_result is not None:
                        evidence = ModelEvidence(
                            model_name=trust_result.model_name or strong,
                            strategy=trust_strategy,
                            predicted_label=trust_result.predicted_label,
                            prediction=trust_result.prediction,
                            confidence=trust_result.confidence,
                            prob_duplicate=trust_result.prob_duplicate,
                            latency_ms=trust_result.latency_ms or trust_latency,
                            rank=len(evidences) + 1,
                        )
                        evidences.append(evidence)
                        results_acc.append(copy.copy(trust_result))
                    else:
                        evidences.append(
                            ModelEvidence(
                                model_name=strong,
                                strategy=trust_strategy,
                                predicted_label=-1,
                                prediction="error",
                                confidence=0.0,
                                prob_duplicate=0.0,
                                latency_ms=trust_latency,
                                error=errors[-1] if errors else "error",
                                rank=len(evidences) + 1,
                            )
                        )
                    escalation_count += 1
                    escalation_reasons.extend(trust.escalation_reasons)

        run.evidences = evidences
        run.results = results_acc
        run.escalation_count = escalation_count
        run.escalation_reasons = list(dict.fromkeys(escalation_reasons))
        run.total_latency_ms = consumed_latency
        if stopping_reason is None:
            stopping_reason = (run.early_exit_reason or "early_exit") if early_exit else "plan completed"
        run.stopping_reason = stopping_reason

        successful = [e for e in evidences if e.error is None and e.prediction != "error"]
        if not successful:
            run.error = f"all models failed: {'; '.join(errors)}" if errors else "no model executed"
            run.error_code = "ALL_MODELS_FAILED"
            if last_error is not None:
                raise last_error
            raise TaskExecutionError(run.error)

        disagreement = None
        decided_evidence: ModelEvidence | None = None
        if not early_exit and len(successful) >= 2:
            disagreement = self._disagreement.assess(
                successful,
                difficulty_level=assessment.difficulty_level,
                risk_level=assessment.risk_level,
            )
            run.disagreement = disagreement

        if early_exit:
            decided_evidence = successful[0]
            run.final_strategy = plan.initial_strategy
            run.final_model = decided_evidence.model_name
        else:
            decided_label, decided_prob = self._final_decision(successful, disagreement)
            deciding = self._pick_deciding_model(successful, decided_label)
            decided_evidence = deciding
            if disagreement is not None:
                decided_label, decided_prob = disagreement.resolution_label, disagreement.resolution_probability
            run.final_strategy = self._strategy_for_model(decided_evidence.model_name, plan, strategy_models)
            run.final_model = decided_evidence.model_name

        final_result = self._compose_result(
            decided_evidence,
            successful,
            threshold,
            run,
            decided_prob if disagreement is not None else None,
        )
        run.final_confidence = final_result.confidence
        run.final_strategy = run.final_strategy or plan.initial_strategy
        run.final_model = final_result.model_name
        run.final_result = final_result

        # Conditional reflection.
        reflection_requested = plan.reflection_requested or bool(reflect is True)
        skipped_reason = None
        if not reflection_requested:
            skipped_reason = plan.reflection_skipped_reason or "no reflection trigger"
        elif early_exit:
            skipped_reason = "early exit (high confidence / low risk)"
            reflection_requested = False
        elif not budget.reflection_allowed:
            skipped_reason = "budget does not allow reflection"
            reflection_requested = False

        agreement_score = None
        if disagreement is not None:
            ones = sum(1 for e in successful if e.predicted_label == disagreement.resolution_label)
            agreement_score = ones / len(successful)
        uncertainty = assessment.uncertainty_score
        model_count = len(successful)
        run.reflection = self._reflection.reflect(
            final_result,
            question1,
            question2,
            requested=reflection_requested,
            skipped_reason=skipped_reason,
            agreement=agreement_score,
            uncertainty=uncertainty,
            model_count=model_count,
            mode="fusion" if len(successful) > 1 else "selected",
        )

        run.review_required = bool(
            plan.human_review_recommended
            or run.reflection.human_review_required
            or (disagreement is not None and disagreement.disagreement_level == "high")
        )
        if run.review_required:
            final_result.human_review_required = True
            if "review_manually" not in (final_result.recommendations or []):
                final_result.recommendations = list(final_result.recommendations or []) + ["review_manually"]

        self._attach_explanations(final_result, run)
        run.total_latency_ms = round(consumed_latency, 3)
        return run

    def _check_early_exit(
        self,
        plan: RoutingPlan,
        assessment: DifficultyAssessment,
        result: PredictionResult,
        threshold: float,
        trust: TrustAssessment | None = None,
    ) -> tuple[bool, str | None]:
        if not self._config.early_exit_enabled:
            return False, None
        if not plan.early_exit_eligible:
            return False, None
        if assessment.difficulty_level in ("hard", "critical"):
            return False, None
        # Trust gate: never early-exit on a prediction the trust analysis says
        # must be re-verified by a stronger model (e.g. high-confidence cheap
        # duplicate on near-zero content overlap).
        if trust is not None and trust.escalation_required:
            return False, "trust_recheck_required"
        confidence = result.confidence or max(result.prob_duplicate, 1.0 - result.prob_duplicate)
        if confidence < self._config.early_exit_high_confidence_threshold:
            return False, None
        if self._config.early_exit_only_low_risk and assessment.risk_level not in ("low", "medium"):
            return False, None
        return True, "high_confidence_low_risk"

    def _strong_verification_model(self, strategy_models: dict[str, str], already: list[str]) -> str | None:
        """Strongest registered model not yet executed."""
        for strategy in ("cross_encoder", "ensemble"):
            model_name = strategy_models.get(strategy)
            if model_name and model_name not in already:
                return model_name
        best: str | None = None
        best_acc = -1.0
        for model_name in strategy_models.values():
            if model_name in already:
                continue
            profile = self._profiles.get(model_name)
            acc = profile.expected_accuracy if profile is not None else 0.5
            if acc > best_acc:
                best, best_acc = model_name, acc
        return best

    def _strategy_model_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for name in ("fast_lexical", "baseline_classifier", "cross_encoder", "ensemble"):
            if self._strategies.contains(name):
                try:
                    mapping[name] = self._strategies.resolve(name).model_name
                except Exception:
                    continue
        return mapping

    def _strategy_for_model(self, model_name: str, plan: RoutingPlan, strategy_models: dict[str, str]) -> str:
        for strategy, mapped in strategy_models.items():
            if mapped == model_name:
                return strategy
        if model_name == plan.initial_model:
            return plan.initial_strategy
        return "cross_encoder" if "Cross-Encoder" in model_name else "fast_lexical"

    def _fusion_candidates(self, already: list[str]) -> list[str]:
        pool = self._config.fusion_model_names
        if not pool:
            pool = [p.model_name for p in self._profiles.available()]
        result = []
        for name in pool:
            if name not in already:
                result.append(name)
        return result

    def _final_decision(
        self, successful: list[ModelEvidence], disagreement: DisagreementAssessment | None
    ) -> tuple[int, float]:
        if disagreement is not None:
            return disagreement.resolution_label, disagreement.resolution_probability
        labels = [e.predicted_label for e in successful]
        ones = sum(labels)
        label = 1 if ones > len(successful) - ones else 0
        agreeing = [e for e in successful if e.predicted_label == label]
        prob = sum(e.prob_duplicate for e in agreeing) / len(agreeing) if agreeing else 0.5
        return label, prob

    def _pick_deciding_model(self, successful: list[ModelEvidence], label: int) -> ModelEvidence:
        agreeing = [e for e in successful if e.predicted_label == label]
        candidates = agreeing or successful
        best = None
        best_acc = -1.0
        for evidence in candidates:
            profile = self._profiles.get(evidence.model_name)
            acc = profile.expected_accuracy if profile is not None else 0.5
            if acc > best_acc:
                best = evidence
                best_acc = acc
        return best if best is not None else successful[0]

    def _compose_result(
        self,
        deciding: ModelEvidence,
        successful: list[ModelEvidence],
        threshold: float,
        run: AdaptiveRun,
        decided_prob: float | None,
    ) -> PredictionResult:
        source = (
            run.results[successful.index(deciding)]
            if successful
            else PredictionResult(
                predicted_label=0,
                prediction="Non-Duplicate",
                confidence=0.5,
                prob_duplicate=0.5,
                prob_non_duplicate=0.5,
                model_name=deciding.model_name,
                latency_ms=0.0,
            )
        )
        prob = decided_prob if decided_prob is not None else deciding.prob_duplicate
        prob = max(0.0, min(1.0, prob))
        label = deciding.predicted_label if decided_prob is None else (1 if prob >= threshold else 0)
        prediction = "Duplicate" if label == 1 else "Non-Duplicate"
        confidence = max(prob, 1.0 - prob)
        executed = " + ".join(dict.fromkeys(e.model_name for e in successful))
        return PredictionResult(
            predicted_label=label,
            prediction=prediction,
            confidence=confidence,
            prob_duplicate=prob,
            prob_non_duplicate=1.0 - prob,
            model_name=deciding.model_name,
            latency_ms=run.total_latency_ms,
            selected_model=deciding.model_name,
            executed_model=executed,
            backend=source.backend,
            threshold=threshold,
        )

    def _attach_explanations(self, result: PredictionResult, run: AdaptiveRun) -> None:
        evidence_dicts = {e.model_name: e.to_dict() for e in run.evidences}
        result.explanations = {
            **(result.explanations or {}),
            "adaptive_routing": {
                "difficulty": run.assessment.to_dict(),
                "plan": run.plan.to_dict(),
                "disagreement": run.disagreement.to_dict() if run.disagreement else None,
                "early_exit": run.early_exit,
                "early_exit_reason": run.early_exit_reason,
                "escalation_reasons": list(run.escalation_reasons),
                "trust": run.trust.to_dict() if run.trust is not None else None,
                "reflection": run.reflection.to_dict(),
                "evidence": evidence_dicts,
            },
            "routing_explanation": run.routing_explanation,
        }


def _adjust_budget_for_override(budget: ComputeBudget) -> ComputeBudget:
    return ComputeBudget(
        name=budget.name,
        max_model_calls=budget.max_model_calls,
        max_escalation_level=budget.max_escalation_level,
        max_latency_ms=budget.max_latency_ms,
        reflection_allowed=budget.reflection_allowed,
        fusion_min_models=0,
        max_stages=budget.max_stages,
    )


class AdaptivePredictionEngine:
    """Adapters the ``AdaptiveExecutor`` to the Phase 13 ``PredictionEngine``
    protocol so the pipeline's prediction stage can run adaptive routing
    without any change to the orchestrator.

    A truthy ``model`` is treated as an explicit caller override (forced
    initial model, fusion disabled); an empty ``model`` means the router
    decides the path itself.  The resulting Phase 14 trace is attached to the
    returned ``PredictionResult.adaptive_trace`` for additive merging into the
    orchestration trace by the orchestrator.
    """

    def __init__(
        self,
        engine: PredictionEngine | None = None,
        *,
        config: dict[str, Any] | None = None,
        executor: AdaptiveExecutor | None = None,
        warmup: bool = True,
    ) -> None:
        self._executor = executor or AdaptiveExecutor(engine, config=config)
        self._config = AdaptiveRoutingConfig(config)
        self._warmed: list[str] = []
        if warmup:
            self.warmup()

    @property
    def executor(self) -> AdaptiveExecutor:
        return self._executor

    @property
    def warmed(self) -> list[str]:
        return list(self._warmed)

    def warmup(self, timeout_ms: float = 120_000.0) -> list[str]:
        """Load every model the router may invoke so the first real request is
        warm.  Model artifacts are cached process-wide, so a single warm pass
        benefits all subsequent requests.  Warm-up failures are recorded and
        skipped (lazy-loading fallback keeps the router usable)."""
        if self._warmed:
            return self._warmed
        engine = self._executor._engine
        models: list[str] = []
        try:
            for name in self._executor._strategy_model_map().values():
                if name and name not in models:
                    models.append(name)
        except Exception:
            models = []
        warmed: list[str] = []
        for name in models:
            try:
                engine.predict(
                    "warmup request",
                    "warm up request",
                    model=name,
                    threshold=0.5,
                    reflect=False,
                    semantic_validation=False,
                    timeout_ms=timeout_ms,
                )
                warmed.append(name)
            except Exception:
                continue
        self._warmed = warmed
        return warmed

    def predict(
        self,
        question1: str,
        question2: str,
        *,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool = True,
        semantic_validation: bool = True,
        timeout_ms: float | None = None,
    ) -> PredictionResult:
        del semantic_validation  # adaptive reflection is governed by the routing plan
        try:
            run = self._executor.execute(
                question1,
                question2,
                model=model,
                threshold=threshold,
                reflect=reflect,
                timeout_ms=timeout_ms,
            )
        except Exception as exc:
            from contextlib import suppress

            with suppress(Exception):
                exc._adaptive_run = self._executor.last_run
            self._attach_failure_trace(exc)
            raise
        if run.final_result is None:
            raise TaskExecutionError("Adaptive execution produced no final prediction result")
        run.final_result.adaptive_trace = run.to_trace_dict()
        return run.final_result

    @staticmethod
    def _attach_failure_trace(exc: Exception) -> None:
        """Attach the failure-safe adaptive trace to a raised exception so the
        orchestrator can surface error/error_code/fallback_used/routing trace."""
        run: AdaptiveRun | None = getattr(exc, "_adaptive_run", None)
        if run is None:
            return
        trace = run.to_trace_dict()
        from contextlib import suppress

        with suppress(Exception):
            exc.adaptive_trace = trace
