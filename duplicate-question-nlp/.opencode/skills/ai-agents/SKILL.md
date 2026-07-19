---
name: ai-agents
description: Use when building AI agents and agentic systems. Covers tool use, planning, memory, multi-agent systems, and agent architectures.
---

# AI Agents Skill

## Instructions

### Agent Fundamentals

1. **Agent Definition** - An AI agent is an LLM-powered system that perceives its environment, makes decisions, and takes actions to achieve goals. Core components: model (decision-making), tools (action space), memory (state), planning (strategy), and execution loop.

2. **Agent Loop** - The standard ReAct loop: Observe (receive input and state) -> Think (decide what to do) -> Act (call a tool or generate response) -> Observe (tool result) -> Repeat until goal achieved or max iterations. Each cycle is one step.

3. **Tool-Using Agents** - The LLM generates structured tool calls (function name + arguments). Tools are executed externally. Results are fed back as observations. The LLM decides when to call tools and when to respond directly.

4. **Planning Agents** - Agents decompose tasks into sub-tasks, create execution plans, and execute step by step. Plans can be static (all steps planned upfront) or dynamic (plan updated based on intermediate results). Plan quality depends on the model's reasoning ability.

5. **Reflexion Agents** - Self-evaluation loop: execute task, evaluate output, store feedback in memory, re-attempt based on feedback. The agent maintains a running log of attempts and reflections. Improves through iterative self-correction.

### Tool Design

1. **Tool Interface** - Each tool has: name (unique, descriptive), description (what it does, when to use it), parameters (JSON schema with types and descriptions), return type, and error handling. The tool description is critical for correct routing.

2. **Tool Granularity** - Tools should be single-purpose and composable. A calculator tool does one thing. A `search_knowledge_base` tool should not also summarize results. Combine multiple tool calls in sequence for complex tasks.

3. **Parameter Schemas** - Use Pydantic models for tool arguments. Mark optional parameters explicitly. Provide examples in parameter descriptions. Avoid complex nested schemas that are hard for LLMs to generate correctly.

4. **Error Handling** - Tools should never crash the agent. Catch exceptions, return descriptive error messages as observations. Include recovery suggestions: `Failed to connect to database. The server may be down. Try again in a few seconds.`

5. **Idempotent Tools** - Design tools to be safely callable multiple times. Read operations are naturally idempotent. Write operations should use idempotency keys or be designed to handle duplicates gracefully.

### Memory Systems

1. **Short-Term Memory** - The conversation context within the current session. Limited by the model's context window (4k-200k tokens). Managed automatically by the agent framework. Include only immediately relevant information.

2. **Long-Term Memory** - Persistent storage across sessions. Stores facts about the user, past interactions, learned preferences, and completed tasks. Implemented as a vector database with semantic search for retrieval.

3. **Episodic Memory** - Records of past agent runs: actions taken, results, and reflections. Retrievable for experience-based learning. Use structured format: `{episode_id, goal, steps, outcome, reflection, timestamp}`.

4. **Working Memory** - Temporary scratchpad for the current task. Stores intermediate results, partial plans, and reasoning traces. Managed as part of the agent state. Clear working memory between tasks to avoid context contamination.

5. **Memory Retrieval** - Retrieve relevant memories before each agent step. Use embedding similarity to find relevant past experiences. Apply recency, relevance, and importance scoring. Limit retrieved memories to ~5 items to stay within context window.

### Planning Systems

1. **Task Decomposition** - Break goals into sub-tasks using LLM: `Given the goal X, list the sub-tasks required in order`. Each sub-task should be atomic (one tool call) and testable. Decomposition quality improves with chain-of-thought.

2. **Dynamic Re-planning** - After each sub-task, evaluate progress. If stuck (same error repeated, no progress after N steps), pause execution, analyze the failure, and generate a new plan. Re-planning should reference the original goal.

3. **Plan Representation** - Store plans as structured data: `{steps: [{action, expected_outcome, dependencies, status}], goal, current_step}`. Mark steps as pending, in_progress, completed, failed, or blocked. Update status after each step.

4. **Contingency Planning** - For critical steps, define backup plans: `If search returns no results, try rephrasing the query. If still no results, ask the user for clarification.` Contingencies prevent agent deadlock.

5. **Plan Validation** - Before executing a plan, validate: Are all tools available for planned actions? Are action sequences logically ordered? Are there unnecessary steps? Invalid plans should be rejected with explanation.

### Multi-Agent Systems

1. **Agent Roles** - Specialized agents with distinct responsibilities. Examples: Researcher (information gathering), Coder (implementation), Reviewer (quality checking), Coordinator (task routing). Each agent has a specific system prompt and tool set.

2. **Communication** - Agents communicate through structured messages. Define message schemas: `{from, to, type (request, response, update, error), content, metadata}`. Use a shared message bus or direct routing through a coordinator.

3. **Orchestration** - Topologies: Supervisor (single coordinator assigns tasks), Peer-to-peer (agents communicate directly), Pipeline (serial handoff), Debate (agents discuss and converge). Choose based on task complexity and agent count.

4. **Consensus Mechanisms** - When agents disagree, use voting, deliberation, or delegation to a superior agent. For factual disagreements, use external tools to verify. For subjective disagreements, the supervisor makes the final call.

5. **Agent Termination** - Define clear termination conditions: goal achieved, maximum iterations exceeded, user interrupt, fatal error, agent explicitly requests termination. Log termination reason for debugging.

### Agent Evaluation

1. **Success Rate** - Binary metric: did the agent achieve the stated goal? Measure over a test set of tasks. Account for partial success with graded scoring (0-1 scale per task).

2. **Efficiency Metrics** - Steps taken, tokens consumed, wall-clock time, tool call count, error rate. Efficient agents minimize all of these while maintaining success rate. Compare to optimal human performance when available.

3. **Robustness Testing** - Test agents on: ambiguous instructions, missing information, tool failures, adversarial inputs, out-of-distribution tasks, long-running tasks. Document failure modes and implement guards.

4. **Safety Evaluation** - Does the agent refuse harmful requests? Does it operate within permissions? Are there side effects from tool calls? Does it respect user privacy? Implement automated safety testing before deployment.

5. **Cost Analysis** - Track per-task cost: API calls (LLM + tools), token consumption (input + output per call), storage costs. Optimize for cost by: shorter prompts, fewer steps, cheaper models for simple tasks, caching.

## Examples

### Simple Tool-Using Agent

```python
import json
from openai import OpenAI

def search_web(query: str) -> str:
    return f'Results for {query}: ...'

def calculate(expr: str) -> str:
    return str(eval(expr))

tools = [
    {'type': 'function', 'function': {
        'name': 'search_web',
        'description': 'Search the web for current information',
        'parameters': {'type': 'object', 'properties': {
            'query': {'type': 'string', 'description': 'The search query'}
        }, 'required': ['query']}
    }},
    {'type': 'function', 'function': {
        'name': 'calculate',
        'description': 'Evaluate a mathematical expression',
        'parameters': {'type': 'object', 'properties': {
            'expression': {'type': 'string', 'description': 'Math expression'}
        }, 'required': ['expression']}
    }}
]

available_tools = {'search_web': search_web, 'calculate': calculate}

messages = [{'role': 'system', 'content': 'You are a helpful assistant with web search and calculation abilities.'}]
messages.append({'role': 'user', 'content': 'What was the GDP of Japan in 2023, and what is 10% of that?'})

for _ in range(5):
    response = client.chat.completions.create(model='gpt-4o', messages=messages, tools=tools)
    msg = response.choices[0].message
    messages.append(msg)
    if not msg.tool_calls:
        break
    for tc in msg.tool_calls:
        fn = json.loads(tc.function.arguments)
        result = available_tools[tc.function.name](**fn)
        messages.append({'role': 'tool', 'tool_call_id': tc.id, 'content': result})
```

### Multi-Agent Supervisor

```python
class SupervisorAgent:
    def __init__(self):
        self.agents = {
            'researcher': ResearchAgent(tools=[search, fetch_page]),
            'analyst': AnalysisAgent(tools=[calculate, visualize]),
            'writer': WritingAgent(tools=[format, proofread]),
        }

    def run(self, task: str) -> str:
        plan = self.create_plan(task)
        results = {}
        for step in plan:
            agent = self.agents[step['agent']]
            result = agent.execute(step['instruction'], context=results)
            results[step['output_key']] = result
        return self.synthesize(results)
```

### Agent with Reflexion

```python
class ReflexionAgent:
    def __init__(self, model, tools, max_attempts=3):
        self.model = model
        self.tools = tools
        self.max_attempts = max_attempts
        self.memory = []

    def run(self, task: str) -> str:
        for attempt in range(self.max_attempts):
            result = self.execute_with_context(task, self.memory)
            evaluation = self.evaluate(task, result)
            if evaluation['success']:
                return result['output']
            self.memory.append({
                'attempt': attempt,
                'task': task,
                'result': result,
                'evaluation': evaluation,
                'reflection': evaluation['feedback'],
            })
        return self.memory[-1]['result']['output']
```

## Best Practices

1. **Set explicit max iterations** (5-15) to prevent infinite loops and runaway costs.
2. **Validate tool call syntax** before execution; malformed calls should return error, not crash.
3. **Log every agent step** including raw LLM output, tool calls, tool results, and timestamps.
4. **Implement human-in-the-loop** for any irreversible action (payments, deletions, external mutations).
5. **Use structured tool outputs** (JSON) rather than free text for easier parsing by subsequent steps.
6. **Cache tool results** for idempotent operations to reduce latency and cost.
7. **Test agents with systematic prompt injection** to verify safety boundaries.
8. **Monitor agent drift** over time as underlying LLMs are updated; re-evaluate monthly.
9. **Provide agent context** of recent history (last 3-5 steps) to maintain coherence without filling context window.
10. **Implement fallback behavior** for every expected failure mode: tool unavailable, output parsing fails, model refuses.

## Common Mistakes

1. **Vague tool descriptions** causing the agent to use inappropriate tools for tasks.
2. **Infinite loops** from no max iteration limit or missing termination conditions.
3. **Ignoring tool errors** and continuing with incorrect information from failed calls.
4. **Context overflow** from storing all history without summarization or pruning.
5. **Overly complex tools** that do too much, making it hard for the agent to use them correctly.
6. **Not handling model refusal** gracefully; model may refuse to use tools or refuse tasks.
7. **Mixing agent state across sessions** due to improper session isolation in memory.
8. **Hardcoded tool sequences** when agent should be deciding actions dynamically.
9. **No recovery strategy** when a step fails; agent should attempt alternatives, not crash.
10. **Excessive planning overhead** spending more tokens on planning than execution for simple tasks.

## Libraries

- `langchain` - Agent framework with tool integration and memory management
- `langgraph` - Stateful agent orchestration with graphs and persistence
- `crewai` - Multi-agent collaboration framework
- `autogen` - Microsoft's multi-agent conversation framework
- `semantic-kernel` - Microsoft's agent SDK with planning capabilities
- `pydantic` - Tool parameter schema validation
- `guidance` - Constrained generation for reliable tool call formatting
- `tiktoken` - Token counting for context window management
- `redis` - Persistent memory and state storage
- `weaviate` / `chromadb` - Vector memory for long-term storage

## Design Principles

1. **Tool-Centric Design** - The agent's capabilities are defined entirely by its tools; invest in tool quality.
2. **Fail Fast, Recover Gracefully** - Detect failures early and attempt recovery; never silently produce wrong output.
3. **Separation of Concerns** - Planning, execution, and evaluation are distinct phases managed independently.
4. **Stateless Tools, Stateful Agent** - Tools are pure functions; all state is managed by the agent's memory system.
5. **Progressive Autonomy** - Start with more human oversight; increase autonomy as reliability improves.
6. **Observable by Default** - Every agent action is logged and explainable for debugging and auditing.
7. **Cost-Benefit Proportionality** - Use expensive reasoning steps only when simple approaches are insufficient.

## Coding Standards

1. **Tool definition** - Use `@tool` decorator or Pydantic `BaseTool` subclasses with complete docstrings.
2. **Agent state** - Define state as a TypedDict with explicit schema and default values.
3. **Step logging** - Log each step as `{step_number, agent, action, input, output, duration, tokens}`.
4. **Error handling** - Wrap all tool executions in try/except; return structured error objects.
5. **Configuration** - Load agent config (model, tools, max_iterations, temperature) from environment or config file.
6. **Testing** - Unit test tools independently; integration test agent with mock LLM responses.
7. **Memory management** - Implement `summarize()` and `prune()` methods on memory for context management.
8. **Type safety** - Use Pydantic models for tool inputs and agent state for validation.
9. **Documentation** - Document each agent's purpose, tool set, memory strategy, and known limitations.
10. **Monitoring** - Track success rate, average steps, average cost, error rate, and user satisfaction score.
