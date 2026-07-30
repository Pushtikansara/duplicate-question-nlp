from __future__ import annotations

from typing import Final

ORCHESTRATION_VERSION: Final[str] = "1.0.0"

DEFAULT_CACHE_TTL_SECONDS: Final[int] = 300
DEFAULT_CACHE_MAX_ENTRIES: Final[int] = 1000
DEFAULT_RETRY_MAX_ATTEMPTS: Final[int] = 2
DEFAULT_RETRY_BACKOFF_MS: Final[int] = 100
DEFAULT_FALLBACK_MODEL: Final[str] = "Improved DistilBERT (Week 4)"
DEFAULT_EXECUTION_MODE: Final[str] = "sync"
DEFAULT_MAX_CONCURRENCY: Final[int] = 4
DEFAULT_BATCH_MAX_PAIRS: Final[int] = 1000
DEFAULT_TIMEOUT_MS: Final[float] = 30000.0
DEFAULT_THRESHOLD: Final[float] = 0.5

STAGE_INPUT_VALIDATION: Final[str] = "InputValidationStage"
STAGE_QUERY_UNDERSTANDING: Final[str] = "QueryUnderstandingStage"
STAGE_STRATEGY_SELECTION: Final[str] = "StrategySelectionStage"
STAGE_PREDICTION: Final[str] = "PredictionStage"
STAGE_RESULT_ENRICHMENT: Final[str] = "ResultEnrichmentStage"

DEFAULT_STAGE_ORDER: Final[list[str]] = [
    STAGE_INPUT_VALIDATION,
    STAGE_QUERY_UNDERSTANDING,
    STAGE_STRATEGY_SELECTION,
    STAGE_PREDICTION,
    STAGE_RESULT_ENRICHMENT,
]

STRATEGY_FAST_LEXICAL: Final[str] = "fast_lexical"
STRATEGY_BASELINE: Final[str] = "baseline_classifier"
STRATEGY_CROSS_ENCODER: Final[str] = "cross_encoder"
STRATEGY_ENSEMBLE: Final[str] = "ensemble"
STRATEGY_FALLBACK: Final[str] = "fallback"

EVENT_ORCHESTRATION_STARTED: Final[str] = "orchestration.started"
EVENT_ORCHESTRATION_COMPLETE: Final[str] = "orchestration.complete"
EVENT_ORCHESTRATION_FAILED: Final[str] = "orchestration.failed"
EVENT_ORCHESTRATION_FALLBACK: Final[str] = "orchestration.fallback"
EVENT_STAGE_STARTED: Final[str] = "orchestration.stage.started"
EVENT_STAGE_COMPLETE: Final[str] = "orchestration.stage.complete"
EVENT_PREDICTION_STARTED: Final[str] = "orchestration.prediction.started"
EVENT_PREDICTION_COMPLETE: Final[str] = "orchestration.prediction.complete"
EVENT_CACHE_HIT: Final[str] = "orchestration.cache.hit"
EVENT_CACHE_MISS: Final[str] = "orchestration.cache.miss"
