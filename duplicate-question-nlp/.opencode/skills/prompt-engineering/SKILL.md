---
name: prompt-engineering
description: Use when designing prompts for LLMs. Covers zero-shot, few-shot, chain-of-thought, structured outputs, and prompt optimization.
---

# Prompt Engineering Skill

## Instructions

### Fundamental Techniques

1. **Zero-Shot Prompting** - Ask the model to perform a task without examples. Format: `Classify the sentiment of this text as positive, negative, or neutral: {text}`. Works well for simple, well-defined tasks. Best when the task description is clear and unambiguous.

2. **Few-Shot Prompting** - Provide 2-5 examples of input-output pairs before the target query. Examples establish the pattern, format, and reasoning style. Select diverse examples covering edge cases. Order examples from simple to complex.

3. **System Prompts** - Set the model's behavior, persona, and constraints. Place at the start of the conversation. Define role, tone, output format, and guardrails. Example: `You are an expert data scientist. Explain concepts at a graduate level. Use technical terminology appropriately.`

4. **Instruction Placement** - Put instructions at the beginning or end of the prompt. Middle instructions are more likely to be ignored by the model. Use separators (---, ###) to distinguish instructions from input. Prioritize the most important instruction.

5. **Role Prompting** - Assign a specific persona: `You are a world-class mathematician specializing in number theory.` Role prompts activate domain-specific knowledge and adjust the model's reasoning and vocabulary. Effective for specialized tasks.

### Advanced Techniques

1. **Chain-of-Thought (CoT)** - Encourage step-by-step reasoning before the final answer. Add `Let's think step by step` or provide a reasoned example. Improves performance on arithmetic, logical, and multi-step reasoning tasks by 10-30%.

2. **Tree-of-Thought (ToT)** - Explore multiple reasoning branches simultaneously. Evaluate each branch and backtrack when necessary. Prompt: `Consider three different approaches to solve this problem. For each, explain the reasoning steps and evaluate which is most likely correct.`

3. **Least-to-Most Prompting** - Break a complex problem into simpler subproblems. Solve each subproblem sequentially, using previous answers as context. Effective for tasks requiring multiple steps or synthesis of information.

4. **Self-Consistency** - Generate multiple reasoning paths (k=3-10) with higher temperature (0.5-0.8). Take majority vote or average for final answer. Improves reliability by 5-15% on reasoning tasks. Cost: k times more tokens.

5. **ReAct (Reasoning + Acting)** - Interleave reasoning traces with actions (tool calls, searches). Format: `Thought: ... Action: ... Observation: ... Thought: ... Final Answer:`. Enables LLMs to use external tools and incorporate real-time information.

6. **Structured Output Requests** - Request specific output formats: JSON, XML, markdown, code blocks. Use `You must respond in valid JSON format with keys: "answer", "confidence", "explanation".` Combine with schema description and examples.

### Output Formatting

1. **JSON Mode** - Explicitly request JSON: `Respond with a JSON object containing "result" and "reasoning" fields.` Use the model's native JSON mode when available (OpenAI: `response_format={'type': 'json_object'}`). Validate output with json.loads().

2. **Schema Definition** - Provide Pydantic-style schema in the prompt: `The output must match: {"name": str, "age": int, "skills": list[str], "metadata": {"experience": int, "level": str}}`. Strict schema enforcement improves parsability.

3. **Tag-Based Formatting** - Use XML-style tags: `<thinking>...</thinking><answer>...</answer>` or markdown headings. Tags help the model segment its response and make parsing more reliable. Use self-closing tags for boolean/category outputs.

4. **Constrained Generation** - Limit output tokens with `max_tokens`, use logit bias to restrict vocabulary, or use grammar-based sampling (guidance library, lmql). Essential when output must conform to a formal grammar.

### Prompt Optimization

1. **Iterative Refinement** - Start simple, test, analyze failures, refine. Common refinements: add examples for edge cases, clarify ambiguous instructions, reorder examples, adjust task framing. Track changes in a versioned prompt file.

2. **A/B Testing** - Compare prompt variants on a fixed evaluation set. Measure accuracy, format compliance, token usage, and latency. Statistical significance requires 100+ test examples per variant. Use the same model version for fair comparison.

3. **Template Variables** - Parametrize prompts: `Classify the sentiment of this {domain} text: {text}`. Load domain from config. Enables multi-domain systems without duplicating prompts. Document expected variable types and formats.

4. **Negative Instructions** - State what NOT to do: `Do not include explanations. Do not use markdown formatting.` More effective than omitting the instruction. Place negative instructions after positive ones. Limit to 2-3 negative instructions.

5. **Token Budget Management** - Allocate prompt tokens wisely: 70% for instructions and examples, 30% for input. Shorter prompts are faster and cheaper but may lack necessary context. Monitor token usage per request with tiktoken.

### Domain-Specific Techniques

1. **Code Generation** - Specify language, framework, coding standards, and test requirements. Use: `Write Python 3.11 code using type hints. Include docstrings. Add unit tests with pytest.` Provide input/output examples. Request error handling.

2. **Data Extraction** - Define schema precisely: `Extract all person entities: name, age, occupation, location. If a field is not found, use null.` Use few-shot examples with edge cases (missing fields, multiple entities). Validate extracted data programmatically.

3. **Summarization** - Specify length, style, audience, and key points to include. Use: `Summarize in 3 bullet points for a technical audience. Focus on methodology and results.` Control length with output constraints. Extract vs abstractive summarization.

4. **Creative Writing** - Provide genre, tone, style references, character descriptions, plot constraints. Use: `Write in the style of Ernest Hemingway. Use short sentences. Focus on action rather than description.` Set creativity with temperature (0.7-0.9 for creative, 0.1-0.3 for factual).

### Safety and Robustness

1. **Input Validation** - Sanitize user input before inserting into prompts. Strip control characters, limit length, filter known injection patterns. Never directly concatenate user input without escaping.

2. **Prompt Injection Defense** - Use delimiters around user input: `User message: """{input}"""`. Instruct the model to ignore instructions within user input. Implement a separate guard prompt for safety classification.

3. **Output Validation** - Validate output format before presenting to user. Check for harmful content with a content safety classifier. Implement fallback responses for failed validation. Log all output validation failures.

4. **Rate Limiting** - Implement per-user and per-API-key rate limiting. Monitor token consumption. Queue requests when limits are approached. Communicate rate limits to users transparently.

## Examples

### Chain-of-Thought for Math

```python
prompt = '''
Solve this math problem step by step.

Problem: A store sells apples for $0.50 each and oranges for $0.75 each.
If a customer buys 3 apples and 2 oranges, what is the total cost?

Step 1: Calculate cost of apples: 3 * $0.50 = $1.50
Step 2: Calculate cost of oranges: 2 * $0.75 = $1.50
Step 3: Add costs together: $1.50 + $1.50 = $3.00
Answer: $3.00

Now solve this problem:
At a cinema, adult tickets cost $12 and child tickets cost $8.
A family of 2 adults and 3 children go to the cinema.
What is the total cost?

Step 1:'''
```

### Structured JSON Output

```python
messages = [
    {'role': 'system', 'content': '''
You extract structured data from text. Respond in JSON format:
{
  "entities": [{"name": str, "type": "person|org|location", "mentions": int}],
  "summary": {"key_points": [str], "sentiment": "positive|negative|neutral"}
}
'''},
    {'role': 'user', 'content': text},
]

response = client.chat.completions.create(
    model='gpt-4o',
    messages=messages,
    response_format={'type': 'json_object'},
    temperature=0.1,
)
```

### Few-Shot Classification

```python
prompt = '''
Classify email intent as: complaint, inquiry, feedback, or spam.

Email: "My order hasn't arrived after 2 weeks. This is unacceptable."
Intent: complaint

Email: "What are your business hours during holidays?"
Intent: inquiry

Email: "Great service! The staff was very helpful."
Intent: feedback

Email: "Congratulations! You won a free iPhone. Click here to claim."
Intent: spam

Email: "I need to return a defective product. Can you provide the return label?"
Intent:'''
```

## Best Practices

1. **Be specific and explicit** rather than vague; state exactly what you want the model to do.
2. **Use examples over descriptions** for complex tasks; 3 good examples outperform a detailed description.
3. **Temperature of 0** for factual tasks (classification, extraction, coding); 0.7-0.9 for creative tasks.
4. **Test with edge cases**: empty input, adversarial input, ambiguous queries, multi-language input.
5. **Version control prompts** alongside code using .prompt or .txt files with Git.
6. **Monitor token usage** per prompt and per session to control costs.
7. **Use system prompts for fixed behavior**, user prompts for variable input.
8. **Provide negative examples** of what constitutes a bad output for complex formatting tasks.
9. **Separate instructions from data** with clear delimiters to reduce injection risk.
10. **One prompt per task** - don't overload a single prompt with multiple complex instructions.

## Common Mistakes

1. **Over-specifying output format** with too many constraints leading to format failures.
2. **Assuming the model remembers information** from the beginning of a long prompt.
3. **Using complex instructions** when simple ones suffice; prompts should be as simple as possible.
4. **Not providing enough examples** for nuanced tasks, causing inconsistent output.
5. **Forgetting to handle edge cases** in few-shot examples; model learns from all examples equally.
6. **Using temperature > 0 for deterministic tasks** causing unpredictable output variations.
7. **Prompt leakage** - user input containing instructions that override the system prompt.
8. **Inconsistent formatting** between examples causing the model to produce mixed formats.
9. **Chain-of-thought for simple tasks** wasting tokens when direct answering would suffice.
10. **Not testing with the exact model version** as prompt effectiveness varies between models.

## Libraries

- `langchain-core` - Prompt templates and composable prompt building
- `guidance` - Grammar-based constrained generation
- `outlines` - Structured generation with regex and Pydantic schemas
- `lmql` - SQL-like constrained language model queries
- `jinja2` - Advanced template engine for complex prompt composition
- `tiktoken` - Token counting and budget management
- `prompttools` - Prompt experimentation and evaluation
- `spacy` - Input text preprocessing and sanitization
- `guardrails` - Output validation and safety checking
- `text-generation-inference` - Constrained generation in production

## Design Principles

1. **Clarity Over Cleverness** - Prompts should be direct and unambiguous; avoid prompting tricks unless necessary.
2. **Progressive Disclosure** - Start with minimal instructions; add complexity only when baseline fails.
3. **Garbage In, Garbage Out** - Prompt quality directly determines output quality; invest in prompt design.
4. **Constraint-Driven Design** - Define the output space first, then craft instructions that constrain the model to it.
5. **Separation of Concerns** - System prompt for persona and constraints, user prompt for task and input.
6. **Idempotency** - Same prompt + same input should produce the same output (use temperature=0).
7. **Testability** - Prompts should be evaluable against a ground truth dataset with quantitative metrics.

## Coding Standards

1. **Templating** - Use `PromptTemplate` or `ChatPromptTemplate` instead of f-string formatting for prompts.
2. **Variable naming** - Use descriptive snake_case variable names in templates: `{user_input}`, `{domain}`.
3. **Versioning** - Store prompts as `.prompt` or `.txt` files with semantic versioning in filenames.
4. **Configuration** - Load prompt templates from files, not hardcoded in Python strings.
5. **Testing** - Unit test prompts with known inputs and expected outputs; integration test with live model.
6. **Logging** - Log full prompt and response pairs for debugging and quality analysis.
7. **Documentation** - Document each prompt's purpose, expected input format, output schema, and known limitations.
8. **Temperature handling** - Pass temperature as an explicit parameter, not hardcoded in prompt text.
9. **Fallback behavior** - Define fallback responses for when the model fails to produce valid output.
10. **Monitoring** - Track prompt success rate, average tokens per prompt, and format compliance rate.
