---
name: accessibility
description: Use when ensuring web accessibility (a11y) compliance. Covers WCAG guidelines, ARIA, semantic HTML, keyboard navigation, screen reader support, and accessibility testing.
---

# Accessibility (a11y) Skill

## Instructions

1. Always start by auditing the current state using automated tools (axe-core, Lighthouse, WAVE) and manual testing with screen readers (NVDA, VoiceOver, JAWS).
2. Follow the WCAG 2.2 AA standard as the minimum compliance level. Aim for AAA where feasible.
3. Ensure all interactive elements are keyboard accessible. Every focusable element must have a visible focus indicator.
4. Use semantic HTML elements (`<nav>`, `<main>`, `<header>`, `<footer>`, `<section>`, `<article>`, `<aside>`, `<button>`, `<a>`) instead of generic `<div>` and `<span>` with ARIA roles.
5. Provide text alternatives for non-text content: `alt` attributes on images, transcripts for audio, captions for video.
6. Manage focus order logically. Use `tabindex="0"` for elements that should be focusable, `tabindex="-1"` for programmatic focus, and avoid positive `tabindex` values.
7. Implement skip navigation links as the first focusable element on the page.
8. Ensure color contrast ratios meet WCAG standards: 4.5:1 for normal text, 3:1 for large text (18px+ or 14px+ bold), and 3:1 for UI components and graphical objects.
9. Do not convey information through color alone. Use icons, patterns, text labels, or underlines as supplementary indicators.
10. Use ARIA landmarks (`role="banner"`, `role="navigation"`, `role="main"`, `role="complementary"`, `role="contentinfo"`) to define page regions when HTML5 semantic elements are not sufficient.
11. Ensure all form inputs have associated `<label>` elements, either via `for`/`id` association or by wrapping.
12. Provide clear error messages for form validation that programmatically associate with the input using `aria-describedby` or `aria-errormessage`.
13. Use `aria-live` regions for dynamic content updates (polite for non-urgent, assertive for urgent).
14. Test with browser zoom up to 400% and ensure content does not overlap or clip.
15. Ensure all functionality is operable through a keyboard interface without specific timings for individual keystrokes.
16. Avoid or provide alternatives for content that flashes more than three times per second (seizure risk).
17. Use `prefers-reduced-motion` media query to disable or simplify animations for users with vestibular disorders.
18. Write descriptive link text that makes sense out of context. Avoid "click here" or "read more".
19. Ensure custom widgets follow ARIA authoring practices for their specific pattern (dialog, tabpanel, accordion, etc.).
20. Conduct user testing with people who have disabilities to validate accessibility implementation.

## Examples

### Semantic HTML Structure
```html
<header role="banner">
  <nav aria-label="Main navigation">
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/about">About</a></li>
    </ul>
  </nav>
</header>
<main role="main">
  <h1>Page Title</h1>
  <section aria-labelledby="section-heading">
    <h2 id="section-heading">Section Title</h2>
    <p>Content here.</p>
  </section>
</main>
<footer role="contentinfo">
  <p>&copy; 2026 Company Name</p>
</footer>
```

### Accessible Form with Error Handling
```html
<div class="form-field">
  <label for="email">Email address</label>
  <input
    type="email"
    id="email"
    name="email"
    aria-describedby="email-hint email-error"
    aria-invalid="true"
    autocomplete="email"
  />
  <p id="email-hint" class="hint">We will never share your email.</p>
  <p id="email-error" class="error" role="alert">
    Please enter a valid email address.
  </p>
</div>
```

### Skip Navigation Link
```html
<a href="#main-content" class="skip-link">Skip to main content</a>
<header>...</header>
<main id="main-content" tabindex="-1">
  <!-- main content -->
</main>
```

### Accessible Dialog with Focus Trap
```html
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
>
  <h2 id="dialog-title">Confirm Deletion</h2>
  <p id="dialog-desc">This action cannot be undone.</p>
  <button id="confirm-btn">Confirm</button>
  <button id="cancel-btn">Cancel</button>
</div>
```

### prefers-reduced-motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### Accessible Icon Button
```html
<button aria-label="Close dialog">
  <svg aria-hidden="true" focusable="false" width="24" height="24">
    <path d="M6 6l12 12M18 6l-12 12" stroke="currentColor" stroke-width="2"/>
  </svg>
</button>
```

## Best Practices

- Write HTML with accessibility in mind from the start. Retrofitting accessibility is significantly more expensive.
- Use the accessibility tree (browser dev tools) to verify that assistive technologies receive the correct information.
- Test with real screen readers: NVDA (Windows, free), VoiceOver (macOS/iOS, built-in), JAWS (Windows, most popular).
- Use `aria-hidden="true"` on decorative icons and `focusable="false"` on SVG elements to hide them from screen readers.
- Ensure custom components have appropriate roles, states, and properties according to the ARIA design pattern specification.
- Implement visible focus indicators that are at least 2px thick and have a 3:1 contrast ratio against the background.
- Use `aria-expanded` and `aria-controls` on toggle buttons that show/hide content.
- Use proper heading hierarchy (h1-h6) without skipping levels. Never use headings for visual styling only.
- Provide captions and transcripts for all video and audio content.
- Ensure touch targets are at least 44x44 CSS pixels (WCAG 2.5.8).
- Test keyboard navigation: Tab through all interactive elements, use Enter/Space to activate, Escape to close, Arrow keys for navigation widgets.
- Use `lang` attribute on the `<html>` element and on content that changes language.
- Implement `aria-current` for the current page in navigation (page, step, location, date, time, true).
- Use `status` role (or `aria-live="polite" aria-atomic="true"`) for status messages that should be announced.
- Ensure PDFs and other downloadable documents are accessible.

## Common Mistakes

- Using `aria-label` on non-interactive elements or elements that don't map to the accessibility API.
- Overusing ARIA roles when semantic HTML would suffice (e.g., `role="button"` on a `<div>` instead of using `<button>`).
- Removing focus outlines without providing an alternative focus indicator.
- Using `aria-hidden="true"` on parent elements containing focusable content, which traps keyboard users.
- Setting `tabindex` values higher than 0, which creates an illogical tab order.
- Forgetting to manage focus in single-page applications when content changes without a page reload.
- Providing `alt` text for decorative images or missing `alt` text for informative images.
- Using color as the sole differentiator for links, errors, or status indicators.
- Building custom form controls without implementing full keyboard interaction patterns.
- Ignoring the reading order in CSS: visually repositioned content may be read in a different order by screen readers.
- Using `placeholder` attributes as the sole label for form inputs; placeholders disappear on input and fail contrast requirements.
- Creating modals without focus trapping, causing focus to escape behind the overlay.
- Not testing with actual assistive technology, relying only on automated tools.
- Overriding browser default focus styles with `outline: none` globally.
- Using `title` attribute as a substitute for proper labeling.

## Libraries and Tools

- **axe-core**: Browser extension and CLI tool for automated accessibility testing. Integrates with Cypress, Playwright, and Jest.
- **Lighthouse**: Built into Chrome DevTools. Automated auditing for performance, accessibility, SEO, and more.
- **WAVE**: Web Accessibility Evaluation Tool by WebAIM. Browser extension for visual accessibility feedback.
- **NVDA**: Free, open-source screen reader for Windows. Essential for testing.
- **VoiceOver**: Built-in screen reader on macOS and iOS. Test with Safari.
- **JAWS**: Most popular commercial screen reader for Windows.
- **Accessibility Insights**: Microsoft's tool for guided accessibility testing.
- **Pa11y**: Automated accessibility testing toolkit that runs in CI/CD pipelines.
- **react-axe**: React-specific accessibility auditing library for development.
- **eslint-plugin-jsx-a11y**: ESLint plugin that enforces accessibility best practices in JSX.
- **@testing-library/jest-dom**: Custom Jest matchers including `toBeInTheDocument`, `toHaveAttribute`, and `toBeVisible`.
- **focus-trap-react**: Focus trapping utility for modals, dialogs, and sidebars.
- **react-remove-scroll**: Prevents background scrolling when a modal is open.
- **Downshift**: Accessible autocomplete, combobox, and select components.
- **Reach UI / Radix UI / Ariakit**: Accessible, unstyled component primitives.
- **Storybook a11y addon**: Accessibility testing within Storybook.
- **Colour Contrast Analyser (CCA)**: Desktop tool for checking color contrast.

## Design Principles

1. **Perceivable**: Information and user interface components must be presentable to users in ways they can perceive. This means providing text alternatives, captions, and ensuring content can be presented in different ways without losing meaning.
2. **Operable**: User interface components and navigation must be operable. This requires keyboard accessibility, enough time to read and use content, avoiding seizure-causing content, and providing navigable interfaces.
3. **Understandable**: Information and the operation of the user interface must be understandable. Text must be readable, content must appear and operate in predictable ways, and users must be able to avoid and correct errors.
4. **Robust**: Content must be robust enough to be interpreted reliably by a wide variety of user agents, including assistive technologies. This means maximizing compatibility with current and future tools.
5. **Progressive Enhancement**: Build a solid, accessible baseline experience first, then layer enhanced functionality on top. Ensure core functionality works without JavaScript.
6. **Inclusive by Design**: Accessibility is not a feature or a checklist. It is a fundamental aspect of user experience design. Designing for edge cases improves the experience for everyone.
7. **User Control**: Users should have control over their experience. Provide options to reduce motion, pause animations, adjust font sizes, and customize contrast.

## Coding Standards

- All JSX elements must have accessible names. Use `eslint-plugin-jsx-a11y` to enforce rules: `alt-text`, `anchor-has-content`, `aria-props`, `aria-role`, `click-events-have-key-events`, `heading-has-content`, `html-has-lang`, `iframe-has-title`, `img-redundant-alt`, `label-has-associated-control`, `mouse-events-have-key-events`, `no-access-key`, `no-autofocus`, `no-distracting-elements`, `no-onchange`, `no-redundant-roles`, `role-has-required-aria-props`, `scope`, `tabindex-no-positive`.
- Use TypeScript with strict null checks to prevent runtime errors that could break accessibility.
- Ensure all interactive elements (`<button>`, `<a>`, `<input>`, `<select>`, `<textarea>`) have visible focus styles.
- Set `:focus-visible` for keyboard-only focus indicators and `:focus` (with outline) when needed.
- Never disable the default browser focus outline without providing a more visible custom alternative.
- Use rem/em units for typography to respect user font size preferences.
- Use `prefers-contrast: more` media query for high contrast mode support.
- Use `prefers-color-scheme: dark` for dark mode support, ensuring contrast ratios are maintained.
- Ensure all images have meaningful `alt` text. Decorative images should have `alt=""`.
- Provide `aria-label` or `aria-labelledby` for all interactive elements that lack visible text labels.
- Use `role="presentation"` or `role="none"` on decorative SVG elements.
- Ensure that all event handlers have keyboard equivalents: `onClick` with `onKeyDown`/`onKeyUp` handling Enter and Space.
- Use `<label>` elements correctly associated with form controls via `htmlFor` (React) or `for` (HTML).
- Implement proper `aria-live` regions for dynamic content: `polite` for non-critical updates, `assertive` for urgent messages.
- Use `aria-describedby` to associate help text and error messages with inputs.
- Test every component with keyboard navigation before considering it complete.
- Run automated accessibility tests as part of the CI/CD pipeline with axe-core or Pa11y.
- Maintain an accessibility statement page that documents known issues and accommodations.
