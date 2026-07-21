# Integration Architecture

## Package Structure

```
_integration/
  cognitive_pipeline.py        # CognitivePipeline orchestrator
  pipeline_context.py          # PipelineContext dataclass
  pipeline_events.py           # PipelineEvent enum
  pipeline_hooks.py            # PipelineHook pub-sub system
  pipeline_result.py           # PipelineResult dataclass
  lifecycle.py                 # LifecycleManager, ModuleState
  integration_configuration.py # IntegrationConfig, defaults
  compatibility.py             # Backward compatibility layer
  validation.py                # Input/output validation utilities
  plugins/
    __init__.py                # Plugin registry
    integration_plugin.py      # IntegrationPlugin base class
    ...                        # Third-party plugin implementations
```

## Import Dependency Graph

```
                        +------------------+
                        | pipeline_context |
                        +--------+---------+
                                 |
              +------------------+------------------+
              |                  |                  |
              v                  v                  v
      +-------------+    +-------------+    +--------------+
      |pipeline_    |    |pipeline_    |    |pipeline_    |
      |events.py    |    |hooks.py     |    |result.py    |
      +------+------+    +------+------+    +------+------+
             |                   |                   |
             +-------------------+-------------------+
                                 |
                                 v
                         +---------------+
                         |  lifecycle   |
                         +-------+-------+
                                 |
                     +-----------+-----------+
                     |                       |
                     v                       v
            +---------------+       +-----------------+
            |validation     |       |compatibility    |
            +-------+-------+       +--------+--------+
                    |                        |
                    +----------+-------------+
                               |
                               v
                    +------------------+
                    |cognitive_pipeline|
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |integration_config|
                    +------------------+
                             |
                             v
                    +------------------+
                    | plugins/         |
                    | integration_     |
                    | plugin.py        |
                    +------------------+
```

Dependencies flow downward. No module in `_integration/` imports from outside the package except `plugins/` which imports the base class.

## Interface Contracts

Every module exposed to the pipeline conforms to `PipelineModule`:

```python
class PipelineModule(Protocol):
    name: str

    def initialize(self) -> None:
        """Allocate resources. Called once at pipeline startup."""

    def execute(self, context: PipelineContext) -> dict:
        """Process the context and return output dict. Must be thread-safe."""

    def shutdown(self) -> None:
        """Release resources. Called once at pipeline teardown."""
```

Modules may optionally declare:

```python
    requires: list[str] = []       # Module names that must complete first
    is_critical: bool = False      # Failure halts the pipeline
    timeout: float = 30.0          # Max execution time in seconds
```

## Plugin System

`IntegrationPlugin` in `plugins/integration_plugin.py`:

```python
class IntegrationPlugin(ABC):
    @abstractmethod
    def get_name(self) -> str: ...

    @abstractmethod
    def get_module(self) -> PipelineModule: ...

    @abstractmethod
    def get_config_schema(self) -> dict: ...

    def on_register(self, config: IntegrationConfig) -> None: ...
    def on_unregister(self) -> None: ...
```

Plugins register into the pipeline via:

```python
pipeline.register_plugin(MyCustomPlugin())
```

## Configuration (IntegrationConfig)

```python
@dataclass
class IntegrationConfig:
    enabled_modules: set[str] = field(
        default_factory=lambda: {
            "perception", "routing", "semantic", "reasoning", "decision"
        })
    critical_modules: dict[str, bool] = field(default_factory=dict)
    cms_enabled: bool = True
    debate_enabled: bool = False
    pipeline_timeout: float = 60.0
    hook_timeout: float = 5.0
    log_events: bool = True
    metrics_enabled: bool = False
    plugin_configs: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "IntegrationConfig": ...
    def to_dict(self) -> dict: ...
```
