---
description: Generate comprehensive documentation for code.
---

# Documentation Generation Prompt

You are tasked with generating comprehensive documentation for the following code.

## Input

{{input}}

## Documentation Instructions

Generate thorough documentation following language-specific conventions:

- **Python**: Google-style docstrings (or NumPy/Sphinx depending on project convention)
- **JavaScript/TypeScript**: JSDoc annotations
- **Java**: Javadoc
- **Rust**: rustdoc
- **Go**: Go-style comments
- **Ruby**: YARD

## Documentation Sections

### 1. Overview

- **Module/Class/Function name**
- **Purpose**: What does this code do? Why does it exist? (1-2 paragraphs)
- **Context**: Where is this used in the application? What problem does it solve?
- **Dependencies**: What other components does it rely on?

### 2. API Reference

For each public function, method, or class:

**Functions/Methods**:

```python
def function_name(param1: type, param2: type = default) -> return_type:
```

- **Description**: What the function does
- **Parameters**:
  - `param1` (type): Description, constraints, default value
  - `param2` (type): Description, constraints, default value
- **Returns**: (type) Description of return value
- **Raises/Exceptions**:
  - `ValueError`: When and why raised
  - `TimeoutError`: When and why raised
- **Example**:

```python
# usage example showing all features
```

**Classes**:

```python
class ClassName:
```

- **Description**: What the class represents and its responsibility
- **Attributes**:
  - `attr1` (type): Description, default value, mutability
  - `attr2` (type): Description, default value, mutability
- **Methods**: (refer to method docstrings)
- **Example**:

```python
# instantiation and usage
```

### 3. Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| option_name | string | "default" | What this config controls |
| option_name | int | 60 | Timeout in seconds |

- How configuration is loaded (env vars, config files, CLI args)
- Configuration precedence and merging behavior
- Example configuration files

### 4. Usage Examples

Provide complete, runnable examples covering:

- **Basic usage**: minimal setup and common operations
- **Advanced usage**: complex scenarios with configuration
- **Error handling**: how to handle common errors and edge cases

Each example should:
- Be self-contained and copy-paste runnable
- Include imports and setup
- Demonstrate both success and error paths
- Follow best practices and idioms

### 5. Edge Cases

Document behavior under unusual conditions:

- **Empty/null input**: what happens and how to handle it
- **Boundary values**: minimum, maximum, and boundary behavior
- **Concurrent access**: thread safety, locking behavior
- **Error conditions**: network failures, timeouts, rate limits
- **Resource exhaustion**: memory limits, file descriptor limits

### 6. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Error message X | Missing dependency Y | Run `pip install Y` |
| Slow performance | Missing database index | Add index on column Z |
| Connection refused | Service not running | Start service with `systemctl start X` |

- Common error messages and their meanings
- Debugging techniques and tools
- How to enable verbose/debug logging
- Support contacts and escalation path

### 7. Changelog

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 2.0.0 | 2024-01-15 | Major refactor of API | @user |
| 1.1.0 | 2023-11-01 | Added new feature | @user |
| 1.0.0 | 2023-09-15 | Initial release | @user |

### 8. Related Resources

- **Source code**: link to repository
- **Issue tracker**: link to bug tracker
- **API docs**: link to full API reference
- **Tutorials**: link to guides and walkthroughs
- **Tests**: how to run the test suite

## Documentation Format

Structure the output as follows:

```markdown
# Module Name

## Overview
...

## API Reference
### `function_name(param1, param2)`
...

## Configuration
...

## Examples
...

## Edge Cases
...

## Troubleshooting
...

## Changelog
...
```
