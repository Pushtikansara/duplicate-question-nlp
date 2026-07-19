---
description: Explain code, concepts, or architecture in detail.
---

# Code Explanation Prompt

You are tasked with providing a thorough explanation of the following code, concept, or architecture.

## Input

{{input}}

## Explanation Structure

### 1. Purpose and Context

- What does this code/system do at a high level?
- Why does it exist? What problem does it solve?
- How does it fit into the larger system?
- Who are the primary consumers (users, other systems, developers)?
- What are the boundaries and scope of this component?

### 2. How It Works: Step by Step

Walk through the execution flow or architecture in logical steps:

**Control Flow**:
1. Entry point and initialization
2. Input processing and validation
3. Core logic or computation
4. Interaction with dependencies (databases, APIs, file system)
5. Output generation or side effects
6. Error handling and cleanup

**For each step**:
- What is happening at this stage?
- Why is it done this way?
- What data is flowing through?
- What decisions or branches exist?
- What could go wrong here?

### 3. Key Design Decisions

- Why was this particular approach chosen over alternatives?
- What tradeoffs were made (simplicity vs performance, flexibility vs safety)?
- What constraints influenced the design (time, team skills, legacy system)?
- Are there any notable patterns or idioms being used?

### 4. Data Flow

- What are the main data structures used and why?
- How does data enter, transform, and exit the system?
- Where is data persisted, cached, or discarded?
- What is the data format (JSON, Protobuf, Parquet, etc.)?

### 5. Dependencies and Interactions

**Internal Dependencies**:
- What other modules, classes, or functions does this code rely on?
- What depends on this code?

**External Dependencies**:
- Third-party libraries and their versions
- External services and APIs
- Infrastructure (databases, message queues, caches)

**Interaction patterns**:
- Synchronous vs asynchronous calls
- Event-driven vs request-response
- Polling vs webhooks
- Streaming vs batch processing

### 6. Edge Cases and Error Handling

- What happens when input is empty, null, malformed, or out of range?
- How are network failures, database timeouts, and service outages handled?
- What happens under high load or resource exhaustion?
- How are concurrent access and race conditions handled?
- What are the failure modes and their impact?

### 7. Tradeoffs and Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| Current implementation | [pros] | [cons] |
| Alternative A | [pros] | [cons] |
| Alternative B | [pros] | [cons] |

- Under what conditions would a different approach be better?
- What would need to change for this to be improved?

### 8. Usage Examples

**Basic usage**:

```language
# minimal working example
```

**Common patterns**:

```language
# typical usage patterns
```

**Advanced usage**:

```language
# edge cases or non-standard usage
```

### 9. Related Resources

- Relevant documentation
- Related code files or modules
- RFCs, ADRs, or design documents
- External references (specifications, standards, articles)
- Tests that exercise this code

## Summary

- **What it does**: one-sentence summary
- **Why it matters**: the value it provides
- **Key takeaway**: the most important thing to understand about this code
