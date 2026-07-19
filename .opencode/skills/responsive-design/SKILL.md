---
name: responsive-design
description: Use when building responsive layouts, mobile-first designs, cross-device compatibility, or adaptive interfaces. Covers CSS Grid, Flexbox, media queries, and responsive patterns.
---

# Responsive Design Skill

## Instructions

1. Adopt a mobile-first approach: design and write CSS for the smallest screen size first, then progressively enhance with `min-width` media queries for larger screens.
2. Use a fluid grid system. Define layout columns using relative units (`%`, `fr`, `vw`) rather than fixed pixel values.
3. Set a viewport meta tag: `<meta name="viewport" content="width=device-width, initial-scale=1.0">` on every page.
4. Use CSS Grid for two-dimensional layouts (rows and columns) and Flexbox for one-dimensional layouts (either row or column).
5. Define breakpoints based on content needs, not specific device widths. Common breakpoints: 480px (small mobile), 768px (tablet), 1024px (desktop), 1280px (wide).
6. Use relative units for typography: `rem` for font sizes (root em), `em` for spacing relative to the current font size, `ch` for line length limits.
7. Ensure touch targets are at least 44x44 CSS pixels for interactive elements on touch devices.
8. Use `max-width` with `margin: 0 auto` for centered, responsive containers.
9. Implement responsive images with `srcset` and `sizes` attributes, or use the `<picture>` element for art direction.
10. Use CSS `clamp()` function for fluid typography: `font-size: clamp(1rem, 2.5vw, 2rem)`.
11. Test on real devices, not just browser DevTools device emulation. Test on various screen sizes, orientations, and pixel densities.
12. Optimize for different input methods: touch, mouse, stylus, keyboard. Avoid hover-dependent interactions on touch devices.
13. Use `container queries` (container queries) for component-level responsiveness when the component needs to adapt to its parent container rather than the viewport.
14. Ensure horizontal scrolling does not occur at any viewport width. Use `overflow-x: hidden` sparingly; fix the root cause.
15. Implement responsive navigation patterns: hamburger menu for mobile, horizontal nav for desktop, or priority+ pattern.
16. Use `object-fit` and `object-position` for responsive media in containers.
17. Prefer logical properties (`margin-inline`, `padding-block`) over physical properties (`margin-left`, `padding-top`) for better internationalization support.
18. Use `aspect-ratio` CSS property for responsive media embeds and cards.
19. Implement responsive data tables: use horizontal scroll, hide low-priority columns on small screens, or convert to a stacked card layout.
20. Performance matters: lazy-load offscreen images with `loading="lazy"`, use responsive font sizes to reduce CLS (Cumulative Layout Shift).

## Examples

### Mobile-First Grid Layout
```css
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### Fluid Typography with clamp
```css
h1 {
  font-size: clamp(1.75rem, 4vw + 1rem, 3rem);
  line-height: 1.2;
}

p {
  font-size: clamp(1rem, 1.5vw + 0.5rem, 1.25rem);
  max-width: 70ch;
}
```

### Responsive Card Component
```css
.card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

@media (min-width: 600px) {
  .card {
    flex-direction: row;
    align-items: center;
  }

  .card__image {
    flex: 0 0 200px;
    aspect-ratio: 4 / 3;
    object-fit: cover;
  }

  .card__content {
    flex: 1;
  }
}
```

### Responsive Navigation (Hamburger)
```html
<nav class="nav">
  <button class="nav__toggle" aria-label="Toggle menu">☰</button>
  <ul class="nav__list">
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
    <li><a href="/contact">Contact</a></li>
  </ul>
</nav>
```
```css
.nav__list {
  display: none;
}

.nav__list.is-open {
  display: flex;
  flex-direction: column;
}

@media (min-width: 768px) {
  .nav__toggle {
    display: none;
  }

  .nav__list {
    display: flex;
    flex-direction: row;
    gap: 1rem;
  }
}
```

### Responsive Image with srcset
```html
<img
  src="photo-800.jpg"
  srcset="photo-400.jpg 400w, photo-800.jpg 800w, photo-1200.jpg 1200w"
  sizes="(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw"
  alt="Descriptive alt text"
  loading="lazy"
  decoding="async"
/>
```

### Container Query
```css
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    flex-direction: row;
  }
}
```

### Responsive Table to Cards
```css
@media (max-width: 600px) {
  table, thead, tbody, th, td, tr {
    display: block;
  }

  thead {
    display: none;
  }

  td::before {
    content: attr(data-label);
    font-weight: bold;
    display: inline-block;
    width: 120px;
  }
}
```

## Best Practices

- Start with the smallest viewport and add complexity as screen space increases. Mobile-first naturally produces smaller, more efficient CSS.
- Use CSS custom properties (variables) for design tokens (colors, spacing, fonts) and override them in media queries for theme variations.
- Test responsive layouts with real content, not placeholder text. Content length variations often break layouts.
- Use the `picture` element for art direction (different image crops at different screen sizes), and `srcset` for resolution switching.
- Set `html { font-size: 100%; }` and avoid changing the root font size in media queries, as it breaks browser zoom behavior.
- Use `gap` in both Grid and Flexbox for consistent spacing instead of margins.
- For complex responsive layouts, use CSS Grid template areas and redefine the grid in media queries.
- Use `min-height: 100dvh` (dynamic viewport height) instead of `100vh` to avoid mobile browser chrome issues.
- Implement responsive padding using `clamp()` or CSS variables that change at breakpoints.
- Test touch interactions: swiping, pinching, long-pressing. These are not the same as mouse interactions.
- Consider network conditions: serve appropriately sized images for mobile connections. Use responsive image attributes.
- Use `<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">` for notched devices.
- Avoid fixed heights. Allow content to determine its height for true responsiveness.
- Use `text-overflow: ellipsis` with caution; it can hide important content on small screens.
- Design forms responsively: single column on mobile, multi-column on desktop. Radio buttons and checkboxes need adequate spacing for touch.

## Common Mistakes

- Using fixed pixel widths for layout elements instead of relative units like `%`, `fr`, or `vw`.
- Setting `max-width` without a corresponding `width: 100%` on images, causing overflow.
- Overusing `display: none` to hide content on mobile instead of restructuring the layout.
- Using device-specific breakpoints (iPhone, iPad) instead of content-driven breakpoints.
- Forgetting the viewport meta tag, which causes mobile browsers to render at desktop width.
- Relying solely on emulators without testing on real devices.
- Using `vh` units without accounting for mobile browser toolbar height (use `dvh` instead).
- Creating hamburger menus that are not keyboard accessible or have poor touch targets.
- Ignoring landscape orientation on mobile — content should still be usable and not overly stretched.
- Using `position: fixed` on mobile without handling virtual keyboard issues.
- Not providing responsive images, causing massive download sizes on mobile connections.
- Failing to test with different font sizes (browser zoom), breaking layouts.
- Using hover-only interactions that are inaccessible on touch devices.
- Overcomplicating responsive behavior with too many breakpoints.
- Not respecting user preferences like `prefers-reduced-motion` or `prefers-color-scheme`.

## Libraries and Tools

- **Chrome DevTools Device Emulation**: Built-in responsive testing with device presets and network throttling.
- **Responsively App**: Desktop app that mirrors a URL across multiple viewports simultaneously.
- **Polypane**: Browser for responsive design and development with side-by-side previews.
- **BrowserStack / Sauce Labs**: Cloud-based testing on real devices and browsers.
- **Lighthouse**: Built into Chrome DevTools. Reports on CLS, responsiveness, and mobile friendliness.
- **CSS Grid Generator (layoutit.com)**: Visual tool for creating CSS Grid layouts.
- **Fluid Type Scale Calculator (utopia.fyi)**: Generates fluid type scales and space scales with `clamp()`.
- **Container Query Polyfill**: For browsers that do not yet support container queries.
- **Modern Fluid Typography Calculator**: Tools to generate `clamp()` values for responsive text.
- **PostCSS / Autoprefixer**: Automatically adds vendor prefixes for older browser support.
- **TailwindCSS**: Utility-first CSS framework with built-in responsive variants.
- **Bootstrap / Foundation**: CSS frameworks with responsive grid systems (if project constraints dictate).
- **cssnano**: CSS optimizer that can help keep responsive CSS bundles small.

## Design Principles

1. **Mobile First**: Design for the smallest screen and least capable device first. This forces prioritization of content and creates a progressive enhancement path.
2. **Content Out**: Let content define the layout, not the other way around. Layouts should adapt to content length variations, not clip or overflow.
3. **Progressive Enhancement**: Build a baseline experience that works everywhere, then layer enhanced functionality for capable browsers and larger screens.
4. **Fluid Grids**: Use relative units for all layout dimensions. Grids and columns should flex and adapt to the viewport naturally.
5. **Device Agnosticism**: Design for viewport ranges, not specific devices. Today's iPhone is tomorrow's budget Android.
6. **Performance Budget**: Responsive design must account for network conditions. Serve appropriate assets based on device capabilities and connection speed.
7. **Accessibility Parity**: Responsive design should not reduce accessibility. Keyboard navigation, screen reader support, and touch targets must work at all viewport sizes.
8. **Test Early, Test Often**: Validate responsive behavior throughout development, not as a final step. Catch layout breaks when they are cheap to fix.

## Coding Standards

- Use `min-width` media queries for mobile-first development. Avoid `max-width` queries unless overriding a mobile-first default.
- Write CSS custom properties for all design tokens: `--color-primary`, `--spacing-md`, `--font-size-base`. Override these in media queries or container queries.
- Use logical CSS properties: `margin-inline`, `margin-block`, `padding-inline`, `padding-block`, `border-inline-start` for better internationalization (RTL support).
- Use the `rem` unit for font sizes, `em` for padding/margin relative to font size, `%` for widths, `vw`/`vh` for viewport-relative sizing, `ch` for measure (line length).
- Set `img`, `video`, `iframe`, `embed`, `object` to `max-width: 100%` and `height: auto` by default.
- Use CSS Grid with `auto-fit`/`auto-fill` and `minmax()` for intrinsic responsive grids: `grid-template-columns: repeat(auto-fit, minmax(250px, 1fr))`.
- Implement responsive typography with `clamp()`: `font-size: clamp(1rem, 1rem + 0.5vw, 1.5rem)`.
- Use `@media (hover: hover) and (pointer: fine)` to detect devices with a hover-capable mouse for hover-only interactions.
- Use `@media (prefers-reduced-motion: no-preference)` to conditionally enable animations.
- Set `touch-action: manipulation` on interactive elements to eliminate 300ms tap delay and prevent double-tap zoom.
- Use `scrollbar-gutter: stable` to prevent layout shift when scrollbars appear.
- Implement `content-visibility: auto` on off-screen sections to improve rendering performance.
- Set `interpolate-size: allow-keywords` for smooth height transitions in responsive components.
- Always include `width` and `height` attributes on images to prevent CLS (Cumulative Layout Shift).
- Use `aspect-ratio` CSS property for media containers instead of padding-bottom hacks.
- For responsive SVGs, set `width="100%"` and `height="auto"` with `viewBox` defined.
- Use CSS cascade layers (`@layer`) to manage responsive overrides systematically.
