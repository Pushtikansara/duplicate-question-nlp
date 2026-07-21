from __future__ import annotations

from unittest.mock import Mock

import pytest

from duplicate_question_app._perception.cognitive_representation import Metadata as PerceptionMetadata
from duplicate_question_app._reasoning.reasoning_result import ConfidenceChain, ProcessingMetadata, ReasoningResult
from duplicate_question_app._routing.configuration import RoutingConfig
from duplicate_question_app._routing.routing_context import RoutingContext
from duplicate_question_app._routing.routing_strategy import RoutingStrategy
from duplicate_question_app._semantic_intelligence.semantic_assessment import Conflict, SemanticAssessment


@pytest.fixture
def sample_simple_questions() -> tuple[str, str]:
    return ("What is Python?", "What is Python programming language?")


@pytest.fixture
def sample_medium_questions() -> tuple[str, str]:
    return (
        "How to install Python on Ubuntu?",
        "What is the best way to set up Python on Linux?",
    )


@pytest.fixture
def sample_complex_questions() -> tuple[str, str]:
    return (
        "What is the difference between Python 2 and Python 3 in terms of"
        " Unicode handling, print function, and integer division? Also how does"
        " the migration affect existing codebases and what are the best strategies"
        " for transitioning large projects?",
        "Compare Python 2 and Python 3. What are the key differences in syntax,"
        " performance, and library support? How should teams approach migration"
        " from Python 2 to Python 3 given the end-of-life considerations?",
    )


@pytest.fixture
def sample_greeting_questions() -> tuple[str, str]:
    return ("Hi", "Hello")


@pytest.fixture
def sample_empty_questions() -> tuple[str, str]:
    return ("", "")


@pytest.fixture
def sample_perception_metadata() -> PerceptionMetadata:
    return PerceptionMetadata(
        length=120,
        char_count=120,
        word_count=20,
        sentence_count=2,
        question_type="wh-what",
        has_question_mark=True,
    )


@pytest.fixture
def sample_routing_context(sample_simple_questions) -> RoutingContext:
    qa, qb = sample_simple_questions
    return RoutingContext(
        question_a=qa,
        question_b=qb,
        cross_encoder_score=0.85,
        perception_metadata=PerceptionMetadata(
            length=len(qa) + len(qb),
            char_count=len(qa) + len(qb),
            word_count=len(qa.split()) + len(qb.split()),
            sentence_count=2,
            question_type="wh-what",
        ),
    )


@pytest.fixture
def default_config() -> RoutingConfig:
    return RoutingConfig()


@pytest.fixture
def fast_config() -> RoutingConfig:
    return RoutingConfig(default_strategy=RoutingStrategy.FASTEST)


@pytest.fixture
def accuracy_config() -> RoutingConfig:
    return RoutingConfig(default_strategy=RoutingStrategy.HIGHEST_ACCURACY)


@pytest.fixture
def research_config() -> RoutingConfig:
    return RoutingConfig(default_strategy=RoutingStrategy.RESEARCH)


@pytest.fixture
def mock_semantic_assessment() -> SemanticAssessment:
    return SemanticAssessment(
        semantic_similarity=0.85,
        confidence=0.9,
        conflicts=[],
    )


@pytest.fixture
def mock_semantic_assessment_low_conf() -> SemanticAssessment:
    return SemanticAssessment(
        semantic_similarity=0.35,
        confidence=0.3,
        conflicts=[],
    )


@pytest.fixture
def mock_semantic_assessment_with_conflicts() -> SemanticAssessment:
    return SemanticAssessment(
        semantic_similarity=0.6,
        confidence=0.7,
        conflicts=[
            Conflict(conflict_type="entity_mismatch", description="Entities do not align", severity=0.8),
        ],
    )


@pytest.fixture
def mock_reasoning_result() -> ReasoningResult:
    return ReasoningResult(
        decision="duplicate",
        confidence=0.85,
        uncertainty=0.15,
        confidence_chain=ConfidenceChain(decision_confidence=0.85),
        processing_metadata=ProcessingMetadata(),
    )


@pytest.fixture
def mock_reasoning_result_high_uncertainty() -> ReasoningResult:
    return ReasoningResult(
        decision="uncertain",
        confidence=0.3,
        uncertainty=0.8,
        confidence_chain=ConfidenceChain(decision_confidence=0.3),
        processing_metadata=ProcessingMetadata(),
    )


@pytest.fixture
def mock_complexity_estimator() -> Mock:
    from duplicate_question_app._routing.routing_result import ComplexityResult

    mock = Mock()
    mock.estimate.return_value = ComplexityResult(
        complexity="simple",
        score=0.2,
        features={"avg_word_count": 5, "entity_count": 0},
        explanation="Short factual question",
    )
    return mock


@pytest.fixture
def mock_uncertainty_router() -> Mock:
    from duplicate_question_app._routing.routing_result import UncertaintyResult

    mock = Mock()
    mock.should_escalate.return_value = UncertaintyResult(
        should_escalate=False,
        reason="All scores acceptable",
        uncertainty_score=0.0,
        contributing_factors=[],
    )
    return mock


@pytest.fixture
def mock_pipeline_selector() -> Mock:
    from duplicate_question_app._routing.routing_result import PipelineSelection

    mock = Mock()
    mock.select.return_value = PipelineSelection(
        pipeline="cross_encoder_only",
        required_modules=["cross_encoder"],
        skipped_modules=["semantic_intelligence", "reasoning", "made"],
        reason="Simple question",
    )
    return mock


@pytest.fixture
def mock_cost_estimator() -> Mock:
    mock = Mock()
    mock.estimate_cost.return_value = 0.1
    return mock


@pytest.fixture
def mock_latency_estimator() -> Mock:
    mock = Mock()
    mock.estimate_latency.return_value = 100.0
    return mock


@pytest.fixture
def mock_estimators(
    mock_complexity_estimator,
    mock_uncertainty_router,
    mock_pipeline_selector,
    mock_cost_estimator,
    mock_latency_estimator,
) -> dict:
    return {
        "complexity_estimator": mock_complexity_estimator,
        "uncertainty_router": mock_uncertainty_router,
        "pipeline_selector": mock_pipeline_selector,
        "cost_estimator": mock_cost_estimator,
        "latency_estimator": mock_latency_estimator,
    }
