---
name: langchain
description: Use when building LLM-powered applications with LangChain. Covers chains, agents, retrievers, memory, and tool integration.
---

# LangChain Skill

## Instructions

### Core Abstractions

1. **LLMs vs ChatModels** - LLMs take string input/output (`llm.invoke('text')`). ChatModels take message lists and return messages (`chat_model.invoke([HumanMessage('text')])`). Use ChatModels for conversational applications; they support system messages, function calling, and multi-turn context.

2. **Messages** - SystemMessage (sets behavior), HumanMessage (user input), AIMessage (model response), FunctionMessage (tool result), ToolMessage (tool response). Use `messages_from_dict` for serialization. Each message has `content` and optional `additional_kwargs`.

3. **Prompt Templates** - Use `ChatPromptTemplate.from_messages([...])` with `MessagesPlaceholder` for dynamic message injection. Use `PromptTemplate` for string templates. Templates support variable interpolation with `{variable_name}` syntax.

4. **Output Parsers** - `StrOutputParser` (default, returns string), `PydanticOutputParser` (structured Pydantic model), `JsonOutputParser` (JSON parsed), `CommaSeparatedListOutputParser`, `DatetimeOutputParser`. Use `.with_structured_output()` on ChatModels for native function-calling-based parsing.

5. **Runnable Interface** - Every component implements `invoke`, `batch`, `stream`, `astream`, `ainvoke`, `abatch`. Compose with pipe operator `|`. Example: `chain = prompt | model | output_parser`.

### Chains

1. **LCEL (LangChain Expression Language)** - Preferred way to build chains. Use pipe operator: `chain = prompt | model | parser`. Supports branching with `RunnableParallel`, `RunnablePassthrough`, and `itemgetter`. LCEL chains are automatically traced and streamable.

2. **RunnableParallel** - Execute multiple operations in parallel: `RunnableParallel({'summary': summary_chain, 'keywords': keywords_chain})`. Results are merged into single dict. Each sub-chain receives the same input.

3. **RunnablePassthrough** - Passes input unchanged. Use with `.assign()` to add fields: `RunnablePassthrough.assign(processed=lambda x: process(x))`. Useful for splitting and merging data flows.

4. **RunnableBranch** - Route between chains based on condition: `RunnableBranch((lambda x: len(x) > 100, long_chain), short_chain)`. Conditions are evaluated in order; first match wins.

5. **Legacy Chains** - Avoid `LLMChain`, `SimpleSequentialChain`, `SequentialChain` unless maintaining old code. Use LCEL instead. Legacy chains lack streaming, tracing, and parallel execution support.

### Agents

1. **Agent Executor** - Core agent runtime. Takes `agent` and `tools`. Loop: thought -> action -> observation -> thought... until final answer. Configurable with `max_iterations`, `early_stopping_method`, `handle_parsing_errors`.

2. **Tool Definition** - Create tools with `@tool` decorator on functions with docstrings and type hints. Tool name defaults to function name, description from docstring. Use `Tool.from_function` for more control. Tools should be single-purpose.

3. **Toolkits** - Bundled sets of related tools. `SQLDatabaseToolkit`, `GmailToolkit`, `GitHubToolkit`, `PlayWrightBrowserToolkit`. Each toolkit provides pre-built tools for interacting with that system.

4. **Agent Types** - `openai-functions` (best for function-calling models), `openai-tools` (tools parameter), `react-docstore` (for document stores), `self-ask-with-search` (for search-backed QA), `conversational-react-description` (for chat).

5. **Agent Lifecycle** - Create agent with `create_react_agent(llm, tools, prompt)` or `create_openai_functions_agent`. Pass to `AgentExecutor(agent=agent, tools=tools, verbose=True)`. Invoke with `agent_executor.invoke({'input': 'query'})`.

### Memory

1. **ConversationBufferMemory** - Stores entire message history. Simplest memory but grows unbounded. Use `return_messages=True` to get message objects. Memory key defaults to `history`.

2. **ConversationBufferWindowMemory** - Keeps last k turns of conversation. Fixed memory size. Set `k=5` for typical use. Drops oldest messages when limit exceeded.

3. **ConversationSummaryMemory** - Summarizes conversation after each turn. Stores summary instead of raw messages. More token-efficient for long conversations. Uses LLM to generate summaries.

4. **ConversationSummaryBufferMemory** - Hybrid: keeps recent messages raw, summarizes old messages. Trigger summarization when token count exceeds `max_token_limit`. Best balance of detail and efficiency.

5. **VectorStoreRetrieverMemory** - Stores memories as embeddings in a vector store. Retrieve relevant memories based on semantic similarity. Useful for long-running agents that need to recall specific facts.

6. **Memory Integration** - Inject memory into chains via `RunnableWithMessageHistory` in LCEL. Create `get_session_history` callable that returns `ChatMessageHistory`. Use `session_id` for multi-user persistence.

### Retrieval

1. **Vector Store Retrieval** - `vectorstore.as_retriever(search_type='similarity', search_kwargs={'k': 4})`. Supports `similarity` (cosine), `mmr` (diversity), `similarity_score_threshold` (filter by score).

2. **Ensemble Retrieval** - `EnsembleRetriever(retrievers=[bm25_retriever, vector_retriever], weights=[0.3, 0.7])`. Combines sparse (BM25) and dense retrieval for better coverage. Weighted reciprocal rank fusion.

3. **Contextual Compression** - `ContextualCompressionRetriever(base_compressor=LLMChainExtractor(), base_retriever=retriever)` Extracts only relevant parts of retrieved documents using LLM. Reduces context size.

4. **Multi-Query Retrieval** - Generate multiple query variations, retrieve for each, combine results. `from langchain.retrievers.multi_query import MultiQueryRetriever`. Improves recall by addressing phrasing variation.

5. **Parent Document Retriever** - Store document chunks, retrieve parent documents. `ParentDocumentRetriever(vectorstore=store, docstore=store, child_splitter=splitter)`. Ensures retrieved chunks have full context.

6. **Time-Weighted Retrieval** - Decay document relevance over time. Uses exponential decay: `score = similarity * (1 - decay_rate) ** hours_old`. Configure `decay_rate` and `time_weight`.

## Examples

### Basic LCEL Chain

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_template('Tell me a short joke about {topic}')
model = ChatOpenAI(model='gpt-4o-mini', temperature=0.7)
output_parser = StrOutputParser()

chain = prompt | model | output_parser
result = chain.invoke({'topic': 'programming'})
# 'Why do programmers prefer dark mode? Because light attracts bugs!'
```

### Agent with Tools

```python
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate

@tool
def search(query: str) -> str:
    """Search the web for current information."""
    return f'Search results for: {query}'

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression))

tools = [search, calculator]
prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are a helpful assistant with search and calculation abilities.'),
    ('human', '{input}'),
    ('placeholder', '{agent_scratchpad}'),
])
agent = create_openai_tools_agent(ChatOpenAI(model='gpt-4o'), tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

result = agent_executor.invoke({'input': 'What is the current population of Tokyo and what is 10% of it?'})
```

### Chain with Memory

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

store = {}

def get_session(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain = prompt | model | StrOutputParser()
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session,
    input_messages_key='input',
    history_messages_key='history',
)

result = chain_with_memory.invoke(
    {'input': 'Hi, my name is Alice'},
    config={'configurable': {'session_id': 'user_123'}},
)
```

## Best Practices

1. **Use LCEL** for all new chains; avoid legacy chain classes.
2. **Implement retry logic** with `try/except` around LLM calls; models can fail transiently.
3. **Set `max_iterations`** on agents (typically 5-15) to prevent infinite loops.
4. **Use `handle_parsing_errors=True`** in AgentExecutor to gracefully recover from malformed output.
5. **Validate tool inputs** with Pydantic models using `args_schema` parameter.
6. **Use `RunnableWithMessageHistory`** instead of manually managing memory in chains.
7. **Pin model versions** (e.g., `gpt-4o-2024-08-06`) for reproducible behavior.
8. **Enable tracing** with LangSmith via `LANGSMITH_TRACING=true` for debugging complex chains.
9. **Batch process** with `.batch()` for parallel invocation over multiple inputs.
10. **Stream responses** with `.stream()` for better user experience in interactive applications.

## Common Mistakes

1. **Using legacy chains** instead of LCEL, losing streaming and tracing capabilities.
2. **Not handling tool errors** causing agent to crash instead of retrying.
3. **Forgetting `agent_scratchpad`** placeholder in agent prompts, leading to missing intermediate steps.
4. **Memory overflow** from unbounded `ConversationBufferMemory` exhausting context window.
5. **Missing `get_session_history`** when using `RunnableWithMessageHistory`, causing memory corruption.
6. **Overly broad tool descriptions** causing agents to use wrong tools for tasks.
7. **Not setting `return_direct=True`** on tools that should return final answers directly.
8. **Ignoring token limits** and sending too much context in retrieval-based chains.
9. **Using `invoke` instead of `stream`** for real-time user-facing applications.
10. **Nesting agents** unnecessarily; prefer a single agent with comprehensive tools.

## Libraries

- `langchain-core` - Base abstractions (runnables, messages, tools, prompts)
- `langchain` - Community integrations, chains, agents, memory implementations
- `langchain-openai` - OpenAI model and embedding integrations
- `langchain-anthropic` - Anthropic Claude integration
- `langchain-community` - Third-party model and vector store integrations
- `langgraph` - Stateful, multi-step agent orchestration
- `langserve` - Deploy chains as REST API
- `langsmith` - Tracing, evaluation, and testing SDK
- `chromadb` - Default vector store for retrieval
- `tavily-python` - Web search API for agent tools

## Design Principles

1. **Runnable Interface** - Every component exposes the same invoke/batch/stream interface for composability.
2. **Composability First** - LCEL enables arbitrary chain topologies through pipe operator and RunnableParallel.
3. **Model Agnostic** - Same code works with OpenAI, Anthropic, local models, or any LLM provider.
4. **Progressive Disclosure** - Start with high-level defaults; drop to low-level controls as needed.
5. **Observability** - Every step is traceable and debuggable through LangSmith integration.
6. **Streaming by Default** - LCEL chains automatically support streaming of intermediate results.
7. **Fail Gracefully** - Agents should recover from errors, retry failed steps, and degrade gracefully.

## Coding Standards

1. **Import organization** - Group imports by source: langchain-core, langchain-community, then external.
2. **Type hints** - Use `Runnable`, `BaseMessage`, `Tool` type annotations for all function signatures.
3. **Tool definition** - Use `@tool` decorator with complete docstrings and type-annotated parameters.
4. **Prompt design** - Store prompts as module-level constants; use ChatPromptTemplate.from_messages.
5. **Configuration** - Pass configuration via `configurable` dict in `invoke`, not hardcoded in chain.
6. **Error handling** - Wrap agent executor calls in try/except; log errors with descriptive messages.
7. **Testing** - Mock LLM responses for unit tests; use `FakeListLLM` for deterministic agent testing.
8. **Logging** - Use `get_logger(__name__)` for structured logging; set verbose only in development.
9. **Secrets management** - Read API keys from environment variables; never hardcode credentials.
10. **Chain documentation** - Document input/output schemas for each chain using docstring descriptions.
