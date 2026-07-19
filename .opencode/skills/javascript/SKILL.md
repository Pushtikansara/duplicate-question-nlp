---
name: javascript
description: Use when writing JavaScript code. Covers ES6+, async patterns, modules, and best practices.
---

# JavaScript Skill

## Overview
JavaScript is a high-level, dynamic, interpreted programming language that conforms to the ECMAScript specification. It is the core language of the web platform and runs in browsers, Node.js, Deno, and Bun. Modern JavaScript (ES6+) provides classes, modules, promises, and numerous syntactic improvements.

## Instructions
- Use `const` by default; use `let` only when you need to reassign a variable
- Never use `var` — it has function scoping and hoisting quirks that lead to bugs
- Use arrow functions for callbacks, closures, and short functions; use `function` declarations for methods needing `this` binding
- Use template literals for string interpolation instead of concatenation
- Use destructuring for extracting values from objects and arrays
- Use spread syntax for copying and merging objects/arrays
- Prefer `===` and `!==` over `==` and `!=` (avoid type coercion)
- Use optional chaining (`?.`) and nullish coalescing (`??`) for safe property access
- Use `for...of` for iterating arrays instead of `for...in` (which iterates keys as strings)
- Use `Array` methods (`map`, `filter`, `reduce`, `find`, `some`, `every`) instead of manual loops
- Use `async/await` over raw promises and callback patterns
- Use `import`/`export` (ES modules) instead of `require`/`module.exports` (CommonJS)

## Core Concepts

### Variables and Scoping
- `const` — block-scoped, cannot be reassigned (but objects/arrays can be mutated)
- `let` — block-scoped, can be reassigned
- Block scope: `{}` creates a scope for `const` and `let`
- Hoisting: `function` declarations are hoisted; `const` and `let` are hoisted but not initialized (Temporal Dead Zone)
- Closures: inner functions retain access to outer function's variables even after the outer function returns

### Functions
- Arrow functions: `const fn = (x) => x * 2` — no `this` binding, no `arguments` object
- Default parameters: `function greet(name = 'Guest')`
- Rest parameters: `function sum(...numbers: number[])`
- Spread operator: `Math.max(...arr)`
- Higher-order functions: functions that take or return other functions
- Immediately Invoked Function Expressions (IIFE): `(function() { ... })()`

### Objects
- Object literal shorthand: `{ name, age }` instead of `{ name: name, age: age }`
- Computed property keys: `{ [dynamicKey]: value }`
- Method shorthand: `{ greet() { ... } }` instead of `{ greet: function() { ... } }`
- Property value shorthand: `{ name }` when variable name matches property name
- `Object.freeze()` for shallow immutability
- `Object.entries()`, `Object.keys()`, `Object.values()` for iteration

### Arrays
- `map` — transform each element
- `filter` — keep elements matching a condition
- `reduce` — accumulate values into a single result
- `find` — return first matching element
- `some` — test if any element passes
- `every` — test if all elements pass
- `flat` and `flatMap` — flatten nested arrays
- `Array.from` — create arrays from iterables
- `Array.isArray` — check if value is an array

### Async JavaScript
- Callbacks: `fs.readFile(path, (err, data) => { ... })`
- Promises: `fetch(url).then(res => res.json()).catch(err => console.error(err))`
- `async/await`: syntactic sugar over promises
- `Promise.all` — run promises in parallel, fail fast
- `Promise.allSettled` — run promises in parallel, wait for all to settle
- `Promise.race` — first settled promise wins
- `Promise.any` — first fulfilled promise wins
- Error handling: always use `try/catch` with `await`

### Modules (ESM)
- Named exports: `export const foo = ...`
- Default export: `export default function bar() { ... }`
- Named import: `import { foo } from './module'`
- Default import: `import bar from './module'`
- Namespace import: `import * as mod from './module'`
- Dynamic import: `const mod = await import('./module')`
- Re-export: `export { foo } from './module'`
- ESM is static — imports are resolved at parse time, not runtime

## Examples

### Async Data Processing
```javascript
import { readFile, writeFile } from 'node:fs/promises'

async function processUserData(filePath) {
  try {
    const rawData = await readFile(filePath, 'utf-8')
    const users = JSON.parse(rawData)

    const processed = users
      .filter(user => user.isActive)
      .map(user => ({
        id: user.id,
        fullName: `${user.firstName} ${user.lastName}`,
        email: user.email?.toLowerCase(),
        role: user.role ?? 'viewer',
      }))
      .sort((a, b) => a.fullName.localeCompare(b.fullName))

    await writeFile('processed-users.json', JSON.stringify(processed, null, 2))
    return processed
  } catch (error) {
    console.error('Failed to process user data:', error)
    throw error
  }
}
```

### Event Emitter Utility
```javascript
export class EventEmitter {
  #listeners = new Map()

  on(event, listener) {
    if (!this.#listeners.has(event)) {
      this.#listeners.set(event, new Set())
    }
    this.#listeners.get(event).add(listener)
    return () => this.off(event, listener)
  }

  off(event, listener) {
    this.#listeners.get(event)?.delete(listener)
  }

  emit(event, ...args) {
    this.#listeners.get(event)?.forEach(listener => {
      try {
        listener(...args)
      } catch (error) {
        console.error(`Error in listener for ${event}:`, error)
      }
    })
  }

  once(event, listener) {
    const wrapper = (...args) => {
      listener(...args)
      this.off(event, wrapper)
    }
    return this.on(event, wrapper)
  }
}
```

### Debounce Function
```javascript
export function debounce(fn, delayMs) {
  let timeoutId = null

  const debounced = (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      fn(...args)
      timeoutId = null
    }, delayMs)
  }

  debounced.cancel = () => {
    clearTimeout(timeoutId)
    timeoutId = null
  }

  return debounced
}
```

## Best Practices
- Use strict equality (`===`) everywhere; only use `==` when explicitly checking for `null`/`undefined`
- Handle all promise rejections with `.catch()` or `try/catch`
- Avoid mutating function parameters — treat them as read-only
- Keep functions small — under 20 lines ideally, under 50 lines maximum
- Use early returns to reduce nesting and improve readability
- Name boolean variables with `is`, `has`, `should`, `can` prefixes
- Use `Number.isNaN()` instead of global `isNaN()` (which coerces to number)
- Use `Number.isFinite()` for checking finite numbers
- Validate input at function boundaries — throw early with descriptive messages
- Use the `Error` class or subclasses for all errors; avoid throwing strings
- Prefer `for...of` over `forEach` for better control flow (can `break`/`continue`)
- Use `Intl` API for formatting dates, numbers, and strings instead of ad-hoc formatting

## Common Mistakes
- Forgetting that `typeof null === 'object'` (legacy bug)
- Comparing with `==` which coerces types (e.g., `0 == ''` is `true`)
- Mutating objects/arrays passed as function arguments
- Not handling the `undefined` return from `array.find()` when no match is found
- Using `new Array(length)` which creates sparse arrays, not filled arrays
- Assuming `parseInt` defaults to base 10 (always pass radix: `parseInt(str, 10)`)
- Using `delete` on arrays (creates holes) instead of `splice`
- Confusing `null` and `undefined` — they represent different absences of value
- Not handling floating-point precision: `0.1 + 0.2 !== 0.3`
- Forgetting to await inside `map` callback (creates array of promises, not resolved values)
- Mutating state directly in React without using setState

## Libraries
- **lodash** — utility functions for common operations (though modern JS covers most cases)
- **date-fns** — modular date utility library (tree-shakable)
- **immer** — immutable state management with mutable syntax
- **zod** — schema validation with runtime checks
- **nanoid** — tiny, secure URL-friendly unique string ID generator
- **dayjs** — lightweight date library (2kB alternative to moment)
- **axios** — promise-based HTTP client with interceptors
- **uuid** — UUID generation (v1, v4, v7)
- **dotenv** — load environment variables from `.env` files
- **chalk** — terminal string styling with ANSI colors
- **p-limit** — concurrency limiting for async operations
- **fast-deep-equal** — deep equality comparison

## Design Principles
- **KISS (Keep It Simple, Stupid)**: Prefer simple solutions over complex abstractions
- **DRY (Don't Repeat Yourself)**: Extract repeated logic into reusable functions
- **Single Responsibility**: Each function should do one thing well
- **Fail Fast**: Validate inputs and throw early rather than propagating bad data
- **Encapsulation**: Hide implementation details, expose clear APIs
- **Composition over Inheritance**: Build complex behavior by composing small functions

## Coding Standards
- 2-space indentation
- Semicolons required
- Single quotes for strings, backticks for template literals
- Trailing commas in multi-line objects and arrays
- Maximum line length of 100 characters
- One variable declaration per line (`const x = 1; const y = 2;` not `const x = 1, y = 2`)
- Space after keywords (`if`, `for`, `while`, `catch`) and before opening braces
- No space between function name and opening parenthesis
- One blank line between function/class definitions
- Use JSDoc for public APIs: `@param`, `@returns`, `@throws`
- File names: kebab-case for modules, PascalCase for classes, camelCase for utilities

## Memory Management
- Understand garbage collection: JS uses mark-and-sweep; objects are collected when unreachable
- Avoid global variables — they are never garbage collected
- Clear references when done: `arr.length = 0` to clear arrays, nullify object references
- Use WeakMap and WeakSet for caching without preventing garbage collection
- Be careful with closures that capture large objects — they keep the scope alive
- Detach DOM event listeners when removing elements to prevent memory leaks
- Use `AbortController` with `addEventListener` to clean up event listeners
- Avoid retaining large data in module-level variables
- For long-running apps, periodically clear caches and buffers

## Error Handling
- Always use `try/catch` with `async/await`
- Create custom error classes extending `Error`
- Use `Error.cause` for error chaining (ES2022)
- Log errors with sufficient context for debugging
- Never silently catch errors without handling them
- Use `finally` for cleanup code (close files, release resources)
- Throw typed errors for different failure modes
- Add `AggregateError` for multiple errors (e.g., `Promise.allSettled` failures)
- Use global error handlers: `process.on('unhandledRejection')` and `process.on('uncaughtException')`
