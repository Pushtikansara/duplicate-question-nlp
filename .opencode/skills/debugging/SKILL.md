---
name: debugging
description: Use when debugging code or systems. Covers systematic debugging, logging, profiling, and root cause analysis.
---

# Debugging Skill

## Instructions

Debugging is the systematic process of identifying, isolating, and fixing defects in software or systems. Effective debugging requires a methodical approach, the right tools, and a deep understanding of the system. This skill covers debugging methodologies, logging strategies, profiling techniques, and root cause analysis.

### The Scientific Method of Debugging

Debugging follows the scientific method:

1. **Observe**: Gather data about the problem (logs, error messages, symptoms)
2. **Hypothesize**: Formulate a theory about the root cause
3. **Predict**: Determine what would confirm or refute the hypothesis
4. **Experiment**: Test the hypothesis with a targeted experiment
5. **Analyze**: Evaluate the results
6. **Repeat**: Refine the hypothesis and test again
7. **Fix**: Implement the solution once root cause is confirmed
8. **Verify**: Confirm the fix resolves the original problem
9. **Prevent**: Add tests, logging, or monitoring to prevent recurrence

### Debugging Mindset

- **Stay calm**: Panic leads to random changes and wasted time
- **Be systematic**: Change one variable at a time
- **Verify assumptions**: Do not assume anything works correctly
- **Read error messages carefully**: They contain specific clues
- **Restate the problem**: Write it down in detail
- **Rubber duck debugging**: Explain the problem to someone (or something)
- **Take breaks**: Stepping away often reveals the solution
- **Bisect**: Narrow down the problem space methodically
- **Check recent changes**: 90% of bugs come from recent modifications

### The Debugging Toolkit

| Category | Tools |
|----------|-------|
| Logging | Log4j, Winston, pino, structlog, `console.log` |
| Debuggers | GDB, LLDB, Chrome DevTools, VS Code debugger, PyCharm debugger |
| Profilers | perf, Valgrind, Chrome DevTools, Py-Spy, dtrace |
| Network | Wireshark, tcpdump, mitmproxy, Charles Proxy, curl |
| System | strace, ltrace, dmesg, journalctl, vmstat, iostat |
| Memory | Valgrind, AddressSanitizer, LeakSanitizer, heap profiling |
| Static Analysis | ESLint, SonarQube, clang-tidy, Pylint, Ruff |
| Tracing | OpenTelemetry, Jaeger, Zipkin, Datadog APM |

## Examples

### Example 1: Systematic Debugging Process

```python
"""
Scenario: A web API returns 500 errors intermittently.
Systematic debugging approach:
"""

import logging
import traceback

# Step 1: Add detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_order(order_id: int) -> dict:
    """Process an order and return the result."""
    try:
        logger.debug(f"Processing order {order_id}")

        # Step 3: Isolate the problem area
        customer = get_customer(order_id)
        logger.debug(f"Found customer: {customer.id}")

        # Hypothesis: Race condition in inventory check
        inventory = check_inventory(order_id)
        logger.debug(f"Inventory check: {inventory}")

        if not inventory['available']:
            raise ValueError("Out of stock")

        # Step 5: Add timing measurements
        import time
        start = time.time()
        result = charge_payment(customer, order_id)
        duration = time.time() - start
        logger.debug(f"Payment took {duration:.3f}s")

        if duration > 2.0:
            logger.warning(f"Slow payment processing for order {order_id}")

        return result

    except Exception as e:
        logger.error(f"Order {order_id} failed: {e}")
        logger.debug(f"Traceback:\n{traceback.format_exc()}")

        # Step 6: Add context for reproduction
        logger.error(f"Context - customer: {customer}, inventory: {inventory}")

        raise


# Step 8: Add metrics and monitoring
from dataclasses import dataclass
from collections import Counter

error_counter = Counter()

def track_errors(error_type: str):
    error_counter[error_type] += 1
    if error_counter[error_type] > 100:
        logger.critical(f"Error threshold exceeded for {error_type}")


# Step 9: Add defensive checks
def check_prerequisites():
    """Validate system state before processing."""
    checks = {
        'database_connected': check_db_connection(),
        'redis_available': check_redis(),
        'disk_space_available': check_disk_space(),
    }

    for check_name, result in checks.items():
        if not result:
            logger.error(f"Prerequisite failed: {check_name}")
            raise SystemError(f"System check failed: {check_name}")

    logger.info(f"All system checks passed: {checks}")
```

### Example 2: JavaScript Debugging with Chrome DevTools

```javascript
// Scenario: Debugging a React component with state issues

// 1. Use console effectively
console.log('Component render:', { props, state });        // Basic logging
console.table(users);                                        // Table format
console.time('api-call');                                    // Timing
console.timeEnd('api-call');
console.trace('Navigation trace');                           // Stack trace
console.group('User Details');                               // Grouped logs
console.log('Name:', user.name);
console.log('Role:', user.role);
console.groupEnd();

// 2. Breakpoints (in DevTools)
// - Line breakpoints: Click line number
// - Conditional breakpoints: Right-click > "Add conditional breakpoint"
// - DOM breakpoints: Elements > Right-click > Break on
// - XHR breakpoints: Sources > XHR Breakpoints
// - Event listener breakpoints: Sources > Event Listener Breakpoints

// 3. Debugger statement (code breakpoint)
function calculateTotal(items) {
    debugger; // Execution pauses here in DevTools
    return items.reduce((sum, item) => sum + item.price, 0);
}

// 4. React DevTools
// - Component tree inspection
// - State and props inspection
// - Performance profiler
// - Component search

// 5. Network throttling simulation
// DevTools > Network > Throttling
// Test with: "Slow 3G", "Fast 3G", "Offline"

// 6. Source maps for debugging production
// Ensure source maps are uploaded to error monitoring service

// 7. Error boundary for React
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        // Log to error reporting service
        logErrorToService(error, errorInfo);
        console.error('Error caught:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return <h1>Something went wrong: {this.state.error.message}</h1>;
        }
        return this.props.children;
    }
}
```

### Example 3: Memory Leak Detection in Node.js

```javascript
// 1. Enable garbage collection for profiling
// Run with: node --expose-gc --inspect app.js

// 2. Memory snapshot comparison
const heapdump = require('heapdump');

function takeSnapshot(label) {
    const filename = `heap-${label}-${Date.now()}.heapsnapshot`;
    heapdump.writeSnapshot(filename);
    console.log(`Heap snapshot saved: ${filename}`);
}

// Take baseline
takeSnapshot('baseline');

// After suspicious operation
// ... leaky code ...
takeSnapshot('after-operation');

// Compare snapshots in Chrome DevTools > Memory > Load

// 3. Detect event emitter leaks
process.on('warning', (warning) => {
    if (warning.name === 'MaxListenersExceededWarning') {
        console.error('Event emitter leak detected:', warning);
        console.trace('Stack trace');
    }
});

// Set custom max listeners
require('events').EventEmitter.defaultMaxListeners = 20;

// 4. Monitor memory usage
const used = process.memoryUsage();
console.log({
    rss: `${Math.round(used.rss / 1024 / 1024)} MB`,         // Resident Set Size
    heapTotal: `${Math.round(used.heapTotal / 1024 / 1024)} MB`,  // Total heap
    heapUsed: `${Math.round(used.heapUsed / 1024 / 1024)} MB`,   // Used heap
    external: `${Math.round(used.external / 1024 / 1024)} MB`,   // External memory
});

// 5. Periodic memory check
setInterval(() => {
    const usage = process.memoryUsage();
    if (usage.heapUsed > 500 * 1024 * 1024) { // 500MB threshold
        console.error('Memory usage exceeded threshold');
        takeSnapshot('high-memory');
    }
}, 60000);

// 6. Profile with clinic.js
// npx clinic doctor -- node app.js
// npx clinic flame -- node app.js
// npx clinic bubbleprof -- node app.js
```

### Example 4: Network Debugging

```bash
# 1. Check DNS resolution
dig example.com
nslookup example.com
host example.com

# 2. Trace network route
traceroute example.com
mtr example.com          # Continuous traceroute

# 3. Check connectivity and latency
ping -c 10 example.com

# 4. HTTP debugging with curl
curl -v https://api.example.com/endpoint       # Verbose output
curl -i https://api.example.com/endpoint       # Include headers
curl -w "%{http_code}: %{time_total}s\n"       # Response code and timing
curl -H "Authorization: Bearer token" ...      # Custom headers
curl -X POST -d '{"key":"value"}' -H "Content-Type: application/json" ...

# 5. TCP dump
sudo tcpdump -i eth0 port 443 -w capture.pcap  # Capture to file
sudo tcpdump -i eth0 host 10.0.0.1             # Filter by host
sudo tcpdump -i eth0 'tcp[13] & 2 != 0'        # Filter SYN packets

# 6. Analyze with Wireshark (from pcap file)
wireshark capture.pcap

# 7. Check listening ports
ss -tulpn
netstat -tulpn
lsof -i :3000

# 8. Test local socket connectivity
nc -zv localhost 3000       # TCP port check
nc -zuv localhost 3000      # UDP port check
```

### Example 5: Post-Mortem Debugging

```python
"""
Post-Mortem Analysis Template
Fill this out for production incidents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Incident:
    title: str
    severity: str  # SEV1, SEV2, SEV3
    duration_minutes: int
    date: datetime
    root_cause: str
    trigger: str
    impact: str = ""
    timeline: List[dict] = field(default_factory=list)
    action_items: List[dict] = field(default_factory=list)

    def add_timeline_entry(self, time: str, event: str, who: str):
        self.timeline.append({
            'time': time,
            'event': event,
            'who': who,
        })

    def add_action_item(self, description: str, owner: str, due_date: str, priority: str = "P1"):
        self.action_items.append({
            'description': description,
            'owner': owner,
            'due_date': due_date,
            'priority': priority,
            'status': 'open',
        })

    def analysis(self) -> dict:
        """Five Whys analysis."""
        return {
            'question_1': 'What happened?',
            'answer_1': self.trigger,
            'question_2': 'Why did it happen?',
            'answer_2': self.root_cause,
            'question_3': 'Why was the root cause present?',
            'answer_3': 'Missing validation in billing module',
            'question_4': 'Why was the validation missing?',
            'answer_4': 'Edge case not covered in requirements',
            'question_5': 'Why was the edge case missed?',
            'answer_5': 'No review process for edge cases in the billing module',
            'systemic_issue': 'Incomplete requirements coverage for billing edge cases',
        }

    def generate_report(self) -> str:
        """Generate post-mortem report."""
        report = [
            f"# Post-Mortem: {self.title}",
            f"**Date**: {self.date}",
            f"**Severity**: {self.severity}",
            f"**Duration**: {self.duration_minutes} minutes",
            f"**Impact**: {self.impact}",
            "",
            "## Timeline",
        ]

        for entry in self.timeline:
            report.append(f"- **{entry['time']}** - {entry['event']} ({entry['who']})")

        report.extend([
            "",
            "## Root Cause Analysis",
            f"**Trigger**: {self.trigger}",
            f"**Root Cause**: {self.root_cause}",
            "",
            "## Five Whys",
        ])

        analysis = self.analysis()
        for i in range(1, 6):
            report.append(f"**{analysis[f'question_{i}']}**")
            report.append(f"{analysis[f'answer_{i}']}")
            report.append("")

        report.append("## Action Items")
        for item in self.action_items:
            report.append(f"- [ ] **{item['priority']}**: {item['description']} (Owner: {item['owner']}, Due: {item['due_date']})")

        return "\n".join(report)
```

### Example 6: Profiling Python Applications

```python
"""
Profiling techniques for Python applications.
"""

import cProfile
import pstats
import io
import time
from functools import wraps
from typing import Callable

# 1. Basic cProfile usage
def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Code to profile
    result = expensive_operation()

    profiler.disable()
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumtime')
    stats.print_stats(20)  # Top 20 by cumulative time
    print(s.getvalue())


# 2. Decorator-based profiling
def profile_decorator(output_file: str = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            result = func(*args, **kwargs)
            profiler.disable()

            stats = pstats.Stats(profiler)
            if output_file:
                stats.dump_stats(output_file)
            else:
                stats.sort_stats('cumtime').print_stats(20)

            return result
        return wrapper
    return decorator

@profile_decorator('profile_output.prof')
def slow_function():
    total = 0
    for i in range(1000000):
        total += i ** 2
    return total


# 3. Line profiler (requires: pip install line_profiler)
# @profile  # Used with kernprof -l -v script.py
def line_profile_example():
    a = [i ** 2 for i in range(100000)]
    b = [i ** 3 for i in range(100000)]
    c = [x + y for x, y in zip(a, b)]
    return sum(c)


# 4. Memory profiler (requires: pip install memory-profiler)
# @profile  # Used with python -m memory_profiler script.py
def memory_profile_example():
    large_list = [i for i in range(1000000)]
    large_dict = {i: i * 2 for i in range(100000)}
    return len(large_list) + len(large_dict)


# 5. Timing context manager
class Timer:
    """Context manager for timing code blocks."""

    def __init__(self, name: str = "block"):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start
        print(f"{self.name}: {self.elapsed:.4f}s")


# Usage
with Timer("database_query"):
    result = run_database_query()

with Timer("data_processing"):
    processed = process_data(result)

print(f"Total: {sum(elapsed for ...)}")


# 6. Time profiling decorator
def timeit(repetitions: int = 1) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            total = 0
            for _ in range(repetitions):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                total += time.perf_counter() - start

            avg = total / repetitions
            print(f"{func.__name__}: avg {avg*1000:.2f}ms over {repetitions} runs")
            return result
        return wrapper
    return decorator

@timeit(repetitions=10)
def compute():
    return sum(range(1000000))
```

### Example 7: Logging Best Practices

```python
"""
Structured logging for debugging.
"""

import logging
import json
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger  # pip install python-json-logger

# 1. Structured JSON logging
def setup_json_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)

    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d',
        datefmt='%Y-%m-%dT%H:%M:%S%z',
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


# 2. Correlation IDs for request tracing
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='')

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


def setup_request_logging():
    logger = logging.getLogger('app')
    logger.addFilter(CorrelationIdFilter())


def handle_request(request):
    request_id = str(uuid.uuid4())[:8]
    token = request_id_var.set(request_id)

    try:
        logger.info("Processing request", extra={
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent'),
        })
        result = process_request(request)
        logger.info("Request completed", extra={
            'status_code': result.status_code,
            'duration_ms': result.duration_ms,
        })
        return result
    except Exception as e:
        logger.error("Request failed", extra={
            'error': str(e),
            'error_type': type(e).__name__,
        })
        raise
    finally:
        request_id_var.reset(token)


# 3. Log levels guide
# DEBUG: Detailed info for diagnosing problems (not in production)
# INFO: Normal operational messages (confirm things are working)
# WARNING: Unexpected but handled situations (deprecated API, high memory)
# ERROR: Serious problem, operation could not complete
# CRITICAL: System is unusable, immediate action needed


# 4. Contextual logging
class ContextLogger:
    """Logger that preserves context across calls."""

    def __init__(self, logger: logging.Logger, **context):
        self._logger = logger
        self._context = context

    def bind(self, **kwargs) -> 'ContextLogger':
        new_context = {**self._context, **kwargs}
        return ContextLogger(self._logger, **new_context)

    def info(self, msg: str, **kwargs):
        self._logger.info(msg, extra={**self._context, **kwargs})

    def error(self, msg: str, **kwargs):
        self._logger.error(msg, extra={**self._context, **kwargs})

    def debug(self, msg: str, **kwargs):
        self._logger.debug(msg, extra={**self._context, **kwargs})


logger = ContextLogger(logging.getLogger('app'), service='payment-api')
logger = logger.bind(request_id='abc123')
logger.info("Processing payment", amount=99.99, currency='USD')
```

## Best Practices

### Logging Practices

- Use structured logging (JSON format) for machine-parseable logs
- Include correlation IDs to trace requests across services
- Log at appropriate levels (DEBUG in dev, INFO+ in production)
- Never log sensitive data (passwords, tokens, PII)
- Add context to logs (function name, line number, input params)
- Use log aggregation tools (ELK, Datadog, Splunk) for searching

### Systematic Debugging

- Reproduce the bug consistently before attempting to fix it
- Change one variable at a time and observe the effect
- Use binary search (bisect) to narrow down the problem area
- Write a failing test that reproduces the bug
- Read stack traces completely; they identify the exact failure point
- Check the simplest possible cause first (typo, config, network)
- Use version control bisect (`git bisect`) for regression bugs

### Profiling Practices

- Profile before optimizing; don't optimize based on hunches
- Establish baseline metrics before making changes
- Profile in production-like environments with realistic data
- Focus on the slowest operations first (the bottleneck principle)
- Measure CPU, memory, I/O, and network separately
- Use flame graphs for visualizing call stacks and hot paths

## Common Mistakes

- **Guessing instead of investigating**: Making random changes based on hunches wastes time. Always gather data first.
- **Ignoring error messages**: Error messages contain specific information about what went wrong. Read them carefully before making changes.
- **Not reproducing the bug**: Fixing a bug you cannot reproduce is guesswork. Always find a reliable reproduction case.
- **Changing too many things at once**: Multiple simultaneous changes make it impossible to determine which one fixed the issue.
- **Not checking recent changes**: Most bugs are introduced by recent code modifications. Use `git diff` and `git blame` first.
- **Skipping root cause analysis**: Treating symptoms rather than root causes leads to recurring bugs.
- **Not adding tests for bugs**: A bug fix without a regression test will be reintroduced.
- **Over-relying on print logging**: Structured logging with context is far more useful than scattered print statements.
- **Debugging without reproduction steps**: Documenting exact reproduction steps saves time when revisiting the issue.
- **Not asking for help**: Stuck on a problem? Explain it to someone or use rubber duck debugging.

## Libraries

### Debugging Tools by Language

| Language | Tools |
|----------|-------|
| JavaScript | Chrome DevTools, Node.js Inspector, React DevTools, Redux DevTools |
| Python | pdb, ipdb, PyCharm Debugger, pudb, traceback |
| Java | IntelliJ Debugger, Eclipse Debugger, JDB, VisualVM |
| Go | Delve (dlv), pprof, trace |
| Rust | gdb, lldb, rr (reverse debugging) |
| C/C++ | GDB, LLDB, Valgrind, AddressSanitizer |

### Profiling Tools

| Tool | Language | Purpose |
|------|----------|---------|
| perf | Linux | CPU profiling and tracing |
| Valgrind | C/C++ | Memory debugging and profiling |
| FlameGraph | Any | Visualization of profiling data |
| Py-Spy | Python | Sampling profiler for Python |
| clinic.js | Node.js | Comprehensive Node.js profiling |
| async-profiler | Java | Low-overhead Java profiler |
| Go pprof | Go | Built-in profiling |
| dtrace | Linux/macOS | Dynamic tracing framework |

## Design Principles

### Fail Fast and Loud

Design systems to detect and report errors early. Validate inputs at system boundaries, check invariants, and crash immediately on unrecoverable errors. Silent failures are the hardest to debug.

### Observability by Design

Build logging, metrics, and tracing into the system from the start, not as an afterthought. Every service should expose health checks, metrics endpoints, and structured logs. Distributed systems must have correlation IDs that flow through all services.

### Reproducibility

Every bug should be reproducible. Use deterministic builds, seed random number generators for testing, record and replay network traffic, and snapshot database state. If you cannot reproduce it, you cannot fix it.

### Scientific Approach

Debugging is science, not art. Form hypotheses, design experiments, collect data, and draw conclusions. The temptation to skip the data collection and jump to conclusions is the most common cause of debugging failure.

## Coding Standards

### Logging Format

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "ERROR",
    "logger": "payment-service",
    "message": "Payment processing failed",
    "request_id": "a1b2c3d4",
    "error": {
        "type": "ConnectionTimeout",
        "message": "Connection to payment gateway timed out",
        "stack": "..."
    },
    "context": {
        "order_id": 12345,
        "amount": 99.99,
        "currency": "USD"
    },
    "service": {
        "name": "payment-api",
        "version": "1.2.3",
        "host": "pod-abc-123"
    }
}
```

### Debug Code Management

```javascript
// DO: Use environment variables for debug features
const DEBUG = process.env.DEBUG === 'true';

function debugLog(...args) {
    if (DEBUG) {
        console.log('[DEBUG]', ...args);
    }
}

// DON'T: Leave debug code in production without a toggle
// console.log('Debug:', sensitiveData); // BAD

// DO: Use proper logging library
// const logger = require('pino')();
// logger.debug({ context }, 'message');

// DO: Clean up debug code before merging
// Use TODO comments if debug code must remain temporarily
// TODO: Remove debug logging after investigating performance issue
```
