---
description: Refactor code to improve structure, readability, and maintainability.
---

# Refactoring Prompt

You are tasked with refactoring the following code. Apply systematic software design principles to improve the codebase.

## Input

{{input}}

## Principles to Follow

- **Clean Architecture**: Separate concerns into layers (presentation, domain, data). Dependencies point inward.
- **SOLID**: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion.
- **DRY (Don't Repeat Yourself)**: Eliminate duplication through abstraction.
- **KISS (Keep It Simple, Stupid)**: Prefer simple solutions over clever ones.
- **YAGNI (You Ain't Gonna Need It)**: Do not add functionality until it is necessary.

## Refactoring Steps

### 1. Analyze the Current Code

- What is the purpose of this code?
- Identify all responsibilities of each module, class, and function.
- Map out dependencies and data flow.
- Note code smells and anti-patterns.
- Estimate the effort and risk for each change.

### 2. Identify Code Smells

| Smell | Description |
|-------|-------------|
| Bloaters | Long methods, large classes, long parameter lists, primitive obsession |
| Couplers | Feature envy, inappropriate intimacy, message chains, middle man |
| Object-Orientation Abusers | Switch/if-else chains, temporary field, refused bequest, alternative classes with different interfaces |
| Change Preventers | Divergent change, shotgun surgery, parallel inheritance hierarchies |
| Dispensables | Comments (used to explain bad code), duplicate code, dead code, speculative generality, lazy class, data class |

### 3. Apply Refactoring Techniques

- **Composing Methods**: Extract method, inline method, replace temp with query, introduce explaining variable, split loop, replace loop with pipeline.
- **Moving Features**: Move method, move field, extract class, inline class, hide delegate, remove middle man, introduce foreign method.
- **Organizing Data**: Self-encapsulate field, replace data value with object, replace array with object, duplicate observed data, change bidirectional association to unidirectional.
- **Simplifying Conditional**: Decompose conditional, consolidate conditional expression, replace nested conditional with guard clauses, introduce null object.
- **Simplifying Method Calls**: Rename method, add/remove parameter, separate query from modifier, parameterize method, replace parameter with explicit methods, introduce parameter object.

### 4. Design Patterns to Consider

- **Creational**: Factory, Abstract Factory, Builder, Singleton (use sparingly), Dependency Injection.
- **Structural**: Adapter, Facade, Proxy, Decorator, Composite, Bridge.
- **Behavioral**: Strategy, Observer, Command, State, Template Method, Visitor, Chain of Responsibility.

### 5. Refactoring Deliverable

For each change, provide:

```
### Refactoring: [Name]

- **Rationale**: Why this change improves the code
- **Before**:

\`\`\`language
// current code
\`\`\`

- **After**:

\`\`\`language
// refactored code
\`\`\`

- **Risk**: LOW / MEDIUM / HIGH
- **Testing Strategy**: How to verify correctness after refactoring
```

## Output Summary

- **Files modified**: list of files
- **Smells eliminated**: what was fixed
- **Metrics improved**: cyclomatic complexity, lines of code, coupling count, duplication percentage
- **Remaining concerns**: what was intentionally left unchanged and why
- **Migration guide**: steps to integrate the refactored code safely
