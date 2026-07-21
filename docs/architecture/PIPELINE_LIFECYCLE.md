# Pipeline Lifecycle Management

## ModuleState Enum

Each module in the pipeline transitions through a well-defined state machine. The `ModuleState` enum captures every valid state:

```
UNAVAILABLE  -->  AVAILABLE  -->  INITIALIZED  -->  RUNNING  -->  COMPLETED
                                                      |
                                                      +--> FAILED
                                                      |
                                                      +--> SKIPPED
```

| State | Meaning |
|---|---|
| `UNAVAILABLE` | Module not present or not registered |
| `AVAILABLE` | Module loaded, awaiting initialization |
| `INITIALIZED` | Module resources allocated (model loaded, connections open) |
| `RUNNING` | Module actively processing |
| `COMPLETED` | Module finished successfully |
| `FAILED` | Module raised an error during execution |
| `SKIPPED` | Module bypassed (configured off or preconditions not met) |

## LifecycleManager Class

The `LifecycleManager` in `lifecycle.py` orchestrates per-module state transitions. It is separate from the `CognitivePipeline` to enforce single responsibility.

```python
class LifecycleManager:
    def __init__(self, config: IntegrationConfig): ...

    def initialize(self, module_name: str) -> None: ...
    def start(self, module_name: str) -> None: ...
    def complete(self, module_name: str) -> None: ...
    def fail(self, module_name: str, error: Exception) -> None: ...
    def skip(self, module_name: str, reason: str) -> None: ...

    def get_state(self, module_name: str) -> ModuleState: ...
    def all_completed(self) -> bool: ...
    def has_failures(self) -> bool: ...
    def get_failures(self) -> dict[str, Exception]: ...
```

### State Transition Rules

1. `initialize()` requires current state `AVAILABLE`, transitions to `INITIALIZED`
2. `start()` requires `INITIALIZED`, transitions to `RUNNING`
3. `complete()` requires `RUNNING`, transitions to `COMPLETED`
4. `fail()` can be called from `RUNNING` or `INITIALIZED`, transitions to `FAILED`
5. `skip()` can be called from `AVAILABLE` or `INITIALIZED`, transitions to `SKIPPED`
6. Terminal states (`COMPLETED`, `FAILED`, `SKIPPED`) are irreversible

## Error Handling Per Module

Each module execution in the pipeline is wrapped:

```python
try:
    lifecycle.start(module_name)
    result = module.execute(context)
    context.set_output(module_name, result)
    lifecycle.complete(module_name)
except SkipModule as e:
    lifecycle.skip(module_name, str(e))
except Exception as e:
    lifecycle.fail(module_name, e)
    if config.critical_modules.get(module_name, False):
        raise PipelineCriticalError(module_name, e) from e
    context.add_error(module_name, e)
```

## Error Propagation Rules

| Condition | Behaviour |
|---|---|
| Module marked `critical` in config | Failure raises `PipelineCriticalError`, pipeline halts |
| Module not critical, failure occurs | Error recorded in context, pipeline continues to next module |
| Downstream module depends on failed module's output | Downstream receives `None` for that input, handles gracefully |
| CMS read fails | Context proceeds without historical data (optional path) |
| CMS write fails | Warning logged, prediction result still returned |
| All modules fail | Pipeline still produces a decision via fallback (raw similarity) |
