---
name: tailwindcss
description: Use when building UIs with TailwindCSS. Covers utility classes, configuration, custom design tokens, responsive variants, and integration with frameworks.
---

# TailwindCSS Skill

## Instructions

1. Install TailwindCSS via npm: `npm install -D tailwindcss @tailwindcss/vite` (or the PostCSS/CLI variant depending on your build tool).
2. Configure `tailwind.config.js` or use `@import "tailwindcss"` in your CSS entry point for v4+.
3. Add the Tailwind directives to your main CSS file: `@tailwind base; @tailwind components; @tailwind utilities;` (v3) or use `@import "tailwindcss"` (v4).
4. Use utility classes directly in your HTML/JSX: `class="flex items-center gap-4 p-4 bg-white rounded-lg shadow-md"`.
5. Leverage Tailwind's responsive prefix system: `sm:`, `md:`, `lg:`, `xl:`, `2xl:` to apply styles at different breakpoints.
6. Use state variants: `hover:`, `focus:`, `active:`, `disabled:`, `focus-visible:`, `group-hover:`, `peer-focus:`.
7. Configure custom design tokens in `tailwind.config.js` under `theme.extend` for colors, fonts, spacing, breakpoints, and more.
8. Extract repeated utility patterns into reusable components or use `@apply` in CSS for shared styles (use sparingly).
9. Use `cn()` or `clsx()` utility to conditionally merge Tailwind classes without conflicts.
10. Leverage the Tailwind CSS IntelliSense VS Code extension for autocomplete, hover previews, and linting.
11. Use `dark:` variant for dark mode support. Configure dark mode strategy in config: `darkMode: "class"` or `darkMode: "media"`.
12. Optimize production builds: Tailwind automatically purges unused styles via content paths in configuration.
13. Use arbitrary values with square brackets for one-off values: `w-[320px]`, `text-[#bada55]`, `top-[calc(100%-2rem)]`.
14. Customize the default theme by overriding values in `theme.extend` rather than replacing entire theme sections.
15. Use `@layer` directives to control CSS cascade order when writing custom CSS alongside Tailwind.
16. Integrate with component libraries: Tailwind works with React, Vue, Angular, Svelte, Next.js, Nuxt, Remix, and Astro.
17. Use `tailwind-merge` or `twMerge` to intelligently merge conflicting Tailwind classes.
18. Define custom variants using the `addVariant` plugin API for complex state combinations.
19. Use container queries via the `@tailwindcss/container-queries` plugin for component-level responsiveness.
20. Write plugin-based animations, utilities, and components using Tailwind's plugin API for reusable design system extensions.

## Examples

### Basic Responsive Card
```jsx
<div className="mx-auto max-w-sm rounded-lg border border-gray-200 bg-white p-6 shadow-sm md:max-w-2xl md:p-8 lg:max-w-4xl">
  <h2 className="mb-2 text-xl font-bold text-gray-900 md:text-2xl">
    Card Title
  </h2>
  <p className="mb-4 text-gray-600">
    This card adapts its padding, max-width, and typography at different breakpoints.
  </p>
  <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
    Learn More
  </button>
</div>
```

### Responsive Grid Layout
```jsx
<div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  {items.map(item => (
    <div key={item.id} className="rounded-lg bg-white p-4 shadow">
      <h3 className="text-lg font-semibold">{item.title}</h3>
      <p className="mt-1 text-sm text-gray-500">{item.description}</p>
    </div>
  ))}
</div>
```

### Dark Mode Toggle
```jsx
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 min-h-screen transition-colors">
  <header className="border-b border-gray-200 dark:border-gray-700 p-4">
    <button
      onClick={toggleDark}
      className="rounded-md p-2 hover:bg-gray-100 dark:hover:bg-gray-800"
      aria-label="Toggle dark mode"
    >
      {isDark ? <SunIcon /> : <MoonIcon />}
    </button>
  </header>
</div>
```

### Custom Config with Extend
```js
// tailwind.config.js
export default {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Cabinet Grotesk", "sans-serif"],
      },
      spacing: {
        18: "4.5rem",
        88: "22rem",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
```

### Class Merge Utility
```jsx
import { twMerge } from "tailwind-merge";
import { clsx } from "clsx";

export function cn(...classes) {
  return twMerge(clsx(...classes));
}

// Usage
<button
  className={cn(
    "rounded-md px-4 py-2 font-medium focus:outline-none focus-visible:ring-2",
    variant === "primary" && "bg-blue-600 text-white hover:bg-blue-700",
    variant === "secondary" && "bg-gray-100 text-gray-900 hover:bg-gray-200",
    disabled && "cursor-not-allowed opacity-50",
    className,
  )}
>
  {children}
</button>
```

### Custom Plugin
```js
// tailwind.config.js
import plugin from "tailwindcss/plugin";

export default {
  plugins: [
    plugin(({ addUtilities, addVariant, addComponents, theme }) => {
      addUtilities({
        ".text-balance": { "text-wrap": "balance" },
        ".scrollbar-hide": {
          "-ms-overflow-style": "none",
          "scrollbar-width": "none",
          "&::-webkit-scrollbar": { display: "none" },
        },
      });

      addVariant("not-first", "&:not(:first-child)");
      addVariant("not-last", "&:not(:last-child)");
    }),
  ],
};
```

### Container Query Usage
```jsx
<div className="@container">
  <div className="@md:flex @md:items-center @md:gap-6">
    <img className="@md:w-48 @md:shrink-0 rounded-lg" src="..." alt="" />
    <div className="mt-4 @md:mt-0">
      <h2 className="text-xl @md:text-2xl font-bold">Title</h2>
      <p className="mt-2 text-gray-600">Description</p>
    </div>
  </div>
</div>
```

## Best Practices

- Prefer utility classes over custom CSS. If you find yourself repeating the same combination, extract a component, not a CSS class.
- Use `@apply` sparingly. It creates a layer of indirection that defeats the purpose of utility-first CSS. Only use it in rare cases like third-party library overrides.
- Configure your content paths explicitly in `tailwind.config.js` to ensure proper purging in production.
- Use design tokens from `theme.extend` for consistent branding. Avoid arbitrary values for colors and spacing that should be part of the design system.
- Install `prettier-plugin-tailwindcss` to automatically sort classes according to the recommended order.
- Leverage the `group` and `peer` variants for parent/child and sibling interactions instead of writing custom CSS.
- Use `dark:` variants for dark mode instead of creating separate dark-mode CSS files.
- Use responsive variants consistently: build mobile-first and add `sm:`, `md:`, etc. for larger screens.
- For complex components, compose small utility classes rather than writing large blocks of custom CSS.
- Use `size-*` utilities (`size-4`, `size-6`) for equal width/height on icons and avatars.
- Use `inset-*` and `**-auto` utilities aggressively — they often eliminate the need for custom positioning CSS.
- Use Tailwind's `safelist` option in config if you dynamically construct class names that might be purged.
- Learn the default spacing scale — using consistent spacing creates visual rhythm. The scale is based on 4px increments (0.25rem).
- Use `text-balance` utility for balanced headline wrapping on headings.
- Use Tailwind Play (play.tailwindcss.com) for quickly prototyping and sharing configurations.

## Common Mistakes

- Using `@apply` everywhere, recreating the CSS-in-CSS pattern that Tailwind is designed to avoid.
- Forgetting to configure content paths, causing all styles to be purged in production.
- Overusing arbitrary values (`h-[calc(100vh-64px)]`) instead of defining proper theme tokens.
- Mixing Tailwind classes with inline styles, creating maintenance confusion.
- Not using responsive variants and instead writing custom media queries in CSS files.
- Nesting Tailwind classes with template literals instead of using `clsx` or `cn()` utilities.
- Applying Tailwind classes to elements that should be styled via a parent (e.g., not using `group` and `group-hover`).
- Using `!important` for overrides instead of understanding Tailwind's specificity system.
- Creating overly long class strings (50+ classes) on a single element. Consider component extraction.
- Not utilizing the `dark:` prefix and instead manually managing dark mode class switches.
- Using negative margins extensively — Tailwind's `gap` and space utilities should cover most spacing needs.
- Ignoring the `cursor-pointer` utility (Tailwind does not add it to buttons by default).
- Adding Tailwind to a project that already has a mature CSS architecture without a migration strategy.
- Not using the `@tailwindcss/typography` plugin for prose content (blog posts, articles).
- Assuming Tailwind classes work in dynamically concatenated strings; use `safelist` or full class names.
- Not leveraging the `@tailwindcss/forms` plugin for consistent form element styling.

## Libraries and Tools

- **tailwindcss**: The core utility-first CSS framework.
- **@tailwindcss/vite**: Official Vite plugin for Tailwind v4.
- **@tailwindcss/postcss**: PostCSS plugin for Tailwind.
- **@tailwindcss/typography**: Prose styling plugin for rich text content (blogs, documentation).
- **@tailwindcss/forms**: Form reset and styling plugin for consistent cross-browser form elements.
- **@tailwindcss/container-queries**: Container query support with `@container` and `@md` variants.
- **tailwind-merge**: Utility to intelligently merge conflicting Tailwind classes.
- **clsx**: Conditional class name construction utility.
- **prettier-plugin-tailwindcss**: Prettier plugin that automatically sorts Tailwind classes.
- **tailwindcss-animate**: Animation plugin with predefined keyframes for common animations.
- **tailwindcss-react-aria**: Tailwind variants for React Aria components.
- **Headless UI**: Unstyled accessible components that pair perfectly with Tailwind.
- **Radix UI**: Unstyled component primitives that work with Tailwind styling.
- **shadcn/ui**: Component library built on Radix UI and TailwindCSS.
- **Tailwind UI**: Official, premium component templates by the Tailwind team.
- **Tailwind Play**: Online playground for prototyping with Tailwind.
- **Tailwind CSS IntelliSense** (VS Code): Autocomplete, linting, and hover previews.
- **Tailwind Color Shades Generator**: Tools to generate color scales from a single hex value.
- **Tailwind Gradient Generator**: Visual gradient builder using Tailwind colors.

## Design Principles

1. **Utility-First**: Build designs using small, composable utility classes rather than semantic CSS classes. This promotes consistency and reduces CSS bloat.
2. **Constraint-Based Design**: Use the predefined design system (spacing scale, color palette, typography scale) rather than arbitrary values. Constraints breed creativity and consistency.
3. **Composition over Abstraction**: Compose behavior from small utility classes instead of creating abstractions that hide implementation details.
4. **Responsive by Default**: Every utility has a responsive variant. Mobile-first responsive design is built into the framework's DNA.
5. **Design Systems as Configuration**: Treat `tailwind.config.js` as the single source of truth for design tokens. Colors, fonts, spacing, and breakpoints should all be defined there.
6. **Elimination of Context Switching**: Keep HTML structure and styling in the same file. No switching between HTML and CSS files, reducing cognitive load.
7. **Production-First Optimization**: Unused styles are automatically purged in production builds, resulting in minimal CSS bundles.
8. **Progressive Enhancement**: Start with base styles in `@tailwind base`, add component styles in `@tailwind components`, and finish with utilities.

## Coding Standards

- Order Tailwind classes according to the Prettier plugin's recommended order: layout, flexbox/grid, spacing, sizing, typography, visuals, interactivity, pseudo-class variants, responsive variants.
- Use consistent class ordering within a project. `prettier-plugin-tailwindcss` enforces this automatically.
- Use the `cn()` utility (combining `clsx` and `tailwind-merge`) for all conditional class composition in React components.
- Configure `tailwind.config.js` with `content` paths pointing to all files that contain class names.
- Design tokens (colors, fonts, spacing) must be defined in `theme.extend` or `theme` in the config, not as arbitrary values.
- Use semantic color names in the design system (e.g., `primary`, `danger`, `success`) rather than generic color names.
- Prefer framework integrations: use `@tailwindcss/vite` for Vite projects, `@tailwindcss/postcss` for Webpack, etc.
- Use `className` props consistently in React components to allow composition and overrides.
- Define custom animations as keyframes in `theme.extend.animation` and `theme.extend.keyframes`.
- Use the `group` utility and `group-hover:` / `group-focus:` variants for parent-child hover effects.
- Use the `peer` utility and `peer-focus:` / `peer-disabled:` variants for sibling-dependent styling.
- Use Tailwind's `has-` variant (`has-[:checked]:`) for styling parent elements based on child state.
- Use `*:` variant for styling all direct children: `<ul className="*:rounded-md *:border">`.
- Use `max-w-*` utilities for content containers instead of custom width classes.
- Use `min-h-dvh` over `min-h-screen` for better mobile browser behavior.
- Ensure all interactive elements have focus styles using `focus-visible:ring-2 focus-visible:ring-offset-2`.
- Use `aria-*` variants when available: `aria-checked:`, `aria-expanded:`, `aria-selected:`, `aria-invalid:`.
- Use `data-*` variants for custom data attribute states: `data-[state=open]:`.
- Use the `not-*` variant for negation: `not:first-child:mt-4`.
- When using component libraries with Tailwind, ensure `content` paths include the library's source files.
