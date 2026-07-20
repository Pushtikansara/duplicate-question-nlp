from app.pages.adaptive_ensemble import render as render_adaptive_ensemble
from app.pages.advanced_calibration import render as render_advanced_calibration
from app.pages.advanced_explainability import render as render_advanced_explainability
from app.pages.agreement_dashboard import render as render_agreement_dashboard
from app.pages.batch_prediction import render as render_batch_prediction
from app.pages.contradiction_detection import render as render_contradiction_detection
from app.pages.dataset import render as render_dataset
from app.pages.entity_detection import render as render_entity_detection
from app.pages.error_explorer import render as render_error_explorer
from app.pages.home import render as render_home
from app.pages.intent_detection import render as render_intent_detection
from app.pages.lexical_penalty import render as render_lexical_penalty
from app.pages.model_manager import render as render_model_manager
from app.pages.negation_detection import render as render_negation_detection
from app.pages.performance import render as render_performance
from app.pages.prediction import render as render_prediction

__all__ = [
    "render_home",
    "render_prediction",
    "render_batch_prediction",
    "render_performance",
    "render_entity_detection",
    "render_intent_detection",
    "render_negation_detection",
    "render_contradiction_detection",
    "render_lexical_penalty",
    "render_adaptive_ensemble",
    "render_advanced_calibration",
    "render_advanced_explainability",
    "render_agreement_dashboard",
    "render_error_explorer",
    "render_model_manager",
    "render_dataset",
]
