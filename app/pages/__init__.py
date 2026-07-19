from app.pages.home import render as render_home
from app.pages.overview import render as render_overview
from app.pages.dataset import render as render_dataset
from app.pages.pipeline import render as render_pipeline
from app.pages.models import render as render_models
from app.pages.prediction import render as render_prediction
from app.pages.batch_prediction import render as render_batch_prediction
from app.pages.model_comparison import render as render_model_comparison
from app.pages.performance import render as render_performance
from app.pages.error_analysis import render as render_error_analysis
from app.pages.explainability import render as render_explainability
from app.pages.model_agreement import render as render_model_agreement
from app.pages.calibration import render as render_calibration
from app.pages.error_explorer import render as render_error_explorer
from app.pages.entity_detection import render as render_entity_detection
from app.pages.intent_detection import render as render_intent_detection
from app.pages.negation_detection import render as render_negation_detection
from app.pages.contradiction_detection import render as render_contradiction_detection
from app.pages.lexical_penalty import render as render_lexical_penalty
from app.pages.adaptive_ensemble import render as render_adaptive_ensemble
from app.pages.advanced_calibration import render as render_advanced_calibration
from app.pages.error_logger import render as render_error_logger
from app.pages.agreement_dashboard import render as render_agreement_dashboard
from app.pages.advanced_explainability import render as render_advanced_explainability
from app.pages.performance_optimizer import render as render_performance_optimizer
from app.pages.evaluation_suite import render as render_evaluation_suite
from app.pages.hard_test_generator import render as render_hard_test_generator
from app.pages.model_manager import render as render_model_manager

__all__ = [
    "render_home",
    "render_overview",
    "render_dataset",
    "render_pipeline",
    "render_models",
    "render_prediction",
    "render_batch_prediction",
    "render_model_comparison",
    "render_performance",
    "render_error_analysis",
    "render_explainability",
    "render_model_agreement",
    "render_calibration",
    "render_error_explorer",
    "render_entity_detection",
    "render_intent_detection",
    "render_negation_detection",
    "render_contradiction_detection",
    "render_lexical_penalty",
    "render_adaptive_ensemble",
    "render_advanced_calibration",
    "render_error_logger",
    "render_agreement_dashboard",
    "render_advanced_explainability",
    "render_performance_optimizer",
    "render_evaluation_suite",
    "render_hard_test_generator",
    "render_model_manager",
]
