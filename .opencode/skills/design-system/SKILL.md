---
name: design-system
description: Use when creating or maintaining design systems, component libraries, style guides, or design tokens. Covers design token architecture, component APIs, documentation, and versioning.
---

# Design System Skill

## Instructions

1. Start by auditing existing UI components and patterns to identify inconsistencies
2. Define design tokens as the foundational layer (colors, typography, spacing, shadows, breakpoints)
3. Adopt atomic design methodology: atoms -> molecules -> organisms -> templates -> pages
4. Design components with composability and reusability as primary goals
5. Document every component with usage guidelines, code examples, and visual examples
6. Establish a versioning strategy for the design system independent of consuming applications
7. Build theme support from the start using CSS custom properties or design tokens
8. Create comprehensive component API documentation with prop types and default values
9. Implement accessibility foundations at the component level, not per-application
10. Establish a contribution process for adding or modifying components

## Examples

1. Design tokens: Define colors as CSS custom properties (--color-primary-500: #3B82F6) with semantic aliases (--color-button-primary-bg: var(--color-primary-500))
2. Atomic design: Button (atom) -> FormField (molecule) -> SignInForm (organism) -> DashboardPage (template) -> App (page)
3. Component API: `<Button variant="primary" size="md" disabled icon={<Icon />}>Click</Button>`
4. Theme tokens: Define light and dark theme values using CSS custom properties with data-attribute scoping
5. Storybook documentation: Write MDX stories with controls, actions, and accessibility addon
6. Versioning: Use semantic versioning (major.minor.patch) for design system releases
7. Component composition: Build complex components from simpler ones (Select uses Popover + List + Input)
8. Design token structure: global tokens -> alias tokens -> component-specific tokens
9. Cross-platform tokens: Define tokens once and generate platform-specific outputs (CSS, JS, Swift, Kotlin)
10. Documentation: Maintain usage guidelines, code examples, and visual examples for every component

## Examples

1. Design token structure: `color.primary.500` -> `--color-primary-500: #3B82F6` -> `--button-primary-bg: var(--color-primary-500)`
2. Atomic design: Button (atom) -> Input + Label + ErrorText (molecule) -> LoginForm (organism) -> SettingsPage (template)
3. Component API: `<Select options={items} value={selected} onChange={handleChange} placeholder="Choose..." disabled={isLoading} />`
4. Storybook story: `export const Primary: Story = { args: { variant: 'primary', children: 'Click Me', size: 'md' } }`
5. Theme tokens: `--color-bg-primary: var(--color-neutral-50)` for light, `--color-bg-primary: var(--color-neutral-900)` for dark
6. Component composition: `<Dialog><DialogTrigger><Button>Open</Button></DialogTrigger><DialogContent><DialogTitle>Title</DialogTitle></DialogContent></Dialog>`
7. Token pipeline: Figma Tokens plugin -> JSON tokens -> Style Dictionary -> CSS/JS/Swift/Kotlin outputs
8. Documentation: Storybook with Controls, Actions, Viewport, Accessibility, and Docs addons
9. Versioning: Release v2.0.0 for breaking changes, v2.1.0 for new features, v2.1.1 for patches
10. Contribution process: RFC -> Design review -> Component implementation -> Code review -> Documentation -> Release

## Examples

1. Design token structure: `color.primary.500: #3B82F6` -> `--color-primary-500: #3B82F6` -> `--button-bg: var(--color-primary-500)`
2. Atomic design hierarchy: Button (atom) -> ButtonGroup (molecule) -> Toolbar (organism) -> EditorPage (template)
3. Component API: `<Button variant="secondary" size="sm" leftIcon={<Icon />} loading>Save</Button>`
4. Storybook story: `export const Primary: Story = { args: { variant: 'primary', children: 'Submit', size: 'lg', disabled: false } }`
5. Theme switching: `[data-theme="dark"] { --color-bg: #1a1a2e; --color-text: #e0e0e0; }`
6. Token generation: Style Dictionary transforms `color.primary.500` into CSS, JS, Swift, and Kotlin formats
7. Component composition: `<Select><SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger><SelectContent><SelectItem value="1">Option 1</SelectItem></SelectContent></Select>`
8. Documentation: Storybook MDX with `<Meta>`, `<Story>`, `<Canvas>`, and `<Controls>` for interactive examples
9. Versioning: `@acme/design-system@2.1.0` with changelog entries for each release
10. Contribution: RFC template with problem statement, proposed solution, API design, and migration guide

## Best Practices

1. Design tokens should be platform-agnostic and generated from a single source of truth
2. Components should be composable, not monolithic — prefer composition over configuration
3. Every component must support all interactive states: default, hover, active, focus, disabled, loading
4. Use semantic versioning and maintain a changelog for the design system package
5. Document the why, not just the how — explain design rationale for each component
6. Test components in isolation and in integration with real application code
7. Support both light and dark themes from the start using CSS custom properties
8. Keep component APIs minimal and predictable — avoid prop explosion
9. Use forwardRef and spread props for flexibility and composition
10. Write accessibility tests for every component using jest-axe or testing-library

## Common Mistakes

1. Building components that are too rigid and don't compose well with other components
2. Creating too many component variations instead of using composition patterns
3. Neglecting to document component APIs, leading to misuse and confusion
4. Failing to version the design system, causing breaking changes without notice
5. Building components without accessibility support, requiring later retrofitting
6. Using hardcoded values instead of design tokens, breaking theming capabilities
7. Creating components that only work in one framework without cross-platform consideration
8. Over-engineering components with too many props and configuration options
9. Ignoring performance implications of component architecture
10. Not testing components across different browsers and devices

## Libraries

1. Storybook - Component documentation and development environment
2. Style Dictionary - Design token transformation and generation
3. Radix UI - Accessible, unstyled React primitives for building design systems
4. Reach UI - Accessible React component primitives
5. Zag.js - Finite state machine driven UI components
6. Stitches - CSS-in-JS with design token support and theming
7. TailwindCSS - Utility-first CSS framework for rapid design system implementation
8. Theme UI - Constraint-based design system library for React
9. Chakra UI - Component library with built-in design system principles
10. System UI - Design system specification and token standardization

## Design Principles

1. Consistency: Every component should look and behave the same way across the entire system
2. Composability: Components should be small, focused, and combinable to create complex UIs
3. Predictability: Component APIs should follow consistent patterns and naming conventions
4. Accessibility: Every component must meet WCAG 2.2 AA standards by default
5. Performance: Components should be tree-shakeable and not bloat application bundles
6. Flexibility: Support theming and customization without breaking core functionality
7. Documentation: Every component must have clear documentation with examples
8. Backward compatibility: Avoid breaking changes; deprecate gradually with migration paths
9. Testability: Components should be easy to test in isolation
10. Discoverability: Components should be easy to find and understand through documentation

## Coding Standards

1. Use TypeScript for all component code with strict type checking enabled
2. Export components with both named and default exports for flexibility
3. Use CSS custom properties for all design tokens to enable runtime theming
4. Follow atomic design file structure: atoms/, molecules/, organisms/, templates/
5. Write unit tests for every component covering all interactive states
6. Use forwardRef for all interactive components to support ref forwarding
7. Spread remaining props to the root DOM element for flexibility
8. Use React.Children and cloneElement sparingly; prefer render props or composition
9. Name component files with PascalCase and test files with .test.tsx suffix
10. Export TypeScript types and interfaces for all component props
