---
name: python-expert
description: Use when writing Python code. Covers Pythonic idioms, typing, async/await, packaging, testing, and performance optimization.
---

# Python Expert Skill

## Overview
Python is a high-level, interpreted programming language known for its readability, versatility, and extensive ecosystem. Expert-level Python usage involves understanding the language's internals, writing idiomatic code, leveraging type hints, using async/await for concurrency, and following established packaging and testing practices.

## Instructions
- Follow PEP 8 for code style; use `black` for formatting and `ruff` for linting
- Use type hints for all function signatures and public APIs (Python 3.6+)
- Prefer `pathlib` over `os.path` for filesystem operations
- Use `f-strings` for string formatting (Python 3.6+)
- Use context managers (`with` statements) for resource management
- Use list comprehensions and generator expressions over `map()`/`filter()`/manual loops
- Prefer `dataclasses` or `NamedTuple` for simple data containers
- Use `enumerate()` instead of `range(len())` for indexed iteration
- Use `zip()` for parallel iteration over multiple iterables
- Use `*` and `**` unpacking operators for function arguments and sequence expansion
- Use `__slots__` in classes with many instances to reduce memory overhead
- Use `functools.lru_cache` and `functools.cache` for memoization
- Use `itertools` for complex iteration patterns (chain, product, permutations, groupby)

## Core Concepts

### Pythonic Idioms
- **EAFP** (Easier to Ask for Forgiveness than Permission): `try/except` instead of `if` checks
- **Duck Typing**: "If it walks like a duck and quacks like a duck, it's a duck"
- **Composition over Inheritance**: Favor composition and mixins over deep class hierarchies
- **Explicit is Better than Implicit**: Zen of Python — code should be clear and unambiguous
- **Flat is Better than Nested**: Avoid deep nesting; use early returns and guard clauses

### Type Hints
- Basic types: `str`, `int`, `float`, `bool`, `bytes`, `None`
- Collections: `list[T]`, `dict[K, V]`, `set[T]`, `tuple[T, ...]`
- `Optional[T]` = `T | None` (Python 3.10+)
- `Union[T, U]` = `T | U` (Python 3.10+)
- `Callable[[ArgType], ReturnType]` for function types
- `Type[T]` for class objects
- `Any` for dynamic types (use sparingly)
- `Self` for return type of class methods (Python 3.11+)
- `TypedDict` for dictionary with fixed keys and types
- `Protocol` for structural subtyping (static duck typing)
- `Literal` for specific literal values
- `Final` for constants that shouldn't be overridden
- `overload` for multiple function signatures

### Async/Await
- `async def` for coroutines, `await` for calling coroutines
- `asyncio.run(main())` for entry point
- `asyncio.create_task()` for concurrent tasks
- `asyncio.gather()` for running multiple coroutines concurrently
- `asyncio.wait()` with `FIRST_COMPLETED`, `ALL_COMPLETED`, `FIRST_EXCEPTION`
- `asyncio.as_completed()` for processing results as they complete
- `asyncio.Semaphore` for concurrency limiting
- `asyncio.Queue` for producer-consumer patterns
- `async for` for async iterators, `async with` for async context managers
- Use `anyio` or `trio` as alternatives to `asyncio` for structured concurrency
- `aiohttp` / `httpx` for async HTTP calls
- `asyncpg` for async PostgreSQL, `aioredis` for async Redis

### Packaging
- `pyproject.toml` as the standard configuration file (PEP 518, 621)
- Build backends: `setuptools`, `flit`, `pdm`, `hatchling`
- `[project]` table: name, version, dependencies, optional-dependencies
- Entry points: `[project.scripts]` for CLI tools
- Use `src/` layout: `src/mypackage/` to prevent import confusion
- Versioning: semantic versioning (MAJOR.MINOR.PATCH)
- `pip install -e .` for development installation
- Use `virtualenv` or `uv` for isolated environments
- `requirements.txt` for pinning exact versions (production)
- `pyproject.toml` for declaring dependencies (development)

### Testing
- `pytest` as the preferred testing framework
- `pytest.fixture` for test setup/teardown and shared resources
- `pytest.mark.parametrize` for data-driven tests
- `pytest.mark.asyncio` for async tests
- `pytest-cov` for coverage reporting
- `pytest-mock` for mocking (wraps `unittest.mock`)
- `pytest-xdist` for parallel test execution
- `factory_boy` for generating test data
- `hypothesis` for property-based testing
- Test file structure: `tests/` mirroring `src/` directory
- Test function naming: `test_<feature>_<scenario>`

## Examples

### Pythonic Code Patterns
```python
from pathlib import Path
from dataclasses import dataclass, field
from typing import Self
from functools import cached_property

@dataclass
class Config:
    name: str
    version: str = "1.0"
    features: set[str] = field(default_factory=set)

    @cached_property
    def feature_list(self) -> list[str]:
        return sorted(self.features)

    @classmethod
    def from_file(cls, path: Path) -> Self:
        with open(path) as f:
            return cls(**parse_toml(f.read()))

    def enable_feature(self, feature: str) -> None:
        self.features.add(feature)


def process_files(directory: Path, pattern: str = "*.txt") -> list[tuple[Path, int]]:
    result = [
        (file, count_lines(file))
        for file in directory.glob(pattern)
        if file.stat().st_size > 0
    ]
    return sorted(result, key=lambda x: x[1], reverse=True)


def count_lines(path: Path) -> int:
    with open(path) as f:
        return sum(1 for _ in f)
```

### Async Example
```python
import asyncio
import httpx
from dataclasses import dataclass

@dataclass
class FetchResult:
    url: str
    status: int
    size: int

async def fetch_url(client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore) -> FetchResult:
    async with sem:
        response = await client.get(url, timeout=10)
        content = await response.aread()
        return FetchResult(url=url, status=response.status_code, size=len(content))

async def fetch_all(urls: list[str], concurrency: int = 10) -> list[FetchResult]:
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        tasks = [fetch_url(client, url, sem) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r for r in results
            if isinstance(r, FetchResult)
        ]

async def main() -> None:
    urls = [
        "https://example.com",
        "https://python.org",
        "https://github.com",
    ]
    results = await fetch_all(urls)
    for result in results:
        print(f"{result.url}: {result.status} ({result.size} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
```

### Decorator Pattern
```python
from functools import wraps
from typing import Callable, ParamSpec, TypeVar, Any
import time
import logging

P = ParamSpec("P")
T = TypeVar("T")

def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logging.warning("Attempt %d failed: %s", attempt + 1, e)
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))
            raise last_exception  # type: ignore
        return wrapper
    return decorator


def timed(func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logging.info("%s took %.3fs", func.__name__, elapsed)
        return result
    return wrapper
```

### Context Manager
```python
from contextlib import contextmanager
from pathlib import Path
import json
from typing import Iterator

@contextmanager
def atomic_write(path: Path) -> Iterator[Path]:
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        yield tmp_path
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

# Usage
with atomic_write(Path("data.json")) as tmp:
    with open(tmp, "w") as f:
        json.dump({"key": "value"}, f)
```

### Property-Based Testing
```python
from hypothesis import given, strategies as st
from hypothesis import assume

def add_positive(a: int, b: int) -> int:
    if a <= 0 or b <= 0:
        raise ValueError("Both arguments must be positive")
    return a + b

@given(a=st.integers(min_value=1, max_value=1000),
       b=st.integers(min_value=1, max_value=1000))
def test_add_positive(a, b):
    result = add_positive(a, b)
    assert result == a + b
    assert result > a
    assert result > b

@given(a=st.integers(min_value=-100, max_value=0))
def test_add_positive_negative_raises(a):
    with pytest.raises(ValueError, match="positive"):
        add_positive(a, 5)
```

## Best Practices
- Use `import` at the top of the file; avoid inline imports
- Keep functions under 50 lines; classes under 200 lines
- Use `__all__` to define public API of a module
- Use `if __name__ == "__main__":` for script entry points
- Use `logging` instead of `print` for application output
- Use `pathlib.Path` for all filesystem operations
- Use `with` for file I/O, locks, and other resources
- Use `enum` for fixed sets of constants
- Use `__repr__` for debuggable object representations
- Use `@property` for computed attributes instead of getter methods
- Use `@classmethod` for alternative constructors
- Use `@staticmethod` for utility functions within a class
- Prefer `is` over `==` for comparing with `None`, `True`, `False`
- Use `_` for unused variables in destructuring

## Common Mistakes
- Using mutable default arguments (`def func(lst=[]):`) — they're shared across calls
- Ignoring `__pycache__` and `.pyc` files in version control
- Using `except:` bare exception (catches `KeyboardInterrupt`, `SystemExit`)
- Modifying a list while iterating over it
- Using `is` for value comparisons (should use `==`)
- Confusing `==` and `is` for comparison
- Using `time.sleep()` in async code (blocks the event loop)
- Not using `async for` with async iterators
- Forgetting to `await` a coroutine (returns a coroutine object, not the result)
- Using `from module import *` (pollutes namespace, hides dependencies)
- Creating circular imports between modules
- Not handling `FileNotFoundError` when reading files
- Using `os.system()` instead of `subprocess.run()`
- Using `range(len(list))` instead of `enumerate(list)`
- Not using `if __name__ == "__main__":` guard in reusable modules

## Libraries
- **pydantic** — data validation and settings management using Python type hints
- **rich** — rich text formatting in terminal
- **click** / **typer** — CLI framework
- **httpx** — modern HTTP client (sync and async)
- **sqlalchemy** — ORM and SQL toolkit
- **pytest** — testing framework
- **hypothesis** — property-based testing
- **fastapi** — web API framework
- **celery** — distributed task queue
- **structlog** — structured logging
- **beartype** — runtime type checking
- **dishka** — dependency injection
- **uv** — fast Python package installer and resolver
- **ruff** — fast Python linter and formatter
- **mypy** — static type checker

## Design Principles
- **Zen of Python (PEP 20)**: Readability counts, explicit is better than implicit, simple is better than complex
- **DRY**: Extract repeated patterns into functions, classes, or decorators
- **Single Responsibility**: Each function, class, and module should have a single, well-defined purpose
- **Open/Closed**: Open for extension, closed for modification (use subclassing and composition)
- **Dependency Inversion**: Depend on abstractions, not concrete implementations
- **Separation of Concerns**: Business logic, I/O, and presentation should be separated

## Coding Standards
- 4-space indentation (PEP 8)
- Maximum line length: 88 (black default) or 79 (strict PEP 8)
- Two blank lines between top-level definitions, one between methods
- Imports: standard library, third-party, local (separated by blank lines)
- Use `snake_case` for variables, functions, and methods
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants
- Use `_single_leading_underscore` for internal/private convention
- Use `__double_leading_underscore` for name mangling (rare)
- Type hints on all public functions and methods
- Docstrings in Google or NumPy style for public APIs

## Performance
- Use `__slots__` in classes with many instances to reduce memory
- Use `local` variable references to avoid global/builtin lookups in hot loops
- Use `map()` and `filter()` with pre-defined functions (faster than lambdas)
- Use `array` module or `numpy` for large numerical arrays
- Use `collections.deque` for stack/queue operations (O(1) append/pop on both ends)
- Use `functools.lru_cache` for memoization of pure functions
- Use `sys.intern()` for string deduplication
- Use `asyncio` for I/O-bound concurrency
- Use `multiprocessing` for CPU-bound parallelism
- Profile with `cProfile` and `py-spy` before optimizing
- Use `__slots__` and `__dict__` reduction for memory-intensive applications
- Avoid attribute lookup in hot code paths; assign to local variables
- Use `str.join()` instead of `+=` for string concatenation in loops
- Use `bisect` module for sorted list operations
- Use `heapq` for priority queue operations
- Use `isinstance` checks with tuples instead of multiple `or` checks
- Prefer `try/except` over `if` for common cases (EAFP is Pythonic)
## Memory Management
- Python uses reference counting and garbage collection (generational GC)
- Circular references are collected by the GC; use `weakref` to break cycles
- Use `del` to remove references and allow collection
- Use `gc.set_threshold()` for tuning GC frequency
- Use `sys.getsizeof()` to estimate object sizes
- Be aware of memory fragmentation with many small allocations
- Use `__slots__` to eliminate per-object `__dict__` overhead
- Use `array` or `numpy` for numerical data instead of lists of small objects
- Context managers ensure timely cleanup of file handles and network connections
- Use `memory_profiler` to identify memory bottlenecks
- Avoid storing large temporary results; use generator pipelines instead
- Use `sys.setrecursionlimit()` carefully (default 1000)
- Use `tracemalloc` for tracking memory allocations
