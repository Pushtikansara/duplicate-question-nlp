---
name: react
description: Use when building user interfaces with React. Covers components, hooks, state management, performance optimization, and React ecosystem.
---

# React Skill

## Overview
React is a declarative, component-based JavaScript library for building user interfaces. Developed by Meta, it enables developers to create reusable UI components that efficiently update and render in response to data changes.

## Instructions
- Always use functional components with hooks; avoid class components unless maintaining legacy code
- Keep components small and focused on a single responsibility
- Use TypeScript with React for type safety and better developer experience
- Prefer composition over inheritance for sharing logic between components
- Lift state up to the nearest common ancestor when multiple children need shared state
- Use React Developer Tools for debugging component trees and performance
- Write unit tests with React Testing Library and Vitest/Jest
- Follow the principle of least privilege for state — keep state as local as possible

## Core Concepts

### Components
- Components are the fundamental building blocks in React
- Every component should be a pure function of its props
- Component names must be PascalCase
- Export components as default exports only when using lazy loading; prefer named exports otherwise
- Extract reusable UI into separate components early

### JSX
- JSX is syntactic sugar for `React.createElement` calls
- Use `className` instead of `class`, `htmlFor` instead of `for`
- Self-close tags that have no children: `<Component />`
- Wrap multi-line JSX in parentheses to avoid automatic semicolon insertion issues
- Keys must be stable, unique, and primitive — avoid using array indices as keys

### Hooks
- Only call hooks at the top level of a component or custom hook
- Only call hooks from React functions (components or custom hooks)
- Custom hooks should start with `use` prefix
- `useState` for local component state; use functional updates when new state depends on previous
- `useEffect` for side effects; always specify dependencies and clean up subscriptions
- `useMemo` and `useCallback` only when profiling shows a performance issue
- `useRef` for mutable values that persist across renders without causing re-renders
- `useContext` for consuming context values; create custom hooks for each context consumer
- `useReducer` for complex state logic involving multiple sub-values or transitions

### State Management
- Start with local state using `useState` and `useReducer`
- Use Context API for shared state that changes infrequently
- Consider Zustand, Jotai, or Redux Toolkit for complex global state
- Keep state normalized to avoid duplication and synchronization issues
- Derive computed values with `useMemo` instead of storing them in state
- Use state reducers for predictable state transitions

### Performance Optimization
- Profile before optimizing — never optimize prematurely
- `React.memo` to prevent unnecessary re-renders of pure components
- `useMemo` to memoize expensive computations
- `useCallback` to memoize callback functions passed to memoized children
- Virtualize long lists with `react-window` or `react-virtuoso`
- Code-split with `React.lazy` and `Suspense`
- Use `React.Fragment` (`<>...</>`) to avoid extra DOM nodes
- Avoid inline object/function creation in render methods

## Examples

### Basic Component
```tsx
interface ButtonProps {
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary'
}

export function Button({ label, onClick, variant = 'primary' }: ButtonProps) {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick}>
      {label}
    </button>
  )
}
```

### Custom Hook
```tsx
import { useState, useEffect } from 'react'

interface FetchState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

export function useFetch<T>(url: string): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    let cancelled = false
    setState(prev => ({ ...prev, loading: true }))

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        if (!cancelled) setState({ data, loading: false, error: null })
      })
      .catch(error => {
        if (!cancelled) setState({ data: null, loading: false, error }))
      }

    return () => { cancelled = true }
  }, [url])

  return state
}
```

### Form with useReducer
```tsx
interface FormState {
  email: string
  password: string
  errors: Record<string, string>
}

type FormAction =
  | { type: 'SET_FIELD'; field: string; value: string }
  | { type: 'SET_ERRORS'; errors: Record<string, string> }
  | { type: 'RESET' }

function formReducer(state: FormState, action: FormAction): FormState {
  switch (action.type) {
    case 'SET_FIELD':
      return { ...state, [action.field]: action.value }
    case 'SET_ERRORS':
      return { ...state, errors: action.errors }
    case 'RESET':
      return { email: '', password: '', errors: {} }
    default:
      return state
  }
}
```

## Best Practices
- Keep components under 100 lines; extract larger ones into smaller pieces
- Use absolute imports configured via `tsconfig` paths to avoid deep relative imports
- Co-locate tests, styles, and stories with their component files
- Use `data-testid` attributes for test targeting instead of CSS selectors
- Avoid prop drilling by composing components or using context
- Write error boundaries at the route or feature level to catch rendering errors
- Use `StrictMode` in development to detect side-effect problems
- Prefer `async/await` over promise chains in effects
- Use `useId()` for generating unique IDs for accessibility attributes

## Common Mistakes
- Mutating state directly instead of using setState
- Omitting dependencies in useEffect leading to stale closures
- Using array index as key when the list can be reordered
- Creating components inside other components (causes remount on every render)
- Overusing state for values that can be derived from props
- Calling hooks conditionally or inside loops
- Forgetting to clean up subscriptions, timers, or event listeners in useEffect
- Using inline arrow functions in JSX props on components wrapped with React.memo

## Libraries
- **react-router-dom** — declarative client-side routing
- **react-hook-form** — performant form management with validation
- **tanstack/react-query** — server state management and caching
- **zustand** — minimal global state management
- **react-hot-toast** — lightweight toast notifications
- **react-dropzone** — file upload with drag-and-drop
- **framer-motion** — declarative animations and gestures
- **react-router** — standard routing library
- **react-i18next** — internationalization
- **react-virtuoso** — virtualized lists and grids
- **react-testing-library** — testing utilities
- **storybook** — component development environment

## Design Principles
- **Declarative**: Describe what the UI should look like; React handles the DOM updates
- **Component-Based**: Encapsulate logic and presentation in reusable units
- **Unidirectional Data Flow**: Data flows down through props; events flow up through callbacks
- **Composition Over Configuration**: Build complex UIs by composing simple components
- **Controlled Components**: Let React manage form element state via value + onChange
- **Single Source of Truth**: Each piece of data has one authoritative source

## Coding Standards
- Use 2-space indentation
- Semicolons required
- Single quotes for strings, backticks for template literals
- Trailing commas in multi-line objects and arrays
- Sort imports: external first, then internal, then styles
- One component per file (default), with related hooks and utilities co-located
- Use `const` for functions defined in the module scope
- File names match exports: `Button.tsx` exports `Button`
- TypeScript strict mode enabled
- Prefer `interface` over `type` for describing object shapes (public API); use `type` for unions and intersections

## Accessibility
- Use semantic HTML elements: `<nav>`, `<main>`, `<aside>`, `<button>`, etc.
- Every image must have `alt` text
- Form elements must have associated `<label>` elements
- Use `aria-*` attributes when semantic HTML is insufficient
- Ensure color contrast meets WCAG AA standards
- Support keyboard navigation with visible focus indicators
- Manage focus programmatically with `useRef` and `useEffect`
- Announce dynamic content changes with `aria-live` regions
- Use `useAnnouncement()` pattern for screen reader notifications

## Testing Philosophy
- Test behavior, not implementation details
- Use `@testing-library/react` for rendering and querying
- Prefer `getByRole` over `getByTestId` for accessible queries
- Test user interactions with `userEvent` instead of `fireEvent`
- Write integration tests for critical user flows
- Mock external API calls at the network level with MSW
- Use snapshot tests sparingly — prefer assertion-based tests
- Aim for 80%+ coverage on business logic and user flows
