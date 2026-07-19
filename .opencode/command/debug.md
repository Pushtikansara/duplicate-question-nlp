---
description: Debug issues systematically to find root causes.
---

# Debugging Prompt

You are tasked with systematically debugging the following issue to identify the root cause and implement a fix.

## Input

{{input}}

## Debugging Methodology

Follow the scientific method: observe, hypothesize, test, conclude.

### Step 1: Reproduce the Issue

- **Environment**: OS, browser/version, device, network conditions
- **Precise steps to reproduce**:
  1. [step 1]
  2. [step 2]
  3. [step 3]
- **Expected behavior**: what should happen
- **Actual behavior**: what actually happens (include exact error messages, screenshots, logs)
- **Is the issue intermittent or consistent?**
- **Can it be reproduced in isolation (minimal reproduction)?**
- **Does it occur on other environments?**
- **What changed recently that might have introduced this bug?** (git log, recent deploys, dependency updates)

### Step 2: Gather Information

**Logs**:
- Application logs (error level, debug level)
- Server/container logs
- Browser console logs
- Network request/response logs

**Error Messages**:
- Full stack trace
- Error codes
- HTTP status codes

**State**:
- Database state at time of failure
- Application state (memory, thread dumps, heap dumps)
- Configuration values
- Feature flag states

**Metrics**:
- Error rate spikes
- Latency changes
- Resource utilization (CPU, memory, disk, network)
- Rate of requests at time of failure

### Step 3: Inspect Relevant Code Paths

- Trace the execution flow from entry point to failure point
- Read the code in the stack trace frames
- Check all function calls, conditionals, and error handling along the path
- Look for common bug patterns:
  - Off-by-one errors in loops and indexing
  - Null/undefined reference errors
  - Type coercion or type mismatch
  - Race conditions and timing issues
  - Incorrect state management
  - Improper resource cleanup
  - Unvalidated user input
  - Incorrect API usage
  - Incorrect assumptions about data format
  - Thread safety issues

### Step 4: Formulate Hypotheses

For each hypothesis, state:

```
### Hypothesis N: [Brief description of suspected cause]

- **Evidence for**: facts that support this hypothesis
- **Evidence against**: facts that contradict this hypothesis
- **Prediction**: if this is the cause, what we would observe when we test it
- **Experiment**: specific action to confirm or refute
```

Possible hypotheses to consider:
- A recent code change introduced a regression
- A race condition between concurrent operations
- A dependency upgrade changed behavior
- A configuration or environment difference
- Corrupted data or state
- Resource exhaustion
- A third-party API changed or is down
- Browser/device compatibility issue

### Step 5: Test Each Hypothesis

For each experiment:

1. **Setup**: what needs to be in place
2. **Action**: what to do
3. **Expected result**: what should happen if hypothesis is correct
4. **Actual result**: what actually happened
5. **Conclusion**: hypothesis confirmed, refuted, or inconclusive

Tools and techniques:
- Add logging/printf statements at key points
- Use debugger (pdb, gdb, Chrome DevTools, IDE debugger)
- Write a minimal test case that reproduces the issue
- Use monitoring and profiling tools
- Use feature flags to isolate changes
- Rollback recent changes to test
- Compare working vs non-working environments

### Step 6: Identify Root Cause

Once a hypothesis is confirmed:

- **Root cause**: one-sentence description of the fundamental cause
- **Why analysis** (5 Whys):
  1. Why did the error occur? Because...
  2. Why did that happen? Because...
  3. Why did that happen? Because...
  4. Why did that happen? Because...
  5. Why did that happen? Because...
- **Contributing factors**: what made this bug possible or harder to find

### Step 7: Implement Fix

- **Fix description**: what the fix does and why it works
- **Code change**:

```language
// before (buggy code)
// after (fixed code)
```

- **Edge cases considered**: ensure fix handles all cases
- **Tests added**: unit test, integration test, regression test
- **Performance impact**: is the fix efficient?

### Step 8: Verify Fix

- [ ] Fix resolves the original issue in the reproduction environment
- [ ] All existing tests still pass
- [ ] New regression tests pass
- [ ] Related functionality is not broken
- [ ] Edge cases are handled
- [ ] No new warnings or errors introduced

### Step 9: Prevent Recurrence

- **Root cause category**: logic error, input validation, race condition, environmental, etc.
- **Systemic fix**: what process, tool, or practice change prevents similar bugs
  - Add linting rule or type check
  - Improve test coverage
  - Add input validation
  - Improve logging/monitoring
  - Update runbook/playbook
  - Add code review checklist item
- **Postmortem**: document what happened, why, and how it was fixed

## Debugging Output

### Summary
- **Issue**: one-line description
- **Root cause**: one-line explanation
- **Fix**: one-line description
- **Files changed**: list

### Timeline of Debugging Steps
1. ...
2. ...
3. ...

### Root Cause Analysis
...detailed explanation...

### Fix
...code and explanation...

### Preventive Measures
...recommendations...
