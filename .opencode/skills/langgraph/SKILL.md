---
name: langgraph
description: Use when building stateful, multi-step LLM workflows with LangGraph. Covers graphs, nodes, edges, state management, and persistence.
---

# LangGraph Skill

## Instructions

### Core Concepts

1. **StateGraph** - Main graph class. Define with `StateGraph(State)` where `State` is a TypedDict or Pydantic model. The graph manages state transitions through nodes and edges. State is the single source of truth passed between nodes.

2. **Nodes** - Python functions or runnable objects that take state and return state updates. Added with `graph.add_node('node_name', function)`. Each node should operate on specific state keys and return a dict of updates. Nodes can be async.

3. **Edges** - Define flow between nodes. `graph.add_edge('node_a', 'node_b')` for unconditional transitions. `graph.add_conditional_edges('node_a', router_function, {True: 'node_b', False: 'node_c'})` for branching.

4. **Entry and End** - `graph.set_entry_point('start_node')` defines where execution begins. `graph.set_finish_point('end_node')` or `END` constant defines termination. Multiple finish points are supported.

5. **State Management** - State is a dict-like object. Each node can read all state fields and write to specific fields using returned dict. State is passed by value; mutations within a node are not visible outside.

### State Design

1. **TypedDict State** - Define with `class AgentState(TypedDict): messages: Annotated[list, add_messages]`. The `Annotated` type with `add_messages` reducer tells LangGraph how to merge state updates (append for lists, replace for scalars).

2. **Reducers** - Custom reducers define how state updates are merged. Built-in reducers: `add_messages` (appends to message list), `operator.add` (for counters/lists). Write custom reducers: `def reducer(existing, update): return updated_value`.

3. **State Keys** - Use descriptive state keys: `messages` (conversation history), `context` (retrieved documents), `intermediate_steps` (agent actions). Keep state flat; avoid deeply nested structures.

4. **Default Values** - Set default values in TypedDict with `total=False` for optional fields. Initialize state with defaults before compilation.

### Graph Execution

1. **Compilation** - `app = graph.compile()` creates the executable application. Pass `checkpointer` for persistence. The compiled app has `invoke`, `stream`, `astream` methods.

2. **Invocation** - `app.invoke({'messages': [HumanMessage('hello')]}, config={'configurable': {'thread_id': 'abc'}})`. The thread_id links to persisted state for multi-turn conversations.

3. **Streaming** - `app.stream(input, config, stream_mode='values')` yields state at each step. Stream modes: 'values' (full state after each node), 'updates' (only state diffs), 'messages' (LLM token streaming).

4. **Interruption** - Set `interrupt_before=['node_name']` in compile. Execution pauses before that node. Resume with `app.invoke(None, config)` to continue. Used for human-in-the-loop approval flows.

5. **Event Callbacks** - Register callbacks with `CallbackManager` for monitoring: node start/end, on_chain_start, on_tool_start. Use LangSmith for production tracing.

### Agent Patterns

1. **Tool-calling Agent** - Node `call_model` generates tool calls. Node `call_tool` executes tools. Conditional edge routes based on whether model output has tool calls. Set `interrupt_before=['call_tool']` for human approval.

2. **ReAct Agent** - Loop of Thought -> Action -> Observation. Implement as `agent` node (LLM call) and `tools` node (tool execution). Conditional edge back to agent if more actions needed, or to end.

3. **Plan-and-Execute** - Separate planning phase generates a sequence of steps. Each step is executed by a separate sub-graph or tool. Planner node generates plan; executor node runs each step. Re-plan if execution fails.

4. **Reflection Agent** - Generate initial output, then critique and refine. Two nodes: `generator` produces output, `reflection` evaluates and provides feedback. Loop until quality threshold or max iterations.

5. **Multi-Agent Supervisor** - Supervisor node routes tasks to specialist agent nodes. Each specialist reports results back. Supervisor decides next action or final answer. Implemented as conditional edges from supervisor.

### Persistence

1. **Checkpointers** - Store state between runs. `MemorySaver` for in-memory (development), `SqliteSaver` for file-based, `PostgresSaver` for production. Pass to `graph.compile(checkpointer=checkpointer)`.

2. **Thread Management** - Each conversation thread has a unique `thread_id`. State is automatically restored when resuming a thread. List threads with `checkpointer.list()`.

3. **State History** - Access previous states with `app.get_state(config)`. Roll back with `app.update_state(config, values)`. Each state snapshot is stored with a `parent_ts` for lineage tracking.

4. **Human-in-the-Loop** - Interrupt graph, let human review/modify state, resume. Use `interrupt_before` and `Command(resume=user_input)`. Human can modify tool call arguments or provide direct answers.

### Subgraphs

1. **Graph Composition** - Define a subgraph with its own state, compile it, and add it as a node in the parent graph. Subgraph state is scoped; parent sees only the returned state dict.

2. **State Mapping** - Use `input` and `output` mapping when adding subgraph nodes: `parent.add_node('sub', subgraph, input=map_in, output=map_out)`. Maps transform between parent and subgraph state schemas.

3. **Parallel Subgraphs** - Use `RunnableParallel` with multiple subgraph nodes for concurrent execution. Each subgraph processes independently. Parent waits for all to complete.

## Examples

### Basic ReAct Agent

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def call_model(state: AgentState) -> dict:
    response = model.invoke(state['messages'])
    return {'messages': [response]}

def should_continue(state: AgentState) -> Literal['tools', END]:
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return 'tools'
    return END

graph = StateGraph(AgentState)
graph.add_node('agent', call_model)
graph.add_node('tools', tool_executor)
graph.set_entry_point('agent')
graph.add_conditional_edges('agent', should_continue)
graph.add_edge('tools', 'agent')

app = graph.compile(checkpointer=MemorySaver())
result = app.invoke(
    {'messages': [HumanMessage('what is the weather in SF?')]},
    config={'configurable': {'thread_id': '1'}}
)
```

### Human-in-the-Loop Approval

```python
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=['call_tool'],
)

config = {'configurable': {'thread_id': 'human_loop_1'}}
events = app.stream({'messages': [HumanMessage('send an email')]}, config)

for event in events:
    if event.get('__interrupt__'):
        user_approved = input('Approve tool call? (y/n): ')
        if user_approved.lower() == 'y':
            app.invoke(None, config)  # resume
```

### Plan-and-Execute Pattern

```python
def planner(state: AgentState) -> dict:
    plan = planner_chain.invoke({'task': state['messages'][-1].content})
    return {'plan': plan, 'current_step': 0}

def executor(state: AgentState) -> dict:
    step = state['plan'][state['current_step']]
    result = exec_chain.invoke({'step': step, 'context': state.get('results', [])})
    return {'results': state.get('results', []) + [result], 'current_step': state['current_step'] + 1}

def plan_router(state: AgentState) -> Literal['executor', 'final']:
    return 'final' if state['current_step'] >= len(state['plan']) else 'executor'

graph.add_conditional_edges('executor', plan_router)
```

## Best Practices

1. **Design state schema first** before adding nodes and edges.
2. **Use `add_messages` reducer** for message lists to maintain full conversation history.
3. **Set `interrupt_before`** for any node that performs irreversible actions (payments, sending emails).
4. **Implement timeout handling** with `recursion_limit` (default 25) to prevent infinite loops.
5. **Use async nodes** (`async def`) for IO-bound operations like API calls and database queries.
6. **Test graphs independently** by calling node functions directly with mock state.
7. **Use LangSmith tracing** for debugging complex graph flows with 10+ nodes.
8. **Version your checkpoints** schemas to handle state migration across graph versions.
9. **Limit state size** by summarizing or pruning old messages in long-running conversations.
10. **Document edge conditions** clearly in conditional routing functions with Literal return types.

## Common Mistakes

1. **Not using reducers** for state keys, causing state to be replaced instead of merged.
2. **Exceeding recursion limit** without implementing proper termination conditions in edges.
3. **Modifying state in place** instead of returning updates; LangGraph uses immutable state passing.
4. **Forgetting `checkpointer`** when resuming interrupted graphs, leading to state loss.
5. **Complex conditional edges** without `Literal` return type annotations, causing type errors.
6. **Overlapping thread_ids** when using shared checkpointers, mixing state across conversations.
7. **Using sync nodes for async operations** blocking the event loop in concurrent graphs.
8. **Not handling edge failures** in tool nodes; errors should return error messages, not crash.
9. **Deeply nested state** that is hard to serialize, debug, and maintain.
10. **Missing `END` case** in conditional routers causing graph to spin forever.

## Libraries

- `langgraph` - Core graph framework for stateful LLM applications
- `langgraph-checkpoint` - Persistence backends (MemorySaver, SqliteSaver, PostgresSaver)
- `langgraph-sdk` - API for deploying LangGraph apps as microservices
- `langchain-core` - Base runnables, messages, and tool abstractions
- `langchain-openai` - OpenAI model integration
- `langsmith` - Tracing, evaluation, and debugging
- `langserve` - REST API deployment for graphs
- `pydantic` - State schema validation and serialization
- `asyncpg` - PostgreSQL async driver for production checkpointing
- `redis` - Caching and distributed state management

## Design Principles

1. **State-Centric** - State is the single source of truth; everything else is derived from it.
2. **Explicit Flow** - Edges explicitly define all possible paths; no implicit routing.
3. **Deterministic Execution** - Given the same state and inputs, the graph produces the same output.
4. **Inspectability** - Every state transition is recorded and replayable for debugging.
5. **Separation of Concerns** - Each node does one thing (think, act, observe, transform).
6. **Failure Isolation** - A failing node does not crash the graph; errors are captured in state.
7. **Composable** - Subgraphs can be combined arbitrarily to build complex workflows.

## Coding Standards

1. **State definition** - Use `TypedDict` with `Annotated` and reducers for mergeable fields.
2. **Node functions** - Accept `state: AgentState` and return `dict` of state updates.
3. **Conditional routers** - Return `Literal['destination_a', 'destination_b']` type annotations.
4. **Graph construction** - Use builder pattern: `StateGraph -> add_node -> add_edge -> set_entry_point -> compile`.
5. **Configuration** - Use `configurable` dict with `thread_id` as required key.
6. **Error handling** - Wrap node logic in try/except; return error strings in state on failure.
7. **Testing** - Unit test each node function independently with mock state objects.
8. **Logging** - Log node entry/exit and state size at each step for debugging.
9. **Serialization** - Ensure all state values are JSON-serializable for checkpointing.
10. **Documentation** - Include a state schema diagram and edge flow chart for complex graphs.
