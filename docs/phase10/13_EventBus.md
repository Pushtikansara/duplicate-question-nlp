# Phase 10 — Event Bus

## 1. Design Principle

The existing `EventBus` in `ares.plugins.hooks` serves plugin-to-plugin communication. Phase 10 adds a **global EventBus** for system-wide events with typed event classes, async delivery, and OpenTelemetry integration.

## 2. Architecture

```
┌────────────────────────────────────────────────────┐
│  Global EventBus (ares.eventbus.bus.EventBus)       │
│                                                     │
│  Subscribers register with channel + handler        │
│  Publishers emit to channel                         │
│  Event is dispatched to all subscribers             │
│                                                     │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Telemetry  │  │   Audit    │  │  Metrics     │  │
│  │ Subscriber │  │ Subscriber │  │  Subscriber  │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Agent      │  │ Workflow   │  │  Custom      │  │
│  │ Subscriber │  │ Subscriber │  │  Subscriber  │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
└────────────────────────────────────────────────────┘
```

## 3. EventBus API

```python
class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[EventHandler]] = {}

    def subscribe(
        self,
        channel: str,
        handler: Callable[[Event], Any],
        filters: EventFilter | None = None,
    ) -> Subscription:
        """Subscribe to a channel. Returns Subscription (for unsubscribe)."""

    def unsubscribe(self, subscription: Subscription) -> None:
        """Remove a subscription."""

    async def emit(self, channel: str, event: Event) -> None:
        """Emit event to all subscribers of the channel."""

    def emit_sync(self, channel: str, event: Event) -> None:
        """Synchronous emit for non-async contexts."""

    def get_subscriber_count(self, channel: str) -> int:
        """Return number of subscribers for a channel."""
```

## 4. Event Types

```python
@dataclass
class Event:
    id: str                          # UUID
    timestamp: datetime
    channel: str
    trace_id: str
    source: str                      # agent_id / tool_id / workflow_id
    payload: dict[str, Any]

# Concrete event subclasses:

@dataclass
class AgentEvent(Event):
    channel: "agent"
    agent_id: str
    event_type: AgentEventType       # INVOKED | COMPLETED | FAILED | PAUSED | RESUMED
    input: Any | None = None
    output: Any | None = None
    processing_time_ms: float = 0.0

@dataclass
class ToolEvent(Event):
    channel: "tool"
    tool_id: str
    event_type: ToolEventType        # INVOKED | COMPLETED | FAILED | DENIED
    agent_id: str
    input: Any | None = None
    output: Any | None = None
    processing_time_ms: float = 0.0

@dataclass
class WorkflowEvent(Event):
    channel: "workflow"
    workflow_id: str
    event_type: WorkflowEventType    # STARTED | STEP_COMPLETED | COMPLETED | FAILED
    step_id: str | None = None
    result: Any | None = None

@dataclass
class MemoryEvent(Event):
    channel: "memory"
    memory_type: str
    event_type: MemoryEventType      # WRITTEN | READ | SEARCHED | CONSOLIDATED
    agent_id: str
    summary: str

@dataclass
class SystemEvent(Event):
    channel: "system"
    event_type: SystemEventType      # STARTUP | SHUTDOWN | ERROR | CONFIG_CHANGE
    message: str
```

## 5. Channel Taxonomy

| Channel | Event Types | Typical Subscribers |
|---------|-------------|---------------------|
| `agent` | INVOKED, COMPLETED, FAILED, PAUSED, RESUMED | Telemetry, Audit, Metrics, Scheduler |
| `tool` | INVOKED, COMPLETED, FAILED, DENIED | Audit, Metrics, Security |
| `workflow` | STARTED, STEP_COMPLETED, COMPLETED, FAILED | Telemetry, AgentCoordinator |
| `memory` | WRITTEN, READ, SEARCHED, CONSOLIDATED | Audit, Telemetry, Agents |
| `system` | STARTUP, SHUTDOWN, ERROR, CONFIG_CHANGE | All subscribers, Admin |

## 6. Integration with Existing Plugin EventBus

```python
# In ares.eventbus.bus — bridges to existing Plugin EventBus:
from ares.plugins.hooks import EventBus as PluginEventBus

class GlobalEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self._plugin_bus = PluginEventBus()

    def bridge_to_plugins(self) -> None:
        """Forward plugin events to global bus and vice versa."""
        # Plugin hooks → global events
        self._plugin_bus.subscribe("*", self._on_plugin_event)
```

## 7. Telemetry Integration

Every event carries `trace_id` (OpenTelemetry trace context):

```python
class TelemetrySubscriber:
    async def on_agent_event(self, event: AgentEvent) -> None:
        with tracer.start_as_current_span(
            f"agent.{event.event_type.value}",
            context=trace_context_from_id(event.trace_id),
        ) as span:
            span.set_attribute("agent.id", event.agent_id)
            span.set_attribute("processing_time_ms", event.processing_time_ms)
            span.set_status(Status.OK if event.event_type != AgentEventType.FAILED else Status.ERROR)
```
