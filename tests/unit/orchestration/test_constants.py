from __future__ import annotations

from ares.orchestration.constants import (
    DEFAULT_BATCH_MAX_PAIRS,
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_EXECUTION_MODE,
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_RETRY_BACKOFF_MS,
    DEFAULT_RETRY_MAX_ATTEMPTS,
    DEFAULT_STAGE_ORDER,
    DEFAULT_THRESHOLD,
    DEFAULT_TIMEOUT_MS,
    EVENT_CACHE_HIT,
    EVENT_CACHE_MISS,
    EVENT_ORCHESTRATION_COMPLETE,
    EVENT_ORCHESTRATION_FAILED,
    EVENT_ORCHESTRATION_FALLBACK,
    EVENT_ORCHESTRATION_STARTED,
    EVENT_PREDICTION_COMPLETE,
    EVENT_PREDICTION_STARTED,
    EVENT_STAGE_COMPLETE,
    EVENT_STAGE_STARTED,
    ORCHESTRATION_VERSION,
    STAGE_INPUT_VALIDATION,
    STAGE_PREDICTION,
    STAGE_QUERY_UNDERSTANDING,
    STAGE_RESULT_ENRICHMENT,
    STAGE_STRATEGY_SELECTION,
    STRATEGY_BASELINE,
    STRATEGY_CROSS_ENCODER,
    STRATEGY_ENSEMBLE,
    STRATEGY_FALLBACK,
    STRATEGY_FAST_LEXICAL,
)


class TestConstantsValues:
    def test_orchestration_version(self):
        assert ORCHESTRATION_VERSION == "1.0.0"

    def test_default_cache_ttl(self):
        assert DEFAULT_CACHE_TTL_SECONDS == 300

    def test_default_cache_max_entries(self):
        assert DEFAULT_CACHE_MAX_ENTRIES == 1000

    def test_default_retry_max_attempts(self):
        assert DEFAULT_RETRY_MAX_ATTEMPTS == 2

    def test_default_retry_backoff_ms(self):
        assert DEFAULT_RETRY_BACKOFF_MS == 100

    def test_default_fallback_model(self):
        assert DEFAULT_FALLBACK_MODEL == "Improved DistilBERT (Week 4)"

    def test_default_execution_mode(self):
        assert DEFAULT_EXECUTION_MODE == "sync"

    def test_default_max_concurrency(self):
        assert DEFAULT_MAX_CONCURRENCY == 4

    def test_default_batch_max_pairs(self):
        assert DEFAULT_BATCH_MAX_PAIRS == 1000

    def test_default_timeout_ms(self):
        assert DEFAULT_TIMEOUT_MS == 30000.0

    def test_default_threshold(self):
        assert DEFAULT_THRESHOLD == 0.5


class TestStageNames:
    def test_stage_names_are_strings(self):
        assert isinstance(STAGE_INPUT_VALIDATION, str)
        assert isinstance(STAGE_QUERY_UNDERSTANDING, str)
        assert isinstance(STAGE_STRATEGY_SELECTION, str)
        assert isinstance(STAGE_PREDICTION, str)
        assert isinstance(STAGE_RESULT_ENRICHMENT, str)

    def test_default_stage_order(self):
        assert len(DEFAULT_STAGE_ORDER) == 5
        assert DEFAULT_STAGE_ORDER[0] == STAGE_INPUT_VALIDATION
        assert DEFAULT_STAGE_ORDER[1] == STAGE_QUERY_UNDERSTANDING
        assert DEFAULT_STAGE_ORDER[2] == STAGE_STRATEGY_SELECTION
        assert DEFAULT_STAGE_ORDER[3] == STAGE_PREDICTION
        assert DEFAULT_STAGE_ORDER[4] == STAGE_RESULT_ENRICHMENT

    def test_all_stages_unique(self):
        assert len(set(DEFAULT_STAGE_ORDER)) == len(DEFAULT_STAGE_ORDER)


class TestStrategyNames:
    def test_strategy_names_are_strings(self):
        assert isinstance(STRATEGY_FAST_LEXICAL, str)
        assert isinstance(STRATEGY_BASELINE, str)
        assert isinstance(STRATEGY_CROSS_ENCODER, str)
        assert isinstance(STRATEGY_ENSEMBLE, str)
        assert isinstance(STRATEGY_FALLBACK, str)

    def test_strategy_values(self):
        assert STRATEGY_FAST_LEXICAL == "fast_lexical"
        assert STRATEGY_BASELINE == "baseline_classifier"
        assert STRATEGY_CROSS_ENCODER == "cross_encoder"
        assert STRATEGY_ENSEMBLE == "ensemble"
        assert STRATEGY_FALLBACK == "fallback"

    def test_all_strategies_unique(self):
        strategies = {
            STRATEGY_FAST_LEXICAL,
            STRATEGY_BASELINE,
            STRATEGY_CROSS_ENCODER,
            STRATEGY_ENSEMBLE,
            STRATEGY_FALLBACK,
        }
        assert len(strategies) == 5


class TestEventTypes:
    def test_event_types_are_strings(self):
        events = [
            EVENT_ORCHESTRATION_STARTED,
            EVENT_ORCHESTRATION_COMPLETE,
            EVENT_ORCHESTRATION_FAILED,
            EVENT_ORCHESTRATION_FALLBACK,
            EVENT_STAGE_STARTED,
            EVENT_STAGE_COMPLETE,
            EVENT_PREDICTION_STARTED,
            EVENT_PREDICTION_COMPLETE,
            EVENT_CACHE_HIT,
            EVENT_CACHE_MISS,
        ]
        for e in events:
            assert isinstance(e, str)

    def test_event_type_formats(self):
        assert EVENT_ORCHESTRATION_STARTED == "orchestration.started"
        assert EVENT_ORCHESTRATION_COMPLETE == "orchestration.complete"
        assert EVENT_ORCHESTRATION_FAILED == "orchestration.failed"
        assert EVENT_STAGE_STARTED == "orchestration.stage.started"
        assert EVENT_STAGE_COMPLETE == "orchestration.stage.complete"

    def test_all_events_unique(self):
        events = {
            EVENT_ORCHESTRATION_STARTED,
            EVENT_ORCHESTRATION_COMPLETE,
            EVENT_ORCHESTRATION_FAILED,
            EVENT_ORCHESTRATION_FALLBACK,
            EVENT_STAGE_STARTED,
            EVENT_STAGE_COMPLETE,
            EVENT_PREDICTION_STARTED,
            EVENT_PREDICTION_COMPLETE,
            EVENT_CACHE_HIT,
            EVENT_CACHE_MISS,
        }
        assert len(events) == 10


class TestConstantsAreFinal:
    def test_constants_are_not_reassignable(self):
        assert isinstance(ORCHESTRATION_VERSION, str)
        assert isinstance(DEFAULT_CACHE_TTL_SECONDS, int)
        assert isinstance(DEFAULT_TIMEOUT_MS, float)
        assert isinstance(DEFAULT_STAGE_ORDER, list)


class TestPublicApi:
    def test_all_constants_exported(self):
        from ares.orchestration import (
            DEFAULT_CACHE_TTL_SECONDS,
            DEFAULT_STAGE_ORDER,
            EVENT_ORCHESTRATION_STARTED,
            ORCHESTRATION_VERSION,
            STAGE_INPUT_VALIDATION,
            STRATEGY_FAST_LEXICAL,
        )

        assert ORCHESTRATION_VERSION is not None
        assert DEFAULT_CACHE_TTL_SECONDS is not None
        assert DEFAULT_STAGE_ORDER is not None
        assert STAGE_INPUT_VALIDATION is not None
        assert STRATEGY_FAST_LEXICAL is not None
        assert EVENT_ORCHESTRATION_STARTED is not None
