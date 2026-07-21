from duplicate_question_app._evaluation.ablation_engine import AblationEngine
from duplicate_question_app._evaluation.benchmark_result import (
    AblationResult,
    BenchmarkResult,
    ClassificationMetrics,
    ModuleSpecificMetrics,
    PerModuleMetrics,
)
from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner
from duplicate_question_app._evaluation.benchmark_suite import BenchmarkSuite
from duplicate_question_app._evaluation.calibration_metrics import (
    compute_brier_score,
    compute_confidence_histogram,
    compute_ece,
    compute_log_loss,
    compute_mce,
    compute_reliability_diagram,
)
from duplicate_question_app._evaluation.configuration import AblationConfig, BenchmarkConfig, EvaluationConfig
from duplicate_question_app._evaluation.debate_metrics import compute_debate_metrics
from duplicate_question_app._evaluation.error_analysis import (
    ErrorCategory,
    categorize_error,
    classify_hardness,
    generate_error_report,
    mine_hard_examples,
)
from duplicate_question_app._evaluation.error_analyzer import ErrorAnalyzer
from duplicate_question_app._evaluation.evaluation_engine import EvaluationEngine
from duplicate_question_app._evaluation.evaluator import Evaluator
from duplicate_question_app._evaluation.explainability_metrics import (
    compute_debate_completeness,
    compute_evidence_completeness,
    compute_explainability_score,
    compute_memory_usage,
    compute_reasoning_completeness,
)
from duplicate_question_app._evaluation.latency_profiler import LatencyProfiler, LatencySnapshot
from duplicate_question_app._evaluation.memory_metrics import compute_memory_metrics
from duplicate_question_app._evaluation.memory_profiler import MemoryProfiler, MemorySnapshot, estimate_object_size

# Re-export from existing modules for convenience
from duplicate_question_app._evaluation.metrics import (
    EvaluationMetrics,
    HardExample,
    compare_models,
    evaluate_model,
    find_hard_examples,
    generate_evaluation_report,
    generate_model_comparison_plots,
    plot_calibration_curve,
    plot_confusion_matrix,
    plot_error_analysis,
    plot_pr_curve,
    plot_prediction_distribution,
    plot_roc_curve,
)
from duplicate_question_app._evaluation.plugins import DefaultEvaluationPlugin, EvaluationPlugin
from duplicate_question_app._evaluation.reasoning_metrics import compute_reasoning_metrics
from duplicate_question_app._evaluation.report_generator import ReportGenerator
from duplicate_question_app._evaluation.routing_metrics import compute_routing_metrics
from duplicate_question_app._evaluation.visualization import (
    plot_ablation_comparison,
    plot_agent_agreement_heatmap,
    plot_latency_breakdown,
    plot_module_contribution,
    plot_routing_distribution,
)

__all__ = [
    # Config
    "EvaluationConfig",
    "BenchmarkConfig",
    "AblationConfig",
    # Results
    "BenchmarkResult",
    "AblationResult",
    "PerModuleMetrics",
    "ClassificationMetrics",
    "ModuleSpecificMetrics",
    # Profilers
    "LatencyProfiler",
    "LatencySnapshot",
    "MemoryProfiler",
    "MemorySnapshot",
    "estimate_object_size",
    # Calibration
    "compute_ece",
    "compute_mce",
    "compute_brier_score",
    "compute_log_loss",
    "compute_reliability_diagram",
    "compute_confidence_histogram",
    # Analysis
    "ErrorAnalyzer",
    "ErrorCategory",
    "categorize_error",
    "classify_hardness",
    "mine_hard_examples",
    "generate_error_report",
    # Explainability
    "compute_reasoning_completeness",
    "compute_evidence_completeness",
    "compute_debate_completeness",
    "compute_memory_usage",
    "compute_explainability_score",
    # Module metrics
    "compute_routing_metrics",
    "compute_reasoning_metrics",
    "compute_debate_metrics",
    "compute_memory_metrics",
    # Core
    "Evaluator",
    "BenchmarkRunner",
    "BenchmarkSuite",
    "AblationEngine",
    "ReportGenerator",
    "EvaluationEngine",
    # Visualization
    "plot_latency_breakdown",
    "plot_module_contribution",
    "plot_ablation_comparison",
    "plot_routing_distribution",
    "plot_agent_agreement_heatmap",
    # Re-exports
    "EvaluationMetrics",
    "HardExample",
    "evaluate_model",
    "find_hard_examples",
    "compare_models",
    "generate_evaluation_report",
    "generate_model_comparison_plots",
    "plot_confusion_matrix",
    "plot_roc_curve",
    "plot_pr_curve",
    "plot_calibration_curve",
    "plot_prediction_distribution",
    "plot_error_analysis",
    # Plugins
    "EvaluationPlugin",
    "DefaultEvaluationPlugin",
]
