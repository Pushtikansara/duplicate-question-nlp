from duplicate_question_app._integration.cognitive_pipeline import CognitivePipeline
from duplicate_question_app._integration.compatibility import ModuleUnavailable, is_module_available
from duplicate_question_app._integration.integration_configuration import IntegrationConfig
from duplicate_question_app._integration.integration_context import IntegrationContext
from duplicate_question_app._integration.lifecycle import LifecycleManager, ModuleState, ModuleStatus
from duplicate_question_app._integration.pipeline_context import PipelineContext
from duplicate_question_app._integration.pipeline_events import PipelineEvent
from duplicate_question_app._integration.pipeline_hooks import PipelineHook
from duplicate_question_app._integration.pipeline_result import PipelineExecutionMetadata, PipelineResult
from duplicate_question_app._integration.plugins import DefaultIntegrationPlugin, IntegrationPlugin
from duplicate_question_app._integration.validation import (
    ValidationResult,
    validate_pipeline_context,
    validate_prediction_unchanged,
)

__all__ = [
    "PipelineEvent",
    "PipelineHook",
    "PipelineContext",
    "PipelineResult",
    "PipelineExecutionMetadata",
    "LifecycleManager",
    "ModuleState",
    "ModuleStatus",
    "IntegrationConfig",
    "ModuleUnavailable",
    "is_module_available",
    "ValidationResult",
    "validate_pipeline_context",
    "validate_prediction_unchanged",
    "IntegrationContext",
    "CognitivePipeline",
    "IntegrationPlugin",
    "DefaultIntegrationPlugin",
]
