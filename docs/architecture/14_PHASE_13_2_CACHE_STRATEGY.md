# Phase 13.2 — Cache Provider + Strategy Registry

**Status:** Implemented (Phase 13.4 will integrate these components into the
prediction pipeline entry points; they are usable independently now.)

**Scope:** Caching of deterministic orchestration inputs (primarily
Query Understanding results) and deterministic translation of a
`RoutingDecision` into an executable engine configuration.

---

## 1. Component overview

```
QueryAnalysis
    └── RoutingDecision (selected_strategy)
              │
              ▼
        StrategyRegistry          (strategy → StrategyDefinition)
              │                         configuration-driven
              ▼
        StrategySelector.resolve(routing_decision, request_params)
              │
              ▼
        EngineConfiguration (model, threshold, reflection, semantic validation)
              │
              ▼
        Existing ARES engine / InferenceDispatcher

Query Understanding request ──► QueryUnderstandingCacheKey ──► InMemoryCacheProvider
```

New files (all in `src/ares/orchestration/`):

| File | Responsibility |
|---|---|
| `cache.py` | `CacheEntry`, `CacheStats`, `InMemoryCacheProvider` (implements the Phase 13.1 `CacheProvider` protocol) |
| `cache_key.py` | `normalize_cache_text()`, `build_query_understanding_cache_key()` |
| `strategy_registry.py` | `StrategyDefinition`, `StrategyRegistry`, `StrategySelector`, `CAPABILITY_ATTRIBUTES` |
| `config_loader.py` | `load_orchestration_yaml()`, `build_strategy_registry()` |
| `configs/orchestration.yaml` | configuration-owned strategy → model mapping |

Exceptions added to the existing Phase 13 hierarchy (children of
`OrchestrationError`, no parallel hierarchy):

- `DuplicateStrategyError` (`DUPLICATE_STRATEGY`, 409)
- `InvalidStrategyConfigurationError` (`INVALID_STRATEGY_CONFIGURATION`, 500)

---

## 2. CacheProvider architecture

`ares.orchestration.interfaces.CacheProvider` (Phase 13.1) is the dependency
inversion point: orchestration code depends on the protocol, never on
`InMemoryCacheProvider`. A future Redis-backed provider implements the same
protocol.

`InMemoryCacheProvider` semantics:

| Aspect | Behavior |
|---|---|
| Eviction | Bounded LRU (`max_size > 0`); least recently used entry evicted on insert at capacity. `get()`/`set()` on an existing key refresh recency. |
| Capacity | `max_size <= 0` ⇒ unbounded cache (never evicts). Default `1000` (`DEFAULT_CACHE_MAX_ENTRIES`). |
| TTL | `ttl > 0` ⇒ entry expires after `ttl` seconds (`time.monotonic`). `ttl == 0` ⇒ no expiration. `ttl < 0` ⇒ `CacheError`. Default `300` (`DEFAULT_CACHE_TTL_SECONDS`). |
| Expiry | Expired entries removed lazily on `get()`/`contains()` and eagerly via `cleanup()`. Expirations are counted. |
| Thread safety | `threading.RLock` around every operation; safe under concurrent get/set/delete/clear/eviction. |
| Value safety | Only *cacheable* values accepted: `None`, primitives, dataclass instances, and containers of cacheable values. Anything else (locks, generators, modules, …) raises `CacheError`. Custom checkers via `value_checker=` constructor arg. |
| `None` values | Cacheable; use `contains()` to distinguish "stored None" from "absent". |

### API

```python
cache = InMemoryCacheProvider(max_size=1000, default_ttl=300)
cache.set(key, value, ttl=300)     # ttl required (protocol); ttl=0 keeps forever
value = cache.get(key)             # None on miss/expired; refreshes recency
cache.delete(key)                  # no-op when absent
cache.contains(key) -> bool        # live entry? does not touch recency/stats
cache.clear()
cache.cleanup() -> int             # removed expired entries
cache.stats() -> CacheStats        # hits, misses, evictions, expirations, size, max_size, hit_rate
len(cache) -> int
```

Observability: `CacheStats` exposes hit/miss/eviction/expiration counters —
one mechanism, no second metrics system. `EVENT_CACHE_HIT` / `EVENT_CACHE_MISS`
constants (Phase 13.1) remain available for pipeline integration in 13.4.

---

## 3. Cache key design

`build_query_understanding_cache_key(question1, question2, *, schema_version, analyzer_version)`
returns a SHA-256 hex digest (64 chars) of a canonical JSON payload:

```json
{"ns": "ares.orchestration.query_understanding",
 "schema_version": "1",
 "analyzer_version": "1.0.0",
 "q1": "<normalized>", "q2": "<normalized>"}
```

- **Normalization** (`normalize_cache_text`): NFKC Unicode normalization,
  `casefold()`, strip, collapse whitespace runs to a single space.
  Punctuation is intentionally preserved: Query Understanding computes
  punctuation features, so stripping punctuation from keys would create
  incorrect collisions.
- **Pair order is significant.** `QueryAnalysis` carries
  `original_question_1`/`original_question_2` and per-question metadata, so
  swapping the questions is a different input and produces a different key.
- **No `hash()`** (process-randomized), no timestamps, no random ids, no
  memory addresses. Same logical input ⇒ same key, across processes and
  machines.
- **Versioning — one mechanism:** `schema_version` (constant
  `CACHE_SCHEMA_VERSION` in `orchestration/constants.py`) changes when the
  key format or normalization semantics change; `analyzer_version` defaults
  to the live Query Understanding router contract version
  (`RouterEngine.version`) and changes when QU behavior changes. Either
  change automatically invalidates cached analyses — no manual flush needed.

---

## 4. StrategyRegistry

`StrategyDefinition` (frozen dataclass): `name`, `model_name` (required);
`threshold`, `use_reflection`, `use_semantic_validation`, `enabled`,
`timeout_ms`, `cache_enabled`, `priority`, `required_capabilities`.

`StrategyRegistry`:

| Method | Behavior |
|---|---|
| `register(strategy)` | duplicate name ⇒ `DuplicateStrategyError`; non-`StrategyDefinition` or empty name ⇒ `InvalidStrategyConfigurationError` |
| `resolve(name)` | unknown ⇒ `StrategyNotFoundError` |
| `contains(name)` / `list_strategies()` / `definitions()` | catalog access (registration order) |
| `validate(paths=None)` | cross-checks every strategy against the model registry; returns a list of issues (unknown model, not-ready model, capability mismatch) |
| `from_config(config)` | build from the `strategy_defaults` section of `configs/orchestration.yaml` |
| `with_defaults()` | Phase 13 default mapping (used when no config file exists) |

There is no hardcoded `STRATEGIES = {...}` source of truth — the registry is
the catalog, populated from configuration (`config_loader.build_strategy_registry`).

## 5. Strategy resolution

`StrategySelector.resolve(routing_decision, request_params, paths=None) -> EngineConfiguration`

- **Inputs:** a `RoutingDecision` (or its dict form) + optional `RequestParams`.
- **Deterministic:** pure function of inputs + registered definitions + model
  registry. No LLM, no randomness, no network.
- **Precedence:** user `RequestParams` (model/threshold/reflect) overrides the
  strategy definition; definition values override defaults
  (`DEFAULT_THRESHOLD`, reflection on).
- **Failures** (Phase 13 exceptions):
  - unknown strategy ⇒ `StrategyNotFoundError`
  - disabled strategy ⇒ `StrategyResolutionError`
  - missing/not-ready model ⇒ `ModelUnavailableError`
  - capability mismatch ⇒ `StrategyResolutionError`
  - malformed/absent routing decision ⇒ `StrategyResolutionError`
- **Capabilities:** `required_capabilities` keys map to the model registry's
  `ModelCapabilities` attributes via `CAPABILITY_ATTRIBUTES`
  (`batch`, `cross_encoding`, `embedding`, `gpu`, …). A model must satisfy all
  required capabilities of its strategy before execution.

## 6. Configuration (`configs/orchestration.yaml`)

Loaded directly by `config_loader` (the shared config loader's name list is
unchanged). Model names must match `ares.model_registry` display names:

```yaml
strategy_defaults:
  fast_lexical:
    model: "TF-IDF + Logistic Regression (Week 2)"
    reflection: false
    semantic_validation: false
    capabilities: ["batch"]
  cross_encoder:
    model: "Cross-Encoder-Quora (Trained)"
    capabilities: ["cross_encoding"]
  ensemble:
    model: "Semantic Ensemble"
  fallback:
    model: "Improved DistilBERT (Week 4)"
```

If the file is absent, `build_strategy_registry()` falls back to
`StrategyRegistry.with_defaults()` so deployments without a config file keep
working.

## 7. Extension points

- **New strategy:** add an entry to `strategy_defaults` (or `register()` a
  `StrategyDefinition` at startup) — no code changes required.
- **New model mapping:** edit `configs/orchestration.yaml` only.
- **Cache backend:** implement `CacheProvider` (e.g. Redis) and swap the
  implementation; orchestration code is unaffected.
- **Key/QU version change:** bump `CACHE_SCHEMA_VERSION` or the QU router
  version — cached entries invalidate automatically.

## 8. Failure behavior

All failures use the Phase 13 exception hierarchy with stable `error_code`
values. No request text, secrets, or keys are included in exception messages.
`CacheError` is reserved for cache contract violations (negative TTL,
uncacheable value) and is non-fatal by design (documented as loggable in the
pipeline spec).

## 9. Testing

`tests/unit/orchestration/`:

- `test_cache.py` — set/get/overwrite/delete/clear, TTL (expiry, `ttl==0`,
  `ttl<0`), LRU eviction and recency, bounded/unbounded capacity, stats,
  cacheable-value contract, protocol conformance, concurrent access,
  key-builder integration (hit/miss paths).
- `test_cache_key.py` — determinism, whitespace/case/Unicode normalization,
  punctuation semantics, reversed pairs, version invalidation, empty/long
  input, digest format.
- `test_strategy_registry.py` — registration/retrieval/enumeration, duplicate
  and unknown strategies, config parsing, defaults, `validate()`, selector
  resolution for every strategy, overrides, all failure modes, integration
  (`RoutingDecision` → registry → `EngineConfiguration`).
- `test_config_loader.py` — YAML loading, missing-file fallback, explicit
  dirs, broken configs.

## 10. Backward compatibility

- No changes to `ARES()`, the engine builder, `RouterEngine`, REST/gRPC/CLI,
  or multi-agent orchestration.
- `strategy.py` (agent-planning strategy resolution) is untouched.
- Existing Phase 13.1 tests pass unchanged; entry-point integration is Phase 13.4.
