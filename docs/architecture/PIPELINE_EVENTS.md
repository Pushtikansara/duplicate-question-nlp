# Pipeline Events

## PipelineEvent Enum

The event system defines 19 events covering every stage boundary in the pipeline:

```python
class PipelineEvent(Enum):
    PIPELINE_STARTED        = "pipeline.started"
    BEFORE_PERCEPTION       = "before.perception"
    AFTER_PERCEPTION        = "after.perception"
    BEFORE_ROUTING          = "before.routing"
    AFTER_ROUTING           = "after.routing"
    BEFORE_MEMORY_READ      = "before.memory.read"
    AFTER_MEMORY_READ       = "after.memory.read"
    BEFORE_SEMANTIC         = "before.semantic"
    AFTER_SEMANTIC          = "after.semantic"
    BEFORE_REASONING        = "before.reasoning"
    AFTER_REASONING         = "after.reasoning"
    BEFORE_DEBATE           = "before.debate"
    AFTER_DEBATE            = "after.debate"
    BEFORE_DECISION         = "before.decision"
    AFTER_DECISION          = "after.decision"
    BEFORE_MEMORY_WRITE     = "before.memory.write"
    AFTER_MEMORY_WRITE      = "after.memory.write"
    PIPELINE_COMPLETED      = "pipeline.completed"
    PIPELINE_FAILED         = "pipeline.failed"
```

## PipelineHook Class

The hook system in `pipeline_hooks.py` implements a publish-subscribe pattern:

```python
class PipelineHook:
    def __init__(self):
        self._handlers: dict[PipelineEvent, list[Callable]] = {}

    def subscribe(self, event: PipelineEvent,
                  handler: Callable[[PipelineContext], None]) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def unsubscribe(self, event: PipelineEvent,
                    handler: Callable[[PipelineContext], None]) -> None:
        self._handlers.get(event, []).remove(handler)

    def publish(self, event: PipelineEvent, context: PipelineContext) -> None:
        for handler in self._handlers.get(event, []):
            try:
                handler(context)
            except Exception:
                logger.exception(f"Hook failed for {event.value}")
```

Hooks are synchronous by design. The pipeline waits for all handlers to complete before proceeding to the next module. This ensures metrics captures and log entries are complete before state transitions.

## How to Add Custom Event Handlers

```python
from _integration.pipeline_hooks import PipelineHook
from _integration.pipeline_events import PipelineEvent

def my_logging_hook(context):
    module = context.current_module
    print(f"[{module}] questions={context.question1!r} vs {context.question2!r}")

def my_metrics_hook(context):
    elapsed = time.perf_counter() - context.start_time
    metrics.record(f"pipeline.{context.current_module}", elapsed)

hook = PipelineHook()
hook.subscribe(PipelineEvent.AFTER_PERCEPTION, my_logging_hook)
hook.subscribe(PipelineEvent.AFTER_PERCEPTION, my_metrics_hook)

# Register with pipeline
pipeline = CognitivePipeline(hook=hook)
```

## Example: Logging Hook

```python
def logging_hook(context):
    module = context.events[-1].value if context.events else "unknown"
    state = "START" if module == "pipeline.started" else \
            "END" if "after" in module or "completed" in module or "failed" in module \
            else "PROCESS"
    print(f"[PIPELINE] {state:7s} | {module:25s} | "
          f"errors={len(context.errors)} | time={context.elapsed():.4f}s")
```

## Example: Metrics Collection Hook

```python
def metrics_collection_hook(context):
    import time
    elapsed = time.perf_counter() - context.start_time
    module = context.current_module
    metrics_counter.labels(module=module).observe(elapsed)

# Install
hook.subscribe(PipelineEvent.AFTER_PERCEPTION, metrics_collection_hook)
hook.subscribe(PipelineEvent.AFTER_ROUTING, metrics_collection_hook)
hook.subscribe(PipelineEvent.AFTER_MEMORY_READ, metrics_collection_hook)
hook.subscribe(PipelineEvent.AFTER_SEMANTIC, metrics_collection_hook)
hook.subscribe(PipelineEvent.AFTER_REASONING, metrics_collection_hook)
hook.subscribe(PipelineEvent.AFTER_DEBATE, metrics_collection_hook)
hook.subscribe(PipelineEvent.AFTER_DECISION, metrics_collection_hook)
```
