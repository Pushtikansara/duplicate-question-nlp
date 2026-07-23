# Phase 10 — Plugin Integration

## 1. Design Principle

Phase 10 does NOT modify the existing `ares.plugins` package. Instead, it extends the `PluginCapability` enum and provides new base classes that inherit from the existing `Plugin`.

## 2. New Plugin Types

```
ares.plugins.base.Plugin (existing, unchanged)
  │
  ├── AgentPlugin (NEW)          — plugin that provides an Agent implementation
  ├── ToolPlugin (NEW)           — plugin that provides a Tool implementation
  └── WorkflowPlugin (NEW)       — plugin that provides one or more WorkflowDefs
```

## 3. AgentPlugin

```python
class AgentPlugin(Plugin):                        # extends existing Plugin
    capabilities = {PluginCapability.AGENT}        # declares capability

    @abstractmethod
    def create_agent(self) -> Agent:
        """Factory method — returns an Agent instance."""
```

Discovery and loading integrate with the existing `PluginManager`:

```python
# In AgentLifecycleManager._discover_agent_plugins():
for plugin in plugin_manager.list(capability=PluginCapability.AGENT):
    agent = plugin.create_agent()
    self.register(agent.__class__, agent.metadata)
```

## 4. ToolPlugin

```python
class ToolPlugin(Plugin):
    capabilities = {PluginCapability.TOOL}

    @abstractmethod
    def create_tool(self) -> Tool:
        """Factory method — returns a Tool instance."""
```

## 5. WorkflowPlugin

```python
class WorkflowPlugin(Plugin):
    capabilities = {PluginCapability.WORKFLOW}

    @abstractmethod
    def register_workflows(self, engine: WorkflowEngine) -> None:
        """Register one or more workflow definitions with the engine."""
```

## 6. Example: Custom Agent Plugin

```python
class MyCustomAgentPlugin(AgentPlugin):
    metadata = PluginMetadata(
        name="my_agent",
        version="1.0.0",
        capabilities={PluginCapability.AGENT},
        # ... other metadata fields
    )

    def create_agent(self) -> Agent:
        return MyCustomAgent()

    def on_install(self, context: PluginContext) -> HookResult:
        logger.info("MyCustomAgent installed")
        return HookResult.CONTINUE

    def on_initialize(self, context: PluginContext) -> HookResult:
        # Register any tools this agent needs
        context.services.tool_registry.register(MyCustomTool())
        return HookResult.CONTINUE
```

## 7. Plugin Hook Extension Points

Existing hooks remain unchanged. New hooks are added to `HookPoint` enum:

```python
class HookPoint(Enum):
    # ... existing 17 hooks unchanged ...
    BEFORE_AGENT_EXECUTE = auto()    # NEW
    AFTER_AGENT_EXECUTE = auto()     # NEW
    BEFORE_TOOL_EXECUTE = auto()     # NEW
    AFTER_TOOL_EXECUTE = auto()      # NEW
    BEFORE_WORKFLOW_STEP = auto()    # NEW
    AFTER_WORKFLOW_STEP = auto()     # NEW
```

## 8. Backward Compatibility

| Existing Plugin Type | Phase 10 Impact |
|----------------------|-----------------|
| Cognitive pipeline plugins (before/after_perception, etc.) | **Unchanged** — pipeline is a tool now |
| Memory plugins | **Unchanged** — memory is a tool now |
| Reflection plugins | **Unchanged** — reflection is a tool now |
| Telemetry/Logging plugins | **Unchanged** — telemetry is a cross-cutting concern |
| Storage plugins | **Unchanged** — storage is a tool now |
