---
name: typescript
description: Use when writing TypeScript code. Covers types, generics, utility types, strict mode, and patterns.
---

# TypeScript Skill

## Overview
TypeScript is a typed superset of JavaScript that compiles to plain JavaScript. It adds optional static typing, interfaces, generics, and advanced type system features that enable better tooling, safer refactoring, and fewer runtime errors.

## Instructions
- Enable `strict: true` in `tsconfig.json` for maximum type safety
- Prefer `interface` for object type declarations that may be extended; use `type` for unions, intersections, and mapped types
- Use `unknown` instead of `any` when the type truly is not known — it forces type narrowing before use
- Avoid `any` entirely; use `unknown`, `never`, or proper generics instead
- Use `as const` for literal type inference on constants and tuples
- Use `satisfies` operator (TS 4.9+) to validate a type while preserving the inferred literal type
- Leverage `typeof` and `keyof` operators for dynamic type creation
- Use discriminated unions for state machines and complex state shapes
- Use template literal types for string manipulation types
- Write JSDoc for public APIs that are consumed by other teams

## Core Type System

### Primitives and Literals
```tsx
let name: string = 'Alice'
let age: number = 30
let isActive: boolean = true
let id: string | number = 'abc123'
let status: 'idle' | 'loading' | 'success' | 'error' = 'idle'
```

### Interfaces and Types
```tsx
interface User {
  id: string
  email: string
  name?: string  // optional
  readonly createdAt: Date  // immutable after creation
}

type Role = 'admin' | 'user' | 'viewer'

interface AdminUser extends User {
  role: 'admin'
  permissions: string[]
}
```

### Generics
```tsx
// Generic function
function first<T>(arr: T[]): T | undefined {
  return arr[0]
}

// Generic interface
interface ApiResponse<T> {
  data: T
  status: number
  message: string
}

// Generic constraints
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key]
}

// Generic utility component
type Result<T> = { ok: true; value: T } | { ok: false; error: string }
```

### Unions and Intersections
```tsx
// Discriminated union
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rectangle'; width: number; height: number }
  | { kind: 'triangle'; base: number; height: number }

function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle':
      return Math.PI * shape.radius ** 2
    case 'rectangle':
      return shape.width * shape.height
    case 'triangle':
      return (shape.base * shape.height) / 2
  }
}

// Intersection type
type WithId = { id: string }
type WithTimestamp = { createdAt: Date; updatedAt: Date }
type Entity = WithId & WithTimestamp
```

### Mapped Types
```tsx
type Readonly<T> = { readonly [P in keyof T]: T[P] }
type Partial<T> = { [P in keyof T]?: T[P] }
type Required<T> = { [P in keyof T]-?: T[P] }
type Nullable<T> = { [P in keyof T]: T[P] | null }

// Conditional mapped type
type FilterProps<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K]
}
```

### Conditional Types
```tsx
type IsString<T> = T extends string ? true : false
type A = IsString<'hello'>  // true
type B = IsString<42>       // false

// Distributive conditional types
type ToArray<T> = T extends unknown ? T[] : never
type Result = ToArray<string | number>  // string[] | number[]

// infer keyword
type ReturnType<T> = T extends (...args: unknown[]) => infer R ? R : never
type ArrayItem<T> = T extends (infer U)[] ? U : never
```

## Utility Types
- `Partial<T>` — makes all properties optional
- `Required<T>` — makes all properties required
- `Readonly<T>` — makes all properties readonly
- `Pick<T, K>` — selects a subset of properties
- `Omit<T, K>` — removes properties
- `Record<K, V>` — creates an object type with keys K and values V
- `Exclude<T, U>` — removes types from a union
- `Extract<T, U>` — extracts types from a union
- `NonNullable<T>` — removes null and undefined from a type
- `Parameters<T>` — extracts parameter types from a function
- `ReturnType<T>` — extracts return type from a function
- `InstanceType<T>` — extracts instance type from a constructor
- `Awaited<T>` — unwraps promises
- `Uppercase<T>`, `Lowercase<T>`, `Capitalize<T>`, `Uncapitalize<T>` — string case manipulation

## Examples

### Typed API Client
```tsx
interface RequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  url: string
  body?: unknown
  headers?: Record<string, string>
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async request<T>(config: RequestConfig): Promise<T> {
    const response = await fetch(`${this.baseUrl}${config.url}`, {
      method: config.method,
      headers: { 'Content-Type': 'application/json', ...config.headers },
      body: config.body ? JSON.stringify(config.body) : undefined,
    })
    if (!response.ok) throw new ApiError(response.status, await response.text())
    return response.json()
  }

  get<T>(url: string): Promise<T> {
    return this.request<T>({ method: 'GET', url })
  }

  post<T>(url: string, body: unknown): Promise<T> {
    return this.request<T>({ method: 'POST', url, body })
  }
}
```

### Typed Event Emitter
```tsx
type EventMap = {
  userLogin: { userId: string; timestamp: Date }
  userLogout: { userId: string }
  error: { message: string; code: number }
}

class TypedEmitter<T extends Record<string, unknown>> {
  private listeners = new Map<keyof T, Set<(...args: unknown[]) => void>>()

  on<K extends keyof T>(event: K, listener: (payload: T[K]) => void): void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set())
    this.listeners.get(event)!.add(listener as (...args: unknown[]) => void)
  }

  emit<K extends keyof T>(event: K, payload: T[K]): void {
    this.listeners.get(event)?.forEach(listener => listener(payload))
  }

  off<K extends keyof T>(event: K, listener: (payload: T[K]) => void): void {
    this.listeners.get(event)?.delete(listener as (...args: unknown[]) => void)
  }
}

const emitter = new TypedEmitter<EventMap>()
emitter.on('userLogin', payload => console.log(payload.userId))
emitter.emit('userLogin', { userId: '123', timestamp: new Date() })
```

### Branded Types
```tsx
type Brand<T, B> = T & { __brand: B }

type UserId = Brand<string, 'UserId'>
type PostId = Brand<string, 'PostId'>

function getUser(id: UserId): User {
  return db.users.find(id)
}

const uid = 'abc' as UserId
const pid = 'xyz' as PostId

getUser(uid)  // ok
getUser(pid)  // type error
```

## Best Practices
- Always use `strict: true` — it catches null reference errors, improves inference, and enables `noImplicitAny`
- Use `noUncheckedIndexedAccess` to force handling of undefined when accessing index signatures
- Prefer `interface` for public APIs (better error messages, declaration merging) and `type` for internal computed types
- Use `as const` for enum-like constants to get literal types
- Use `satisfies` to validate types without widening
- Extract complex types into reusable type aliases
- Use `never` to represent unreachable code in exhaustive checks
- Use `unknown` in catch clauses: `catch (e: unknown)` then narrow
- Avoid type assertions (`as`) unless necessary; prefer type narrowing and guards
- Use `declare` for ambient declarations or third-party type patches

## Common Mistakes
- Using `any` as a crutch instead of properly typing values
- Overusing type assertions to silence legitimate type errors
- Making everything optional when the data is always present
- Not handling the `| undefined` case from array accesses
- Writing overly complex types that are hard to understand
- Forgetting that `||` returns the first truthy value, which may not be boolean
- Assuming `null` and `undefined` are the same thing
- Using `Function` type instead of a proper function signature
- Not using const assertions on literal types
- Using enums instead of union types (enums have runtime overhead and naming collisions)

## Libraries
- **zod** — runtime schema validation with TypeScript inference
- **ts-pattern** — exhaustive pattern matching for discriminated unions
- **type-fest** — collection of essential TypeScript utility types
- **ts-reset** — improved default types for common APIs
- **@types/node** — type definitions for Node.js
- **tsx** — execute TypeScript files directly (replacement for ts-node)
- **typescript-eslint** — TypeScript-aware linting rules
- **tsup** — bundle TypeScript libraries with esbuild
- **typia** — runtime type validator with superfast performance (generated)
- **valibot** — lightweight schema validation (alternative to zod)

## Design Principles
- **Structural Typing**: TypeScript uses structural (duck) typing — compatibility is based on shape, not name
- **Type Erasure**: All type annotations are removed at compile time — no runtime type information
- **Gradual Adoption**: TypeScript can be adopted incrementally in a JavaScript project
- **Soundness with Escape Hatches**: The type system is mostly sound, but provides `any` and `as` for edge cases
- **Type Inference**: TypeScript infers types when possible — only annotate where inference is insufficient
- **Declaration Files**: Separate implementation from type declarations for library authors

## Coding Standards
- Use arrow functions for callbacks and closures; use `function` declarations for top-level module exports
- Name types with PascalCase, values with camelCase
- Export types alongside their consumers — co-locate types with usage
- Use `import type` and `export type` for type-only imports to avoid bundling issues
- Use `noUnusedLocals` and `noUnusedParameters` to catch dead code
- Prefer `enum` only for numeric enums with reverse mapping needs; use union types otherwise
- Use `Array<T>` instead of `T[]` in complex generic contexts, `T[]` for simple arrays
- Always annotate function return types for public APIs
- Use `readonly` for immutable arrays: `readonly T[]` instead of `T[]`
- Use `satisfies` instead of `as` when validating a value against a type without changing its inferred type

## Advanced Patterns
- **Branded Types**: Create nominal-like types by intersecting with a unique brand to prevent mixing IDs
- **Builder Pattern**: Use typed builder with `this` return types for fluent APIs
- **Exhaustive Matching**: Combine discriminated unions with `never` in a default case
- **Phantom Types**: Add unused type parameters to encode type-level state
- **Type-Level Programming**: Use conditional types, mapped types, and recursive types for complex transformations
- **Dependent Types via Zod**: Use runtime validators that derive TypeScript types for validated data
- **Template Literal Types**: Enforce string patterns at the type level (e.g., route paths, CSS classes)
- **Covariance and Contravariance**: Understand variance for generic types — functions are contravariant in parameters
