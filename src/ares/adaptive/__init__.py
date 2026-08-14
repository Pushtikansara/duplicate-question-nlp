from __future__ import annotations

"""ARES Adaptive Routing & Intelligence layer (Phase 14).

The package decides how much computation a request deserves: which model to
run first, whether a cheap model suffices, whether a stronger model or extra
models are required, whether reflection is justified, and when to stop.
Everything is deterministic and configuration-driven; the package is
domain-agnostic (a "request" is a pair of strings) so future applications
can reuse the router unchanged.

Public surface (import from this package):
  - AdaptiveExecutor / AdaptivePredictionEngine: run one adaptive request.
  - DifficultyAnalyzer: deterministic difficulty / uncertainty / risk.
  - AdaptiveRoutingPolicy + BudgetPolicy: plans and budgets.
  - ModelProfileRegistry: capability/cost profiles from the model registry.
  - DisagreementDetector: cross-model disagreement + resolution.
  - AdaptiveReflection: conditional reflection.
  - build_adaptive_trace: additive Phase 14 trace sections.
"""

from ares.adaptive.budget import BudgetPolicy
from ares.adaptive.difficulty import DifficultyAnalyzer
from ares.adaptive.disagreement import DisagreementDetector
from ares.adaptive.executor import AdaptiveExecutor, AdaptivePredictionEngine, AdaptiveRun
from ares.adaptive.models import (
    ComputeBudget,
    DifficultyAssessment,
    DisagreementAssessment,
    ModelEvidence,
    ModelProfile,
    ReflectionRecord,
    RoutingPlan,
)
from ares.adaptive.policy import AdaptiveRoutingPolicy
from ares.adaptive.profiles import ModelProfileRegistry
from ares.adaptive.reflection import AdaptiveReflection
from ares.adaptive.trace import build_adaptive_trace
from ares.adaptive.trust import TrustAnalyzer, TrustAssessment

__all__ = [
    "AdaptiveExecutor",
    "AdaptivePredictionEngine",
    "AdaptiveRun",
    "AdaptiveRoutingPolicy",
    "AdaptiveReflection",
    "BudgetPolicy",
    "DifficultyAnalyzer",
    "DifficultyAssessment",
    "DisagreementDetector",
    "DisagreementAssessment",
    "ComputeBudget",
    "ModelEvidence",
    "ModelProfile",
    "ModelProfileRegistry",
    "ReflectionRecord",
    "RoutingPlan",
    "TrustAnalyzer",
    "TrustAssessment",
    "build_adaptive_trace",
]
