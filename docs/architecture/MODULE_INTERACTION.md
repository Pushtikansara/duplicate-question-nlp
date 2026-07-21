# Module Interaction

## How CognitivePipeline Calls Each Module

The pipeline follows a sequential execution model. Each module implements a standard interface:

```python
class PipelineModule(Protocol):
    name: str
    def execute(self, context: PipelineContext) -> dict: ...
    def initialize(self) -> None: ...
    def shutdown(self) -> None: ...
```

The pipeline calls `module.execute(context)` and stores the returned dict in the context under `module.name`.

```python
for module in self.modules:
    if lifecycle.get_state(module.name) in (ModuleState.FAILED, ModuleState.SKIPPED):
        continue
    self._fire(BEFORE_MODULE.format(module.name), context)
    output = self._run_module(module, context)
    if output is not None:
        context.set_output(module.name, output)
    self._fire(AFTER_MODULE.format(module.name), context)
```

## Data Flow Between Modules

```
+-----------+         +---------+         +----------+
|Perception |-------->|  Router |-------->|  Memory  |
|           |  tokens |         |  route  |  (Read)  |
| features  |  norms  |  strat  |  score  |          |
+-----------+         +---------+         +----+-----+
                                                |
                                                v
+----------+         +-----------+         +----------+
| Decision |<--------| Reasoning |<--------| Semantic |
|          | verdict |            | rules   |          |
|  explain |  conf   |  resolved |  scores |  embeds  |
+----------+         +-----------+         +----------+
     |
     v
+----------+
|  Memory  |
|  (Write) |
+----------+
```

Each module's output dict becomes part of `PipelineContext.outputs`. Subsequent modules read what they need:

- **Perception** writes `tokens`, `features`, `normalized_text`
- **Router** writes `complexity_score`, `selected_strategy`, `model_name`
- **Memory** writes `historical_context`, `similar_pairs` (or empty dict on miss)
- **Semantic** writes `embeddings`, `similarity_matrix`, `semantic_score`
- **Reasoning** writes `rules_applied`, `confidence_adjustment`, `resolved_verdict`
- **Debate** writes `agent_votes`, `consensus_verdict`, `debate_log`
- **Decision** writes `final_verdict`, `confidence`, `explainability`

## PipelineContext: Shared Immutable Data Carrier

`PipelineContext` is the single object passed through the entire pipeline. It is designed to be append-only:

```python
@dataclass(frozen=True)
class PipelineContext:
    question1: str
    question2: str
    metadata: dict
    outputs: dict[str, dict] = field(default_factory=dict)
    errors: dict[str, Exception] = field(default_factory=dict)
    events: list[PipelineEvent] = field(default_factory=list)
    start_time: float = field(default_factory=time.perf_counter)

    def set_output(self, module_name: str, data: dict) -> None:
        object.__setattr__(self, 'outputs',
            {**self.outputs, module_name: data})

    def add_error(self, module_name: str, error: Exception) -> None:
        object.__setattr__(self, 'errors',
            {**self.errors, module_name: error})

    def get_output(self, module_name: str) -> dict | None:
        return self.outputs.get(module_name)
```

The frozen dataclass with `object.__setattr__` enforces append-only semantics. No module can overwrite another module's output.

## How Outputs Become Inputs

Modules declare their input dependencies via annotations or configuration:

```python
class SemanticModule:
    requires = ['perception', 'routing']

    def execute(self, context: PipelineContext) -> dict:
        features = context.get_output('perception')
        strategy = context.get_output('routing')['selected_strategy']
        # ...
```

The pipeline validates dependencies before execution:

```python
def _validate_dependencies(self, module: PipelineModule) -> None:
    for dep in module.requires:
        state = self.lifecycle.get_state(dep)
        if state != ModuleState.COMPLETED:
            logger.warning(f"Module {module.name} depends on {dep} "
                           f"which is in state {state}")
```
