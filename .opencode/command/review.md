---
description: Review code for quality, correctness, security, performance, and adherence to best practices.
---

# Code Review Prompt

You are tasked with performing a thorough code review on the following code. Analyze every aspect and provide actionable feedback.

## Input

{{input}}

## Review Instructions

Analyze the code across the following dimensions. For each issue found, assign a severity rating.

### Severity Ratings

| Severity | Definition |
|----------|------------|
| CRITICAL | Causes data loss, security breach, or complete system failure. Must fix before merge. |
| HIGH     | Causes incorrect behavior, major performance degradation, or significant maintainability problem. Should fix before merge. |
| MEDIUM   | Causes minor incorrect behavior, moderate performance impact, or code quality concern. Should fix soon. |
| LOW      | Cosmetic issue, minor style inconsistency, or non-critical improvement. Fix when convenient. |
| INFO     | Suggestion or observation. Not an issue but worth noting. |

## 1. Correctness

- Does the code correctly implement the intended functionality?
- Are there any logical errors, off-by-one errors, or race conditions?
- Are all edge cases handled (empty inputs, null values, boundary conditions)?
- Are error paths properly handled and do not silently fail?
- Are there any unhandled exceptions or improper error propagation?

## 2. Security

- Is user input properly validated, sanitized, and escaped?
- Are there any injection vulnerabilities (SQL, NoSQL, command, XSS, template)?
- Are authentication and authorization checks correctly implemented?
- Is sensitive data (passwords, tokens, PII) handled securely?
- Are there any hardcoded secrets, API keys, or credentials?

## 3. Performance

- Are there any obvious performance bottlenecks or N+1 query problems?
- Are expensive operations cached appropriately?
- Is there unnecessary object allocation, excessive copying, or memory waste?
- Are async/concurrent patterns used appropriately for I/O-bound operations?
- Could the time or space complexity be improved?

## 4. Maintainability

- Is the code easy to understand and modify?
- Are functions and classes appropriately sized and single-responsibility?
- Are names meaningful, consistent, and self-documenting?
- Is there excessive duplication that should be extracted?
- Are dependencies explicit and loosely coupled?

## 5. Style & Consistency

- Does the code follow the project's style guide and conventions?
- Are there any formatting issues, inconsistent naming, or dead code?
- Is the code idiomatic for the language and framework?

## 6. Test Coverage

- Are there unit tests for core logic and edge cases?
- Do tests actually verify behavior (not just exercise code)?
- Are integration or end-to-end tests needed for this change?
- Are test names descriptive and test structure clear?

## 7. Documentation

- Is the purpose of the code clear from comments or docs?
- Are public APIs documented with params, returns, and exceptions?
- Are complex algorithms or non-obvious decisions explained?
- Are there TODO or FIXME comments that need addressing?

## Output Format

For each issue, provide:

```
### [SEVERITY] Title

- **File**: path/to/file:line
- **Description**: What is wrong and why it matters
- **Suggestion**: Specific, actionable fix
- **Example**:

\`\`\`language
// current code (if applicable)

// suggested fix (if applicable)
\`\`\`
```

## Summary

At the end, provide:

- **Files reviewed**: list of files
- **Total issues found**: count by severity
- **Positive highlights**: what the code does well
- **Overall assessment**: is the code ready for merge, needs changes, or needs major rework
